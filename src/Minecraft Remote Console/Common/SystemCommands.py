#!/usr/bin/python
import wx

from Common.Commands import CommandCategory, Command
from Common import Events
from Common.MinecraftApi import MinecraftJsonApi

class SystemCommands(object):
    def __init__(self, controler):
        self.__controler = controler
        self.__datastore = controler.get_datastore('System Commands')
        if 'history' not in self.__datastore.keys():
            self.__datastore['history'] = ['']
        self.__datastore['historypos'] = len(self.__datastore['history']) - 1
        self.__server = None
   
    #region: KeyPress Events
    def __onquit(self):
        def onquit(event):
            self.__controler.save()
        return Command(onquit, events=[Events.Event.TYPE_QUIT])

    def __submitter(self):
        def submit(event):
            '''Trigger a submit when the enter key is pressed.

            Accepts either keyboard enter or numpad enter.
            '''
            if (isinstance (event, Events.KeyPressEvent) and event.key 
                    in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]):
                # trigger an InputEvent when the user presses the enter key
                evt = Events.InputEvent(event.data)

                # do some history housekeeping
                history = self.__datastore['history']
                history[-1] = event.data
                history.append('')
                self.__datastore['historypos'] = len(history) - 1

                # trigger the new event
                event.add_triggered_event(evt)
        return Command(submit, events=[Events.Event.TYPE_KEYPRESS])

    def __scroll_up(self):
        def scrollup(event):
            '''Scroll the output window one page up'''
            if (isinstance (event, Events.KeyPressEvent) and event.key 
                    in [wx.WXK_PAGEUP, wx.WXK_NUMPAD_PAGEUP]):
                self.__controler.scroll_up()
        return Command(scrollup, events=[Events.Event.TYPE_KEYPRESS])

    def __scroll_down(self):
        def scrolldown(event):
            '''Scroll the output window one page down'''
            if (isinstance (event, Events.KeyPressEvent) and event.key 
                    in [wx.WXK_PAGEDOWN, wx.WXK_NUMPAD_PAGEDOWN]):
                self.__controler.scroll_down()
        return Command(scrolldown, events=[Events.Event.TYPE_KEYPRESS])

    def __histforward(self):
        def histforward(event):
            '''Move forward in time'''
            if (isinstance (event, Events.KeyPressEvent) and event.key 
                    in [wx.WXK_DOWN, wx.WXK_NUMPAD_DOWN]):
                history = self.__datastore['history']
                pos = self.__datastore['historypos']
                if pos < len(history) - 1:
                    history[pos] = event.data
                    pos += 1
                    event.set_input = True
                    event.input = history[pos]
                    self.__datastore['historypos'] = pos
        return Command(histforward, events=[Events.Event.TYPE_KEYPRESS])

    def __histback(self):
        def histback(event):
            '''Move backward in time'''
            if (isinstance (event, Events.KeyPressEvent) and event.key 
                    in [wx.WXK_UP, wx.WXK_NUMPAD_UP]):
                history = self.__datastore['history']
                pos = self.__datastore['historypos']
                if pos > 0:
                    history[pos] = event.data
                    pos -= 1
                    event.set_input = True
                    event.input = history[pos]
                    self.__datastore['historypos'] = pos
        return Command(histback, events=[Events.Event.TYPE_KEYPRESS])

    #endregion: KeyPress Events

    #region: Input Events
    def __quitter(self):
        def quit(event):
            '''Exit the application
            '''
            self.__controler.quit_app()
        return Command(quit, events = [Events.Event.TYPE_INPUT])

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
        return Command(env, events=[Events.Event.TYPE_INPUT])

    def __set_env(self):
        def set(event):
            '''Set a stored environment vatiable'''
            event.env[event.args[1]] = event.args[2]
            event.is_handled = True
        return Command(set, 
                parameters=['key', 'value'],
                events=[Events.Event.TYPE_INPUT])

    def __unset_env(self):
        def unset(event):
            '''Set a stored environment vatiable'''
            if event.args[1] in event.env.keys():
                del event.env[event.args[1]]
            event.is_handled = True
        return Command(unset, 
                parameters=['key'],
                events=[Events.Event.TYPE_INPUT])

    def __clear(self):
        def clear(event):
            '''Clear the screen of output'''
            self.__controler.clear()
            event.is_handled = True
        return Command(clear, events=[Events.Event.TYPE_INPUT])

    def __forget(self):
        def forget(event):
            '''Forget all history'''
            self.__datastore['history'] = ['']
            self.__datastore['historypos'] = 0
            event.is_handled = True
        return Command(forget, events=[Events.Event.TYPE_INPUT])

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
            evt = Events.ConnectEvent(data=server)
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
                    events=[Events.Event.TYPE_INPUT])

    def __disconnect(self):
        def disconnect(event):
            '''Disconnect from remote Ninecraft server
            '''
            if self.__server:
                evt = Events.DisconnectEvent(data=self.__server)
                event.add_triggered_event(evt)
            event.is_handled = True
        return Command(disconnect, events=[Events.Event.TYPE_INPUT])

    def __save(self):
        def save(event):
            '''Save all data stores to disk'''
            try:
                self.__controler.save()
                event.add_output('Data stores saved')
            except Exception as e:
                event.add_output('Error: $s' %e)
            event.is_handled = True
        return Command(save, events=[Events.Event.TYPE_INPUT])

    def __load(self):
        def load(event):
            '''Loadall data stores from disk'''
            try:
                self.__controler.save()
                event.add_output('Data stores restored')
            except Exception as e:
                event.add_output('Error: $s' %e)
            event.is_handled = True
        return Command(load, events=[Events.Event.TYPE_INPUT])

    #endregion: Input Events
    
    def create_commands(self):
        category = CommandCategory('#', 'System Commands', 
            'Commands affecting local status')
        
        # Testing. Remove after
        category.add_command(Command(self.__quitter(), name = 'q'))

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

        return category
# vim: shiftwidth=4:softtabstop=4:expandtab:autoindent:syntax=python
