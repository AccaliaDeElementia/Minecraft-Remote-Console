#!/usr/bin/python
import wx

class AdvancedWindow (wx.Frame):
    @staticmethod
    def start_app():
        return wx.App()

    def __init__(self, parent=None, 
            title="Minecraft Remote Console (advanced)", *args, **kwargs):
        super(AdvancedWindow, self).__init__(parent, 
            title=title, *args, **kwargs)
        self.__make_controls()

    def __make_controls(self):
        contentArea = wx.Panel(self)
        contentSizer = wx.BoxSizer(wx.VERTICAL)
        contentArea.SetSizer(contentSizer)

        self._output = wx.TextCtrl(contentArea, 
            style=wx.TE_MULTILINE|wx.TE_READONLY)
        contentSizer.Add(self._output, proportion=1, flag=wx.EXPAND|wx.ALL)

        inputArea = wx.Panel(contentArea)
        contentSizer.Add(inputArea, proportion=0, 
            flag=wx.EXPAND|wx.RIGHT|wx.LEFT)

        inputSizer = wx.BoxSizer(wx.HORIZONTAL)
        inputArea.SetSizer(inputSizer)

        self._entry = wx.TextCtrl(inputArea)
        self._entry.SetFocus()
        inputSizer.Add(self._entry, proportion=1, flag=wx.EXPAND|wx.ALL)

        self._action = wx.Button(inputArea, label='Send')
        inputSizer.Add(self._action, proportion=0)

if __name__ == '__main__':
    app = AdvancedWindow.start_app()
    adv = AdvancedWindow()
    adv.Show()
    app.MainLoop()
# vim: shiftwidth=4:softtabstop=4:expandtab:autoindent:syntax=python
