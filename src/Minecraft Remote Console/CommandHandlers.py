#!/usr/bin/python
# vim: set shiftwidth=4 softtabstop=4 expandtab autoindent syntax=python:

import wx
import csv
import json
import os
import pickle

from MinecraftApi import MinecraftJsonApi
from SubscriptionManager import SubscriptionReader

class Command(object):
    def __init__(self, name, helpText=None, params=None, showHelp=None, 
        detailHelp=None, handler=None, usesEnv=None, alias = None):
        base = alias
        self.name = name
        self.aliases = alias
        self.helpText = (helpText if helpText 
            else base.helpText if base else '')
        self.detailHelp = (detailHelp if detailHelp 
            else base.detailHelp if base else '')
        self.params = params if params else base.params if base else []
        self.rparams = [p for p in self.params if p[0] != '_']
        self.showHelp = (bool(showHelp) if showHelp != None 
            else False if base else True)
        self.handler = (handler if handler 
            else base.handler if base else lambda x: None)
        self.usesEnv = usesEnv if usesEnv else base.usesEnv if base else {}

class _RemoteConsoleCommands (object):
    _defaultCommands = {}
    _commands = {}
    def __init__(self, prefix, doOutput, doClear, doClose, 
            environment, volitile):
        self._doOutput = doOutput
        self._doClear = doClear
        self._doClose = doClose
        self._env = environment
        self._volitile = volitile
        self._prefix = prefix
        
    def handleCommand(self, message):
        invalid = 'Invalid parameters. Run `%shelp %s` for more information' 
        unrecognized = 'Unrecognized command: %s%s'  
        if message[0] == self._prefix:
            cmd, sep, extra = message[1:].partition(' ')
            if cmd in self._commands.keys():
                args = self._parseArgs(extra)
                command = self._commands[cmd]
                largs = len(args)
                if largs > len(command.params) or largs < len(command.rparams):
                    self._doOutput(invalid % (self._prefix,cmd))
                    return True
                command.handler(self, args)
            else:
                self._doOutput(unrecognized % (self._prefix, cmd))
            return True

    def _parseArgs(self, args):
        params = list(csv.reader([args], delimiter=' '))
        return params[0] if len(params) else []

    def _help(self, args):
        euse = '\n\nCommand uses the following environmental variables\n'
        if len(args) == 0:
            self._doOutput('Available %s Commands:' % self._prefix)
            cmds = []
            for cmd, cfg in self._commands.items():
                if cfg.showHelp:
                    cmds.append('\t{0}\t-- {1}'.format(cmd, cfg.helpText))
            cmds.sort()
            self._doOutput('\n'.join(cmds))
        else:
            template='{usage}\n\n{helpText}{detailHelp}{euse}'
            cmd = self._commands.get(args[0], None)
            if cmd:		
                usage='Usage {prefix}{cmd} {params}'.format(
                    prefix=self._prefix,
                    cmd=cmd.name, 
                    params=' '.join(cmd.rparams)
                )
                euse = ''
                if len(cmd.params) != len(cmd.rparams):
                    fmt = lambda p: p if p[0] != '_' else '[%s]'%p[1:]
                    usage+='\n OR {prefix}{cmd} {params}'.format(
                        prefix=self._prefix,
                        cmd=cmd.name, 
                        params=' '.join([fmt(p) for p in cmd.params])
                    )
                if len(cmd.usesEnv.keys()):
                    vars_ = ['\t{0}: {1}'.format(env, usage_) for env, usage_ 
                        in cmd.usesEnv.items()]
                    vars_.sort()
                    euse += '\n'.join(vars_)
                self._doOutput(template.format(
                    usage=usage,
                    helpText=cmd.helpText,
                    detailHelp=cmd.detailHelp,
                    euse=euse,
                ))
            else:
                self._doOutput('Unrecognized command: %s' % args[0])

    def _envHelp (self, args):
        no_loaded = 'No loaded local commands use environmental variables'
        env_usage = 'The following environmental variables are being used\n'
        uses = {}
        for cmd in self._commands.values():
            for key in cmd.usesEnv.keys():
                if not cmd.aliases:
                    if key not in uses.keys():
                        uses[key] = []
                    uses[key].append(cmd.name)
        if uses.keys() == []:
            self._doOutput(no_loaded)
        else:
            lines = ['{0}: {1}'.format(
                    key, 
                    ', '.join(value)
                ) for key, value in uses.items()]
            self._doOutput(env_usage + '\n'.join(lines))

    _defaultCommands['help'] = Command('help', handler = _help,
            helpText = 'Show help for local commands', params=['_command'])
    _defaultCommands['h'] = Command('h', alias=_defaultCommands['help'])
    _defaultCommands['envusage'] = Command('envusage', handler = _envHelp,
            helpText = 'Show usage of environmental variables for commands')
    _defaultCommands['eusage'] = Command('eusage', 
            alias=_defaultCommands['envusage'])
    _defaultCommands['eus'] = Command('eusage', 
            alias=_defaultCommands['envusage'])
    
class RemoteConsoleLocalCommands (_RemoteConsoleCommands):
    def _showEnv(self, args):
        empty = 'Nobody here but us chickens!'
        items = ['{0}:\t{1}'.format(*i) for i in self._env.items()]
        items.sort()
        self._doOutput('\n'.join(items) if len(items) else empty)

    def _setEnv(self, args):
        self._env[args[0]] = args[1]

    def _unsetEnv(self, args):
        del self._env[args[0]]
    
    _commands = _RemoteConsoleCommands._defaultCommands.copy()
    _commands['unset'] = Command('unset', handler = _unsetEnv,
            helpText = 'Delete environmehtal variable',	params = ['key'])
    _commands['set'] = Command('set', handler = _setEnv,
            helpText = 'Set environmehtal variable', 
            params = ['key', 'value'])
    _commands['env'] = Command('env', handler= _showEnv,
            helpText= 'Show environmental variables')
    _commands['quit'] = Command('quit',
            handler= lambda self, x: self._doClose(),
            helpText='Quit the application')
    _commands['q'] = Command('q', alias=_commands['quit'])

class RemoteConsoleClientCommands (_RemoteConsoleCommands):
    def connect (self, args=[]):
        self.disconnect()
        parts = [None, None, None, None, None]
        for i in range(0, len(args)):
            parts[i] = args[i]

        options = {}
        validations =[
            {'name': 'remote_host', 'default': 'localhost',},
            {'name': 'remote_port',	'default': 20059,
                'converter': int, 'validator': lambda x: x >=0 and x <= 65535,
                'error': 'remote_port must be an integer between 0 and 65535',
            },
            {'name': 'remote_username',	'default': 'admin',},
            {'name': 'remote_password','default': 'demo',},
            {'name': 'remote_salt',	'default': '',},
        ]

        for part, cfg in zip(parts, validations):
            if part == None:
                part = self._env.get(cfg['name'], cfg['default'])
            converter = cfg.get('converter', lambda x:x)
            try:
                result = converter(part)
            except Exception as e:
                self._doOutput(cfg.get(
                    'error', 
                    'An error occurred processing %s: %s' (cfg['name'], e)))
                return
            validator = cfg.get('validator', lambda x: True)
            if not validator(result):
                self._doOutput(cfg.get(
                    'error', 
                    'Validation failed processing %s' (cfg['name'])))
                return
            options[cfg['name']] = result
        try:
            self._volitile['MinecraftJsonApi'] = MinecraftJsonApi(
                host=options['remote_host'],
                port=options['remote_port'],
                username=options['remote_username'],
                password=options['remote_password'],
                salt=options['remote_salt'],
            )
        except Exception as e:
            self._doOutput('Could not connect to remote server: %s' % e)
            return
        self.subscribe()

    def disconnect (self, args=[]):
        if 'MinecraftJsonApi' in self._volitile.keys():
            del self._volitile['MinecraftJsonApi']
        self.unsubscribe()
    
    def subscribe (self, args=[]):
        time_travel = 'Time ran backwards! Did the system time change?\n'
        server_overload = ('Can\'t keep up! Did the system time change, '
                         + 'or is the server overloaded?\n')

        def filter_ (message):
            accept = True
            for msg in [time_travel, server_overload]:
                if message.endswith(msg.format(**self._env)):
                    accept = False
            return accept
        def writer (message):
            self._doOutput(message)

        if 'MinecraftJsonApi' not in self._volitile.keys():
            self._doOutput('Not connected: connect to remote server first.')
            return

        source = (args[0] if len(args) > 0 
                else self._env.get('remote_source', 'console'))

        if source == 'console':
            formatter = lambda x: x['line'] 
        else:
            formatter = lambda x: '%s: %s' %(x['player'], x['message'])

        try:
            stream = self._volitile['MinecraftJsonApi'].subscribe(source)
        except Exception as e:
            self._doOutput('Subscription failed: %s' %e)
            return
        
        reader = SubscriptionReader(stream, writer, filter_, formatter)
        self._volitile['MinecraftJsonReader'] = reader
        reader.start()

    def unsubscribe (self, args=[]):
        if 'MinecraftJsonReader' in self._volitile.keys():
            self._volitile['MinecraftJsonReader'].active = False
            del self._volitile['MinecraftJsonReader']
        
    _commands = _RemoteConsoleCommands._defaultCommands.copy()

    _commands['connect'] = Command('connect', handler = connect,
            helpText = 'Connect to remote server',
            params = ['_host', '_port', '_username', '_password', '_salt'],
            usesEnv = {
                'remote_host': 'Overrides default server (localhost)',
                'remote_port': 'Overrides default port (20059)',
                'remote_username': 'Overrides default username (admin)',
                'remote_password': 'Overrides default password (demo)', 
                'remote_salt': 'Overrides default salt ()',
                'remote_source': 'Overrides default console source (console)',
            })
    _commands['con'] = Command('con', alias=_commands['connect'])
    _commands['c'] = Command('c', alias=_commands['connect'])
    _commands['disconnect'] = Command('disconnect',	handler = disconnect,
        helpText = 'Disconnect from remote server')
    _commands['dis'] = Command('dis', alias=_commands['disconnect'])
    _commands['d'] = Command('d', alias=_commands['disconnect'])
    _commands['subscribe'] = Command('subscribe', handler = subscribe,
        helpText = 'Subscribe to remote output stream (console or chat)',
        params = ['_streamName'],
        usesEnv = {
            'remote_source': 'Overrides default stream (console)'
        })
    _commands['sub'] = Command('sub', alias=_commands['subscribe'])
    _commands['s'] = Command('s', alias=_commands['subscribe'])
    _commands['unsubscribe'] = Command('unsubscribe', handler = unsubscribe,
        helpText = 'Unsubscribe to remote output stream')
    _commands['unsub'] = Command('unsub', alias=_commands['unsubscribe'])
    _commands['u'] = Command('u', alias=_commands['unsubscribe'])
    _commands['clear'] = Command('clear',
        handler = lambda self, args: self._doClear(),
        helpText = 'Clear the screen of output')
    _commands['clr'] = Command('clr', alias=_commands['clear'])

class RemoteConsoleRemoteCommands (_RemoteConsoleCommands):
    def __getCommands(self):
        def creatHandler(name):
            def handler (self, args):
                result = self._volitile['MinecraftJsonApi'].call(name, *args)
                self._doOutput(json.dumps(result, indent=2))
            return handler
        if 'MinecraftJsonApi' not in self._volitile.keys():
            self._doOutput('Not connected: connect to remote server first.')
            return
        self._commands = _RemoteConsoleCommands._defaultCommands.copy()
        
        letters = list('abcdefghijklmnopqrstuvwxyz')
        for method in self._volitile['MinecraftJsonApi'].getLoadedMethods():
            args = ['%s -- %s' %(a,b) for a,b 
                    in zip(letters, method['params']) if b != None]
            detail = '\n\nreturns: {returns}\n\nparameters:\n\t{args}'.format(
                desc = method['description'],
                returns = method['returns'],
                args = '\n\t'.join(args),
            )
            cmd = Command( method['method_name'],
                params = letters[:len(method['params'])],
                handler = creatHandler(method['method_name']),
                helpText = method['description'],
                detailHelp = detail,
            )
            self._commands[cmd.name] = cmd

    def handleCommand(self, message):
        if message[0] == self._prefix:
            self.__getCommands()
            return super(RemoteConsoleRemoteCommands, self).handleCommand(message)
    def _help(self, args):
        self.__getCommands()
        return super(RemoteConsoleRemoteCommands, self)._help(message)

class RemoteConsoleChatCommands (_RemoteConsoleCommands):
    def handleCommand(self, message):
        if 'MinecraftJsonApi' not in self._volitile.keys():
            return
        client = self._volitile['MinecraftJsonApi']
        if message[0] == self._prefix:
            client.call('runConsoleCommand', message[1:])
        else:
            name = self._env.get('name', 'Metatron')
            client.call('broadcastWithName', message, name)
        return True

class Controller (object):
    def __init__ (self, ui):
        def closer ():
            try:
                with open(self.__persistpath, 'wb') as persist:
                    pickle.dump(self.__env, persist)
                    pickle.dump(self.__ui.GetHistory(), persist)
            except Exception as e:
                print(repr(e))
                pass
        def doAction(action):
            method = getattr(self.__ui, action)
            def doIt(*args):
                wx.CallAfter(method, *args)
            return doIt
        self.__ui = ui
        self.__env = {}
        history = []
        self.__persistpath = os.path.expanduser('~/.minecraftRemoteConsole.pkl')
        try:
            with open(self.__persistpath, 'rb') as persisted:
                self.__env = pickle.load(persisted)
                history = pickle.load(persisted)
        except Exception as e:
            print(repr(e))
        self.__ui.SetHistory(history)
        self.__ui.AddCloser(closer)
        self.__volitile = {}
        self.__params = {
            'doOutput': doAction('AddOutput'), 
            'doClear':  doAction('ClearOutput'), 
            'doClose':  doAction('Close'),
            'environment': self.__env, 
            'volitile': self.__volitile,
        }

    def loadCommands(self):
        localCommands = RemoteConsoleLocalCommands(prefix='#', **self.__params)
        self.__ui.AddHandler(lambda x: localCommands.handleCommand(x))
        clientCommands = RemoteConsoleClientCommands(prefix='%',**self.__params)
        self.__ui.AddHandler(lambda x: clientCommands.handleCommand(x))
        remoteCommands = RemoteConsoleRemoteCommands(prefix=':', **self.__params)
        self.__ui.AddHandler(lambda x: remoteCommands.handleCommand(x))
        chatCommands = RemoteConsoleChatCommands(prefix='/', **self.__params)
        self.__ui.AddHandler(lambda x: chatCommands.handleCommand(x))


