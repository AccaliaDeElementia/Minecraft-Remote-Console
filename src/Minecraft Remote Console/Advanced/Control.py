#!/usr/bin/python
from os import path
import pickle

import wx

from Window import AdvancedWindow
from Common.Commands import CommandCategory
from Common import Events

def noop(*args, **kwargs):
    pass

class Control (object):
    ENVIRON_STORE = '__environ_store'
    STORES_PATH = path.expanduser('~/.MinecraftRemoteConsole.store')
    def __init__(self, window):
        self.__window = window
        window.Bind(wx.EVT_CLOSE, self.__evt_close_window)
        window._entry.Bind(wx.EVT_CHAR, self.__evt_entry_char)
        window._action.Bind(wx.EVT_BUTTON, self.__evt_action_click)
        self.__command_categories = {}
        self.__default_handler = noop
        self.__stores = {}
        self.__quitting = False
        try:
            self.load()
        except Exception as e:
            print(str(e))

    def __evt_entry_char(self, event):
        '''Handles special case character entry.
        '''
        evt = Events.KeyPressEvent(self.__window._entry.Value, 
                                   event.GetKeyCode())
        self.trigger_event(evt)
        event.Skip()
    def __evt_action_click(self, event):
        '''Handles onSend events.
        '''
        evt = Events.PreInputEvent(self.__window._entry.Value)
        self.trigger_event(evt)
        if not evt.is_canceled:
            self.__window._entry.SetFocus()
        event.Skip()

    def __evt_close_window(self, event):
        '''Handles preclose cleanup.
        '''
        if self.__quitting:
            event.Skip()
        else:
            self.quit_app()
    
    def __update_after_event(self, event):
        self.__window.Freeze()
        try:
            for line in event.get_output():
                uline = unicode(line)
                if uline[-1] != u'\n':
                    uline += u'\n'
                self.__window._output.AppendText(uline)
        finally:
            if event.scroll_output:
                self.__window._output.ShowPosition(
                    self.__window._output.GetLastPosition)
            self.__window.Thaw()
        if event.set_input:
            self.__window._entry.Value = event.input
            self.__window._entry.SetInsertionPointEnd()
  
    def trigger_event(self, event):
        '''Trigger an event and handle the results.
        '''
        event.env = self.get_datastore(Control.ENVIRON_STORE)
        if not isinstance(event, Events.Event):
            raise TypeError('event must be a subclass of Event')
        for category in self.__command_categories.values():
            if not event.stop_execution:
                category.invoke(event)
        if not event.is_handled and not event.is_canceled:
            self.__default_handler(event)
        if not event.is_canceled:
            wx.CallAfter(self.__update_after_event, event)
            if callable(event.on_success):
                wx.CallAfter(event.on_success)
            for evt in event.get_triggered_events():
                self.trigger_event(evt)
        if callable(event.after):
            wx.CallAfter(event.after)
 
    def quit_app(self):
        def __quit():
            self.__window.Close()
        evt = Events.QuitEvent('Quit App')
        self.trigger_event(evt)
        self.__quitting = not evt.is_canceled
        if not evt.is_canceled:
            wx.CallAfter(__quit)


    def clear(self):
        '''Clear the output
        '''
        def __clear():
            self.__window.Freeze()
            try:
                self.__window._output.Value = ''
            finally:
                self.__window.Thaw()
        wx.CallAfter(__clear)

    def scroll_down(self):
        '''Scroll the output window down
        '''
        wx.CallAfter(self.__window._output.PageDown)

    def scroll_up(self):
        '''Scroll the output window up
        '''
        wx.CallAfter(self.__window._output.PageUp)

    def save(self):
        '''Save persistant data to disk'''
        with open(self.STORES_PATH, 'wb') as stores:
            pickle.dump(self.__stores, stores, -1)

    def load(self):
        '''Load persistant data from disk'''
        with open(self.STORES_PATH, 'rb') as stores:
            self.__stores = pickle.load(stores)

    def register_commands(self, category):
        if not isinstance(category, CommandCategory):
            raise TypeError('category must be a CommandCategory object')
        self.__command_categories[category.prefix] = category
        self.get_datastore(category.prefix)
        return True
        
    def unregister_commands(self, category):
        keyerror = 'Command category prefix "%s" not found'
        if not (isinstance(category, CommandCategory) or
                isinstance(category, basestring)):
            raise TypeError('category must be CategoryCommand or prefix')
        if isinstance(category, CommandCategory):
            prefix = category.prefix
        else:
            prefix = category
        match = self.__command_categories.has_key(prefix)
        if not match:
            raise KeyError(keyerror % prefix)
        cat = self.__command_categories[prefix]
        del self.__command_categories[prefix]
        return cat

    def get_datastore(self, category):
        if not (isinstance(category, CommandCategory) or
                isinstance(category, basestring)):
            raise TypeError('category must be CategoryCommand or prefix')
        if isinstance(category, CommandCategory):
            prefix = category.prefix
        else:
            prefix = category
        match = self.__stores.has_key(prefix)
        if not match:
            self.__stores[prefix] = {}
        return self.__stores[prefix]

    def set_default_handler(self, handler):
        self.__default_handler = handler
# vim: shiftwidth=4:softtabstop=4:expandtab:autoindent:syntax=python
