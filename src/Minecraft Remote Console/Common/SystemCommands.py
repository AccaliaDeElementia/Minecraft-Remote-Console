#!/usr/bin/python
import csv
from StringIO import StringIO

import wx

from Common.Commands import CommandCategory, Command
from Common.Events import *
from Common.MinecraftApi import MinecraftJsonApi

ALIAS_STORE = 'aliases'
HISTORY_STORE = 'history'
HISTORY_POS = 'historypos'

class SystemCommands(object):
    def __init__(self, controler):
        self.__controler = controler
        self.__datastore = controler.get_datastore('System Commands')
        datastore = self.__datastore
        if HISTORY_STORE not in datastore.keys():
            datastore[HISTORY_STORE] = ['']
        datastore[HISTORY_POS] = len(datastore[HISTORY_STORE]) - 1
        if ALIAS_STORE not in self.__datastore.keys():
            self.__datastore[ALIAS_STORE] = {}
        self.__server = None
        self.__alias_recording = None

    #region: Aliases
    def __alias_cmd(self):
        recording = 'Recording alias \'%s\'. Enter command to alias now.'
        def alias(event):
            '''Add an alias command
            '''
            name = event.args[1]
            if len(name.split()) > 1:
                event.add_output('Alias name cannot contain whitespace')
                event.is_handled = True
                return
            if name in ['#alias', '#unalias', '#quit']:
                event.add_output('Cannot alias protected command: '+name)
                event.is_handled = True
                return
            self.__alias_recording = name
            event.add_output(recording % name)
            event.is_handled = True
            pass
        return Command(alias, 
            parameters=['name'],
            events=[Event.TYPE_INPUT])
    def __alias_recorder(self):
        saved = 'Saved alias: \'%s\' => \'%s\''
        def record(event):
            if self.__alias_recording != None:
                aliases = self.__datastore[ALIAS_STORE]
                aliases[self.__alias_recording] = event.data
                evt = OutputEvent(saved % (self.__alias_recording,event.data))
                evt.set_input = True
                self.__controler.trigger_event(evt)
                self.__alias_recording = None
                event.is_canceled = True
                event.is_handled = True
        return Command(record, events=[Event.TYPE_PREINPUT])
    def __alias_listener(self):
        def deserialize(data):
           return list(csv.reader([data], delimiter=' '))[0] 
        def serialize(data):
            s = StringIO()
            writer = csv.writer(s, delimiter=' ')
            writer.writerow(data)
            s.seek(0)
            return s.read()
        def listener(event):
            aliases = self.__datastore[ALIAS_STORE]
            if len(event.args) and event.args[0] in aliases.keys():
                event.is_canceled = True
                event.is_handled = True
                args = deserialize(aliases[event.args[0]]) + event.args[1:]
                evt = PreInputEvent(serialize(args))
                self.__controler.trigger_event(evt)
        return Command(listener, events=[Event.TYPE_PREINPUT])

    #endregion: Aliases

    #region: KeyPress Events
    def __onquit(self):
        def onquit(event):
            self.__controler.save()
        return Command(onquit, events=[Event.TYPE_QUIT])

    def __submitter(self):
        def submit(event):
            '''Trigger a submit when the enter key is pressed.

            Accepts either keyboard enter or numpad enter.
            '''
            if (isinstance (event, KeyPressEvent) and event.key 
                    in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]):
                # trigger an InputEvent when the user presses the enter key
                evt = PreInputEvent(event.data)

                # do some history housekeeping
                history = self.__datastore['history']
                history[-1] = event.data
                history.append('')
                self.__datastore['historypos'] = len(history) - 1

                # trigger the new event
                event.add_triggered_event(evt)
        return Command(submit, events=[Event.TYPE_KEYPRESS])

    def __scroll_up(self):
        def scrollup(event):
            '''Scroll the output window one page up'''
            if (isinstance (event, KeyPressEvent) and event.key 
                    in [wx.WXK_PAGEUP, wx.WXK_NUMPAD_PAGEUP]):
                self.__controler.scroll_up()
        return Command(scrollup, events=[Event.TYPE_KEYPRESS])

    def __scroll_down(self):
        def scrolldown(event):
            '''Scroll the output window one page down'''
            if (isinstance (event, KeyPressEvent) and event.key 
                    in [wx.WXK_PAGEDOWN, wx.WXK_NUMPAD_PAGEDOWN]):
                self.__controler.scroll_down()
        return Command(scrolldown, events=[Event.TYPE_KEYPRESS])

    def __histforward(self):
        def histforward(event):
            '''Move forward in time'''
            if (isinstance (event, KeyPressEvent) and event.key 
                    in [wx.WXK_DOWN, wx.WXK_NUMPAD_DOWN]):
                history = self.__datastore['history']
                pos = self.__datastore['historypos']
                if pos < len(history) - 1:
                    history[pos] = event.data
                    pos += 1
                    event.set_input = True
                    event.input = history[pos]
                    self.__datastore['historypos'] = pos
        return Command(histforward, events=[Event.TYPE_KEYPRESS])

    def __histback(self):
        def histback(event):
            '''Move backward in time'''
            if (isinstance (event, KeyPressEvent) and event.key 
                    in [wx.WXK_UP, wx.WXK_NUMPAD_UP]):
                history = self.__datastore['history']
                pos = self.__datastore['historypos']
                if pos > 0:
                    history[pos] = event.data
                    pos -= 1
                    event.set_input = True
                    event.input = history[pos]
                    self.__datastore['historypos'] = pos
        return Command(histback, events=[Event.TYPE_KEYPRESS])

    #endregion: KeyPress Events

    #region: Input Events
    def __quitter(self):
        def quit(event):
            '''Exit the application
            '''
            self.__controler.quit_app()
            event.is_handled = True
        return Command(quit, events=[Event.TYPE_INPUT])

    def __list_env(self):
        empty = 'Nobody here but us chickens!'
        template = '\t%s =>\t%s'
        def env(event):
            '''List stored environment variables'''
            keys = event.env.keys()
            keys.sort()
            if keys:
                for key in keys:
                    event.add_output(template % (key, event.env[key]))
            else:
                event.add_output(empty)
            event.is_handled = True
        return Command(env, events=[Event.TYPE_INPUT])

    def __set_env(self):
        def set(event):
            '''Set a stored environment vatiable'''
            event.env[event.args[1]] = event.args[2]
            event.is_handled = True
        return Command(set, 
                parameters=['key', 'value'],
                events=[Event.TYPE_INPUT])

    def __unset_env(self):
        def unset(event):
            '''Set a stored environment vatiable'''
            if event.args[1] in event.env.keys():
                del event.env[event.args[1]]
            event.is_handled = True
        return Command(unset, 
                parameters=['key'],
                events=[Event.TYPE_INPUT])

    def __clear(self):
        def clear(event):
            '''Clear the screen of output'''
            self.__controler.clear()
            event.is_handled = True
        return Command(clear, events=[Event.TYPE_INPUT])

    def __forget(self):
        def forget(event):
            '''Forget all history'''
            self.__datastore['history'] = ['']
            self.__datastore['historypos'] = 0
            event.is_handled = True
        return Command(forget, events=[Event.TYPE_INPUT])

    def __connect(self):
        opts = [
            ('host', str, None, None, 'localhost'),
            ('port', int, lambda x: x >= 0 and x <= 65535,
                'port must be between 0 and 65535', 20059),
            ('username', str, None, None, 'admin'),
            ('password', str, None, None, 'demo'),
            ('salt', str, None, None, ''),
        ]
        def connect(event):
            '''Connect to remote Minecraft server
            '''
            eargs = event.args[1:] + [None for x in opts]
            args = {}
            for arg, validator in zip(eargs, [x for x in opts]):
                if arg == None:
                    if 'remote_'+validator[0] in event.env.keys():
                        arg = event.env['remote_'+validator[0]]
                    else:
                        arg = validator[4]
                temp = None
                try:
                    temp = validator[1](arg)
                except Exception as e:
                    event.add_output('Error: %s - %s' % (validator[0], e))
                    event.is_handled = True
                    return
                if validator[2] and not validator[2](temp):
                    event.add_output('Error: %s' % validator[3])
                    event.is_handled = True
                    return
                args[validator[0]] = temp
            try:
                server = MinecraftJsonApi(**args)
            except Exception as e:
                    event.add_output('Error: Connect failed')
                    event.add_output(str(e))
                    event.is_handled = True
                    return
            self.__server = server
            evt = ConnectEvent(data=server)
            event.add_triggered_event(evt)
            event.is_handled = True
        return Command(connect,
                    parameters=['_' + x[0] for x in opts],
                    environment=[
                        ('remote_host', 'Override default host (localhost)'),
                        ('remote_port', 'Override default port (20079)'),
                        ('remote_username', 'Override default user (admin)'),
                        ('remote_password', 'Override default password (demo)'),
                        ('remote_salt', 'Override default salt ()')
                    ],
                    events=[Event.TYPE_INPUT])

    def __disconnect(self):
        def disconnect(event):
            '''Disconnect from remote Ninecraft server
            '''
            if self.__server:
                evt = Events.DisconnectEvent(data=self.__server)
                event.add_triggered_event(evt)
            event.is_handled = True
        return Command(disconnect, events=[Event.TYPE_INPUT])

    def __save(self):
        def save(event):
            '''Save all data stores to disk'''
            try:
                self.__controler.save()
                event.add_output('Data stores saved')
            except Exception as e:
                event.add_output('Error: $s' %e)
            event.is_handled = True
        return Command(save, events=[Event.TYPE_INPUT])

    def __load(self):
        def load(event):
            '''Loadall data stores from disk'''
            try:
                self.__controler.save()
                event.add_output('Data stores restored')
            except Exception as e:
                event.add_output('Error: $s' %e)
            event.is_handled = True
        return Command(load, events=[Event.TYPE_INPUT])

    #endregion: Input Events
    
    def create_commands(self):
        category = CommandCategory('#', 'System Commands', 
            'Commands affecting local status')
        
        # Input Events
        category.add_command(self.__quitter())
        category.add_command(self.__list_env())
        category.add_command(self.__set_env())
        category.add_command(self.__unset_env())
        category.add_command(self.__clear())
        category.add_command(self.__forget())
        category.add_command(self.__connect())
        category.add_command(self.__disconnect())
        category.add_command(self.__save())
        category.add_command(self.__load())
        
        # KeyPress Events
        category.add_command(self.__onquit())
        category.add_command(self.__submitter())
        category.add_command(self.__scroll_up())
        category.add_command(self.__scroll_down())
        category.add_command(self.__histforward())
        category.add_command(self.__histback())

        category.add_command(self.__alias_cmd())
        category.add_command(self.__alias_recorder())
        category.add_command(self.__alias_listener())

        return category
# vim: shiftwidth=4:softtabstop=4:expandtab:autoindent:syntax=python
