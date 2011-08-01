#!/usr/bin/python
import json
from threading import Thread

import wx

from Common.Commands import CommandCategory, Command
from Common import Events
from Common.MinecraftApi import MinecraftJsonApi

class ConsoleListener(Thread):
    def __init__(self, input_, controler_, filter_=None):
        Thread.__init__(self)
        self.__input = input_
        self.__controler = controler_
        self.__filter = filter_ if filter_ else lambda x: True
        self.active = True
        self.daemon = True

    def run(self):
        ctrl = self.__controler
        try:
            while self.active:
                raw = self.__input.readline()
                res = json.loads(raw.decode())
                line = res[res['result']]['line']
                if self.__filter(line) and self.active:
                    evt = Events.OutputEvent(data=line)
                    evt.add_output(line)
                    ctrl.trigger_event(evt)
        except Exception as e:
            evt = Events.OutputEvent(data='ERROR')
            event.add_output('Error: %s' % e)
            ctrl.trigger_event(evt)
            raise
        finally:
            self.__input.close()

class RemoteCommands(object):
    def __init__(self, controler):
        self.__controler = controler
        self.__datastore = controler.get_datastore('Remote Commands')
        self.__server = None
        self.__subscription = None
   
    #region: Connection Events
    def __on_connect(self):
        def handler(event):
            args = list(event.args)
            args[0] = args[0][1:] # trim prefix character
            try:
                rval = self.__server.call(*args)
                if rval:
                    event.add_output(json.dumps(rval, indent=2))
            except Exception as e:
                event.add_output('Error: %s' % e)
            event.is_handled = True

        def on_connect(event):
            '''Perform setup when connecting to a server'''
            self.__server = event.data

            cmds = []
            letters = list('abcdefghijklmnopqrstuvwxyz')
            # Create Commands.
            for cmd in self.__server.getLoadedMethods():
                parms = ['%s - %s' % (x,y) for x,y 
                            in zip(letters, cmd['params'])]
                template = '\n\nreturns: {returns}\n\nparameters:\n\t{parms}'
                details = template.format(
                    returns=cmd['returns'],
                    parms='\n\t'.join(parms)
                )
                cmds.append(Command(handler,
                    name=cmd['method_name'],
                    description=cmd['description'],
                    detail_help=details,
                    parameters=letters[:len(parms)],
                    events=[Events.Event.TYPE_INPUT]
                ))
            self.__category.clear_commands()
            for cmd in cmds:
                self.__category.add_command(cmd)
            self.__category.add_builtins()
        return Command(on_connect, events=[Events.Event.TYPE_CONNECT])
   
    def __on_disconnect(self):
        def on_disconnect(event):
            self.__server = None
            self.__category.clear_commands()
            self.__category.add_builtins()
            event.is_handled = True
        return Command(on_disconnect, events=[Events.Event.TYPE_DISCONNECT])
    
    def __subscribe(self):
        def subscribe(event):
            if self.__subscription != None:
                self.__subscription.active = False
            feed = event.data.subscribe('console')
            sub = ConsoleListener(feed, self.__controler)
            self.__subscription = sub
            sub.start()
        return Command(subscribe, events=[Events.Event.TYPE_CONNECT])


    #endregion: Connection Events

    #region: Input Events
    #endregion: Input Events
    
    def create_commands(self):
        category = CommandCategory(':', 'Remote JSONAPI Commands', 
            'Commands using JSONAPI')
        self.__category = category

        category.add_command(self.__on_connect())
        category.add_command(self.__on_disconnect())
        category.add_command(self.__subscribe())
        return category
# vim: shiftwidth=4:softtabstop=4:expandtab:autoindent:syntax=python
