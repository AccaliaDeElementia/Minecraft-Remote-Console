#!/usr/bin/python

from Advanced.Window import AdvancedWindow
from Advanced.Control import Control
from Common.SystemCommands import SystemCommands
from Common.RemoteCommands import RemoteCommands

if __name__ == '__main__':
    app = AdvancedWindow.start_app()
    window = AdvancedWindow()
    window.Show()
    controler = Control(window)
    sys = SystemCommands(controler)
    remote = RemoteCommands(controler)
    controler.register_commands(sys.create_commands())
    controler.register_commands(remote.create_commands())
    app.MainLoop()
# vim: shiftwidth=4:softtabstop=4:expandtab:autoindent:syntax=python
