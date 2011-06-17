#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import gobject
import dbus
from dbus import SessionBus
from dbus.service import Object, BusName, signal, method
from dbus.mainloop.glib import DBusGMainLoop

class Service1(Object):
    def __init__(self, bus):
        name = BusName('com.example.Service1', bus)
        path = '/'
        super(Service1, self).__init__(name, path)

    @method(dbus_interface='com.example.Service1',
            in_signature='s', out_signature='s')
    def test(self, test):
        print 'test being called'
        return test

dsession = SessionBus(mainloop=DBusGMainLoop())
loop = gobject.MainLoop()
gobject.threads_init()

im = Service1(dsession)
loop.run()

