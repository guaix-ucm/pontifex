#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import logging
import logging.config
import time
from Queue import Queue
import threading
import os

import gobject
import dbus
from dbus import SessionBus
from dbus.service import Object, BusName, signal, method
from dbus.mainloop.glib import DBusGMainLoop

class Service2(Object):
    def __init__(self, bus, loop):
        name = BusName('com.example.Service2', bus)
        super(Service2, self).__init__(name, '/')
        self.lock = threading.Lock()
        self.exposing = False
        self.counter = 1
        self.db = bus.get_object('com.example.Service1', '/')
        self.dbi = dbus.Interface(self.db, dbus_interface='com.example.Service1')

    @method(dbus_interface='com.example.Service2',
            in_signature='', out_signature='i')
    def expose(self):

        return self.internal_expose()

    def internal_expose(self):

        def do_expose():
            print 'calling expose %d' % self.counter            
            self.counter += 1            
            time.sleep(5)
            dd = self.dbi.test('test')
            print 'exposing done'
            self.exposing = False

        if not self.exposing:
            self.exposing = True
            tid = gobject.idle_add(do_expose)        
            return tid
        else:
            print 'no exposing'
            return 0


bus = SessionBus(mainloop=DBusGMainLoop())
gobject.threads_init()
loop = gobject.MainLoop()

im = Service2(bus, loop)

try:
    loop.run()
except:
    pass
