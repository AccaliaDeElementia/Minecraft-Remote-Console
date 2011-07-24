#!/usr/bin/python
import wx

from Window import AdvancedWindow

def noop(*args, **kwargs):
    pass

class Control (object):
    def __init__(self, window):
        self.__window = window
        window.Bind(wx.EVT_CLOSE, self.__evt_close_window)
        window._entry.Bind(wx.EVT_CHAR, self.__evt_entry_char)
        window._action.Bind(wx.EVT_BUTTON, self.__evt_action_click)
        self.__command_categories = []
        self.__default_handler = noop

    def __evt_entry_char(self, event):
        '''Handles special case character entry.
        '''
        actions = {
            wx.WXK_RETURN: 'ENTER',
            wx.WXK_NUMPAD_ENTER: 'ENTER',
            wx.WXK_PAGEUP: 'PAGE UP',
            wx.WXK_NUMPAD_PAGEUP: 'PAGE UP',
            wx.WXK_PAGEDOWN: 'PAGE DOWN',
            wx.WXK_NUMPAD_PAGEDOWN: 'PAGE DOWN',
            wx.WXK_UP: 'UP',
            wx.WXK_NUMPAD_UP: 'UP',
            wx.WXK_DOWN: 'DOWN',
            wx.WXK_NUMPAD_DOWN: 'DOWN',
        }
        action = actions.get(event.GetKeyCode(), event.Skip)
        action()
        pass

    def __evt_action_click(self, event):
        '''Handles onSend events.
        '''
        event.Skip()
        pass

    def __evt_close_window(self, event):
        '''Handles preclose cleanup.
        '''
        event.Skip()

    def send_message(self, data):
        '''Send a message.
        '''
        prefix = data[0] if len(data) else ''
        for category in self.__command_categories:
            if prefix == category.prefix:
                return category.invoke(data)

        #Matches no loaded command prefix. Default it
        return self.__default_handler(data)

    def recv_message(self, data, scroll_output=False):
        '''Display a message to the interface
        '''
        self.__window.Freeze()
        try:
            self.__window._output.AppendText(data)
            if scroll_output:
                self.__window._output.ShowPosition(
                    self.__window._output.GetLastPosition)
        finally:
            self.__window.Thaw()


    def clear(self):
        '''Clear the screen
        '''
        self.__window.Freeze()
        try:
            self.__window._output.value = ''
        finally:
            self.__window.Thaw()
        
if __name__ == '__main__':
    app =AdvancedWindow.start_app()
    window = AdvancedWindow()
    controler = Control(window)
    window.Show()    
    app.MainLoop()

# vim: shiftwidth=4:softtabstop=4:expandtab:autoindent:syntax=python
