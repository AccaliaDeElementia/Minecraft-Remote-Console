#!/usr/bin/python
# vim: set shiftwidth=4 softtabstop=4 expandtab autoindent syntax=python:

import csv
import json
from threading import Thread

class SubscriptionReader(Thread):
    def __init__(self, in_, out_, filter_ = None, formatter=None):
        Thread.__init__(self)
        self.__stream = in_
        self.__writer = out_
        self.__filter = filter_ if filter_ else lambda x: True
        self.__formatter = formatter if formatter else lambda x: x
        self.active = True
        self.daemon = True

    def run(self):
        try:
            while self.active:
                raw = self.__stream.readline()
                # BUGFIX: JSONAPI 1.8.2 emits two bogus bytes at the beginning of each line. Remove them here
                if raw[0] != '{':
                    raw = raw[2:]
                result = json.loads(raw.decode())
                line = self.__formatter(result['success'])

                if self.__filter(line) and self.active:
                    self.__writer(line)
        except Exception as e:
            print (repr(e))
        finally:
            self.__stream.close()

