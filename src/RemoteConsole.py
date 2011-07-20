#!/usr/bin/python
# vim: set shiftwidth=4 softtabstop=4 expandtab autoindent syntax=python:
import wx
import csv
import json
import os
import pickle

from MinecraftApi import MinecraftJsonApi
from SubscriptionManager import SubscriptionReader
from CommandHandlers import Controller

EVENTS = set(['send','recv','presend', 'postsend', 'prerecv', 'postrecv', 'exit'])

class RemoteConsoleUI(wx.Frame):
    class _controls (object):
        def __init__(self, parent):
            self.contentArea = wx.Panel(parent)
            self.contentSizer = wx.BoxSizer(wx.VERTICAL)
            self.contentArea.SetSizer(self.contentSizer)

            self.outputArea = wx.Panel(self.contentArea)
            self.outputSizer = wx.BoxSizer(wx.VERTICAL)
            self.outputArea.SetSizer(self.outputSizer)

            self.output = wx.TextCtrl(self.outputArea, style=wx.TE_MULTILINE)
            self.output.SetEditable(False)

            self.outputSizer.Add(self.output, proportion=1, 
                    flag=wx.EXPAND|wx.ALL)

            self.inputArea = wx.Panel(self.contentArea)
            self.inputSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.inputArea.SetSizer(self.inputSizer)


            self.entry = wx.TextCtrl(self.inputArea)
            self.entry.SetFocus()
            self.action = wx.Button(self.inputArea, label='Send')

            self.inputSizer.Add(self.entry, proportion=1, 
                    flag=wx.EXPAND|wx.ALL)
            self.inputSizer.Add(self.action, proportion=0)

            self.contentSizer.Add(self.outputArea, proportion=1, 
                    flag=wx.EXPAND|wx.ALL)
            self.contentSizer.Add(self.inputArea, proportion=0, 
                    flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
    
    def __init__(self, parent=None, title='JSONAPI Remote Console'):
        super(RemoteConsoleUI, self).__init__(parent, title=title)
        self.controls = self._controls(self)
        self.__initUI()
        self.__onSendHandlers = []
        self.__onCloseHandlers = []
        self.__history = ['']
        self.__history_pos = 0
        self.__handlers = {}
        for event in EVENTS:
            self.__handlers[event] = []

    def __initUI(self):
        self.controls.entry.Bind(wx.EVT_CHAR, self.__evtEntryChar)
        self.controls.action.Bind(wx.EVT_BUTTON, self.__evtAction)
        self.Bind(wx.EVT_CLOSE, self.__evtClose)

    def AddOutput(self, output, scroll = False):
        self.Freeze()
        try:
            if output[-1] != '\n':
                output += '\n'
            self.controls.output.AppendText(output)
            if scroll:
                self.controls.output.ShowPosition(
                        self.controls.output.GetLastPosition())
        finally:
            self.Thaw()

    def ClearOutput (self):
        self.Freeze()
        try:
            self.controls.output.Value = ''
        finally:
            self.Thaw()

    def HistoryBack(self):
        if self.__history_pos > 0:
            self.__history_pos -= 1
            self.controls.entry.Value = self.__history[self.__history_pos]

    def HistoryNext(self):
        if self.__history_pos < len(self.__history) - 1:
            self.__history_pos += 1
            self.controls.entry.Value = self.__history[self.__history_pos]

    def SetHistory(self, history):
        if len(history) < 1:
            return
        if len(history) > 101:
            history = history[-101:]
        self.__history = history
        self.__history_pos = len(self.__history) - 1

    def GetHistory(self):
        return list(self.__history)

    def SendEntry(self):
        value = self.controls.entry.Value
        if len(self.__history) < 2 or self.__history[-2] != value:
            self.__history[-1] = value
            if len(self.__history) > 100:
                self.__history = self.__history[-100:]
            self.__history.append('')
        self.__history_pos = len(self.__history) - 1
        self.AddOutput('>>> ' + value, True)
        for handler in self.__onSendHandlers:
            try:
                result = handler(value)
            except:
                break
            if result == True:
                break
        self.controls.entry.Value = ''
        self.controls.entry.SetFocus()

    def __evtAction(self, event):
        self.SendEntry()
        pass

    def __evtEntryChar(self, event):
        keycode = event.GetKeyCode()
        actions = {
            wx.WXK_RETURN: self.SendEntry,
            wx.WXK_NUMPAD_ENTER: self.SendEntry,
            wx.WXK_PAGEUP: self.controls.output.PageUp,
            wx.WXK_NUMPAD_PAGEUP: self.controls.output.PageUp,
            wx.WXK_PAGEDOWN: self.controls.output.PageDown,
            wx.WXK_NUMPAD_PAGEDOWN: self.controls.output.PageDown,
            wx.WXK_UP: self.HistoryBack,
            wx.WXK_NUMPAD_UP: self.HistoryBack,
            wx.WXK_DOWN: self.HistoryNext,
            wx.WXK_NUMPAD_DOWN: self.HistoryNext,
        }
        actions.get(keycode,event.Skip)()

    def __evtClose(self, event):
        for handler in self.__onCloseHandlers:
            try:
                handler()
            except:
                pass
        event.Skip()

    def bind(self, event, handler):
        if not isinstance(event, str):
            raise TypeError('event must be a string')
        if event not in EVENTS:
            raise ValueError('Unrecognized event "%s"' % event)
        self.__handlers[event] = handler

    def trigger(self, event, data):
        if not isinstance(event, str):
            raise TypeError('event must be a string')
        if event not in EVENTS:
            raise ValueError('Unrecognized event "%s"' % event)
        handled = False
        for handler in self.__handlers[event]:
            try:
                ret = handler(data, handled)
                handled = handled or ret
            except:
                pass

    def _AddHandler(self, handler, pos=None):
        if pos == None or pos >= len(self.__onSendHandlers):
            self.__onSendHandlers.append(handler)
        else:
            self.__onSendHandlers.insert(pos, handler)

    def _AddCloser(self, handler, pos=-1):
        if pos == None or pos >= len(self.__onCloseHandlers):
            self.__onCloseHandlers.append(handler)
        else:
            self.__onCloseHandlers.insert(pos, handler)

if __name__ == '__main__':
    app=wx.App()
    window = RemoteConsoleUI()
    controler = Controller(window)
    controler.loadCommands()
    window.Show()
    app.MainLoop()
