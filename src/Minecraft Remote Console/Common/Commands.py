#!/usr/bin/python
import sys
import csv
from inspect import getargspec

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
    def __init__(self,
            handler,
            name=None, 
            parameters=None,
            description=None,
            detail_help=None,
            environment=None,
            visible=None):
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
        '''

        if isinstance(handler, Command):
            resolve = lambda x,y: x if x is not None else y
            if name is None:
                raise ValueError('Name must be provided for alias commands')
            parameters = resolve(parameters, handler.parameters)
            description = resolve(description, handler.description)
            detail_help = resolve(detail_help, handler.detail_help)
            environment = resolve(environment, handler.environment)
            visible = resolve(visible, False)
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
        else:
            _args = getargspec(handler)
            self.__optional_parameters = len(_args.defaults)
            parameters = _args.args
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
                            else 'No help text available')
        self.detail_help = detail_help

        self.environment = environment if environment is not None else []
        self.visible = bool(visible) if visible is not None else True
        self.prefix=''

    def invoke(self, parameters):
        if (not isinstance(parameters, list) and 
                not isinstance(parameters, tuple)):
            raise TypeError('parameters must be a sequence type')
        plen = len(paramters)
        alen = len(self.parameters)
        olen = alen - self.__optional_parameters
        if plen > alen or plen < olen:
            raise ValueError('Invalid parameter count')
        return self.handler(*parameters, **{})

    def __str__(self):
        template = 'Usage: {prefix}{name} {ropts} [{oopts}]\n\n{desc}\n{det}'
        rparams = len(self.parameters) - self.__optional_parameters
        return template.format(
                    prefix = self.prefix,
                    name= self.name,
                    ropts=' '.join(self.parameters[:rparams]),
                    oopts=' '.join(self.parameters[rparams:]),
                    desc=self.description,
                    det=self.detail_help)


class CommandCategory(object):
    def __init__(self, prefix, name, description = None)
        self.prefix = prefix
        self.name = name
        self.description = description
        self.__commands = {}

    def add_command(self, command):
        command.prefix = self.prefix
        self.__commands[command.name] = command

    def invoke(self, input_):
        def _parse_args (args):
            parsed = list(csv.reader([args], delimiter=' '))
            return parsed[0] if len(parsed) > 0 else []
        command, sep, args = input_.partition(' ')
        if command in self.__commands:
            parameters = _parse_args(args)
            rvalue = ''
            try:
                rvalue = self.__commands[command].invoke(parameters)
            except Exception as e:
                rvalue = 'Command encountered unexpected error: ' + str(e)
            return rvalue
        else:
            return 'Unrecognized command'

# vim: shiftwidth=4:softtabstop=4:expandtab:autoindent:syntax=python
