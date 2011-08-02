#!/usr/bin/python
import csv

class Event(object):
    #TODO: Names, not codes
    TYPE_PREINPUT = 'PREINPUT'
    TYPE_INPUT = 'INPUT'
    TYPE_OUTPUT = 'OUTPUT'
    TYPE_QUIT = 'QUIT'
    TYPE_CONNECT = 'CONNECT'
    TYPE_DISCONNECT = 'DISCONNECT'
    TYPE_KEYPRESS = 'KEYPRESS'
    TYPE_ANY = [
        TYPE_PREINPUT,
        TYPE_INPUT,
        TYPE_OUTPUT,
        TYPE_QUIT,
        TYPE_CONNECT,
        TYPE_DISCONNECT,
        TYPE_KEYPRESS
    ]
    event_type = TYPE_ANY
    def __init__(self, data, after=None):
        self.event_type = Event.TYPE_ANY
        self.data = data
        self.clear_input = False
        _args = None
        try:
            _args = list(csv.reader([data.rstrip()], delimiter=' '))
        except Exception:
            pass
        self.args = _args[0] if _args else []
        self.is_canceled = False
        self.is_handled = False
        self.scroll_output = False
        self.stop_execution = False
        self.after = after
        self.env = {}
        self.__output = []
        self.__triggered_events = []
        self.set_input = False
        self.input = ''

    def add_output(self, output):
        '''Add to the output of the event.

        Will be displayed to users
        '''
        self.__output.append(output)

    def get_output(self):
        return list(self.__output)

    def add_triggered_event(self, event):
        self.__triggered_events.append(event)

    def get_triggered_events(self):
        return list(self.__triggered_events)

class PreInputEvent(Event):
    event_type = Event.TYPE_PREINPUT
    def __init__(self, data, *args, **kwargs):
        super(PreInputEvent, self).__init__(data, *args, **kwargs)
        self.event_type = Event.TYPE_PREINPUT
        self.add_output('>>> %s' % data)
        self.set_input = True
        evt = InputEvent(data)
        self.add_triggered_event(evt)

class InputEvent(Event):
    event_type = Event.TYPE_INPUT
    def __init__(self, data, *args, **kwargs):
        super(InputEvent, self).__init__(data, *args, **kwargs)
        self.event_type = Event.TYPE_INPUT

class OutputEvent(Event):
    event_type = Event.TYPE_OUTPUT
    def __init__(self, data, *args, **kwargs):
        super(OutputEvent, self).__init__(data, *args, **kwargs)
        self.event_type = Event.TYPE_OUTPUT

class QuitEvent(Event):
    event_type = Event.TYPE_QUIT
    def __init__(self, data, *args, **kwargs):
        super(QuitEvent, self).__init__(data, *args, **kwargs)
        self.event_type = Event.TYPE_QUIT

class ConnectEvent(Event):
    event_type = Event.TYPE_CONNECT
    def __init__(self, data, *args, **kwargs):
        super(ConnectEvent, self).__init__(data, *args, **kwargs)
        self.event_type = Event.TYPE_CONNECT

class DisconnectEvent(Event):
    event_type = Event.TYPE_DISCONNECT
    def __init__(self, data, *args, **kwargs):
        super(DisconnectEvent, self).__init__(data, *args, **kwargs)
        self.event_type = Event.TYPE_DISCONNECT

class KeyPressEvent(Event):
    event_type = Event.TYPE_KEYPRESS
    def __init__(self, data, key, *args, **kwargs):
        super(KeyPressEvent, self).__init__(data, *args, **kwargs)
        self.event_type = Event.TYPE_KEYPRESS
        self.key = key

# vim: shiftwidth=4:softtabstop=4:expandtab:autoindent:syntax=python
