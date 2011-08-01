#!/usr/bin/python
import sys
import csv

from Common.Events import Event
def trim_docstring(docstring):
    '''Trim whitespace from string according to python docstring conventions.
    '''
    if not docstring:
        return ''
    lines = docstring.expandtabs().splitlines()
    indent = sys.maxint
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    trimmed = [lines[0].strip()]
    if indent < sys.maxint:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    return '\n'.join(trimmed)

class Command (object):
    @staticmethod
    def annotate(**kwargs):
        def decorate(f):
            for k in kwargs:
                setattr(f, k, kwargs[k])
            return f
        return decorate

    def __init__(self,
            handler,
            name=None, 
            parameters=None,
            description=None,
            detail_help=None,
            environment=None,
            visible=None,
            events=None):
        '''Create a command object for use in Minecraft Remote Console.

        All optional arguments will be determined through introspection of the 
        handler if not provided.

        Arguments:
            handler -- Command handler, provide a Command object for alias.
            name -- name of command.
            parameters -- A list of strings naming command parameters.
            description -- A short one-line description of the command.
            detail_help -- Detailed help text explaining function use.
            environment -- A list of two-tuples of the form:
                (variable_used, short_description_of_use)
            visible -- Set visiblity of command to unfiltered help
            events -- a list of Event.TYPE_* to listen to
        '''
        resolve = lambda x,y: x if x != None else y

        if isinstance(handler, Command):
            if name is None:
                raise ValueError('Name must be provided for alias commands')
            parameters = resolve(parameters, handler.parameters)
            description = resolve(description, handler.description)
            detail_help = resolve(detail_help, handler.detail_help)
            environment = resolve(environment, handler.environment)
            visible = resolve(visible, False)
            events = resolve(events, handler.events)
            handler = handler.handler

        if not callable(handler):
            raise TypeError('handler must be callable')
        self.handler = handler

        if name is not None:
            if not isinstance(name, basestring):
                raise TypeError('name must be a string')
        else:
            name = handler.__name__
        self.name = name

        if parameters is not None:
            _valid = True
            if (not isinstance(parameters, list) and 
                    not isinstance(parameters,tuple)):
                raise TypeError('parameters must be a sequence type')
            for val in parameters:
                if not isinstance(val, basestring):
                    raise ValueError('parameters must be sequence of strings')
            self.__optional_parameters = len([1 for i in parameters 
                                                if i.startswith('_')])
            paratrim = lambda x: x[1:] if x.startswith('_') else x
            parameters = [paratrim(x) for x in parameters]
        else:
            self.__optional_parameters = 0
            parameters = []
        self.parameters = parameters

        _docstr = trim_docstring(handler.__doc__)
        if description is not None:
            if not isinstance(description, basestring):
                raise TypeError('description must be a string')
        else:
            _lines = _docstr.splitlines()
            description = (_lines[0] if len(_lines) > 0 
                                     else 'No description available')
        self.description = description

        if detail_help is not None:
            if not isinstance(detail_help, basestring):
                raise TypeError('detail_help must be a string')
        else:
            detail_help = ('\n'.join(_docstr.splitlines()[1:]) 
                            if len(_docstr) > 0 
                            else '')
        self.detail_help = detail_help

        self.environment = resolve(environment, [])
        self.visible = bool(resolve(visible, True))
        self.events = resolve(events, [])
        self.prefix=''

    def invoke(self, event):
        inval ='Invalid parameter count. See `%shelp %s` for details.' 
        if event.event_type == Event.TYPE_INPUT:
            args = len(event.args)-1
            oargs = self.__optional_parameters
            rargs = len(self.parameters) - oargs
            if args < rargs or args > rargs + oargs:
                event.add_output(inval % (self.prefix, self.name))
                event.is_handled = True
                return
        self.handler(event)

    def __str__(self):
        template = 'Usage: {prefix}{name} {opts}\n\n{desc}\n{det}'
        otemplate = 'Usage: {prefix}{name} {ropts} [{oopts}]\n\n{desc}\n{det}'
        rparams = len(self.parameters) - self.__optional_parameters
        if self.__optional_parameters:
            return otemplate.format(
                    prefix = self.prefix,
                    name= self.name,
                    ropts=' '.join(self.parameters[:rparams]),
                    oopts=' '.join(self.parameters[rparams:]),
                    desc=self.description,
                    det=self.detail_help)
        return template.format(
                    prefix = self.prefix,
                    name= self.name,
                    opts=' '.join(self.parameters[:rparams]),
                    desc=self.description,
                    det=self.detail_help)


class CommandCategory(object):
    def __init__(self, prefix, name, description = None):
        self.prefix = prefix
        self.name = name
        self.description = description
        self.__commands = {}
        self.add_builtins()

    def __help(self, event):
        '''Show help for command category
        '''
        vars_used = 'Variables used:'
        if len(event.args) == 1:
            cmds = [c for c 
                      in self.__commands.get(Event.TYPE_INPUT, {}).values()
                      if c.visible]
            cmds.sort(lambda x,y: cmp(x.name, y.name))
            event.add_output('Available Commands')
            for cmd in cmds:
                event.add_output('{prefix}{name} - {desc}'.format(
                    prefix = cmd.prefix,
                    name = cmd.name,
                    desc = cmd.description
                ))
        else:
            cmd = (self.__commands
                    .get(Event.TYPE_INPUT,{}).get(event.args[1],None))
            if cmd != None:
                event.add_output(str(cmd))
            else:
                event.add_output('Command "%s" not found.' % event.args[1])
            
        event.is_handled = True
                

    def add_command(self, command):
        '''Add command to this category

        The add operation may overwrite an existing command if name collision
        occurs.
        '''
        command.prefix = self.prefix
        for evt in command.events:
            if evt not in self.__commands.keys():
                self.__commands[evt] = {}
            self.__commands[evt][command.name] = command

    def clear_commands(self, event_types=[Event.TYPE_INPUT]):
        '''Clear all commands from category

        This included the automatically added Help command'''
        for evt in event_types:
            self.__commands[evt] = {}

    def add_builtins(self):
        '''Add builtin commands to the command category'''
        self.add_command(Command(lambda x: self.__help(x),
            name='help',
            description='Show help for command category',
            parameters=['_cmd'],
            events=[Event.TYPE_INPUT]))

    def invoke(self, event):
        '''Invoke the event for all registered listeners in this category.
        '''
        def resolve_cmd(type_, name):
            evt = self.__commands.get(type_, {})
            return evt.get(name, None)
        def run_cmd(cmd):
            try:
                cmd.invoke(event)
            except Exception as e:
                event.add_output('Command encountered unexpected error: %s'%e)
                event.stop_propagation = True
                raise 
        if event.event_type & Event.TYPE_INPUT != 0: # InputEvents are special
            if event.data and event.data[0] == self.prefix:
                cmd = resolve_cmd(event.event_type, event.args[0][1:])
                if cmd == None:
                    event.add_output ('Unrecognized command')
                    event.is_handled = True
                else:
                    run_cmd(cmd)
        else:
            for cmd in self.__commands.get(event.event_type, {}).values():
                run_cmd(cmd)

# vim: shiftwidth=4:softtabstop=4:expandtab:autoindent:syntax=python
