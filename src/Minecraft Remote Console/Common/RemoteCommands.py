#!/usr/bin/python
import wx
import json
from Common.Commands import CommandCategory, Command
from Common import Events
from Common.MinecraftApi import MinecraftJsonApi

class RemoteCommands(object):
    def __init__(self, controler):
        self.__controler = controler
        self.__datastore = controler.get_datastore('Remote Commands')
        self.__server = None
   
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
            del self.__server
            self.__category.clear_commands()
            self.__category.add_builtins()
            event.is_handled = True
        return Command(on_disconnect, events=[Events.Event.TYPE_DISCONNECT])
    
    #endregion: Connection Events

    #region: Input Events
    #endregion: Input Events
    
    def create_commands(self):
        category = CommandCategory(':', 'Remote JSONAPI Commands', 
            'Commands using JSONAPI')
        self.__category = category

        category.add_command(self.__on_connect())
        category.add_command(self.__on_disconnect())
        return category
# vim: shiftwidth=4:softtabstop=4:expandtab:autoindent:syntax=python
