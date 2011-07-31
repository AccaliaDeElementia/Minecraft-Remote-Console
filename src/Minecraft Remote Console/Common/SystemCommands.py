#!/usr/bin/python
import wx

from Common.Commands import CommandCategory, Command
from Common import Events

class SystemCommands(object):
    def __init__(self, controler):
        self.__controler = controler
        self.__datastore = controler.get_datastore('System Commands')
        if 'history' not in self.__datastore.keys():
            self.__datastore['history'] = ['']
        self.__datastore['historypos'] = len(self.__datastore['history']) - 1
   
    #region: KeyPress Events   
    def __quitter(self):
        def quit(event):
            '''Exit the application
            '''
            self.__controler.quit_app()
        return Command(quit, events = [Events.Event.TYPE_INPUT])

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
        return Command(env, events=[Events.Event.TYPE_INPUT])

    def __set_env(self):
        def set(event):
            '''Set a stored environment vatiable'''
            event.env[event.args[1]] = event.args[2]
        return Command(set, 
                parameters=['key', 'value'],
                events=[Events.Event.TYPE_INPUT])

    def __unset_env(self):
        def unset(event):
            '''Set a stored environment vatiable'''
            if event.args[1] in event.env.keys():
                del event.env[event.args[1]]
        return Command(unset, 
                parameters=['key'],
                events=[Events.Event.TYPE_INPUT])

    def __clear(self):
        def clear(event):
            '''Clear the screen of output'''
            self.__controler.clear()
        return Command(clear, events=[Events.Event.TYPE_INPUT])

    def __forget(self):
        def forget(event):
            '''Forget all history'''
            self.__datastore['history'] = ['']
            self.__datastore['historypos'] = 0
        return Command(forget, events=[Events.Event.TYPE_INPUT])
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
        
        # KeyPress Events
        category.add_command(self.__submitter())
        category.add_command(self.__scroll_up())
        category.add_command(self.__scroll_down())
        category.add_command(self.__histforward())
        category.add_command(self.__histback())

        return category
# vim: shiftwidth=4:softtabstop=4:expandtab:autoindent:syntax=python
