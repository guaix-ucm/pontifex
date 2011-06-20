#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import logging
import logging.config

import gobject
import dbus
from dbus import SessionBus
from dbus.service import Object, BusName, signal, method
from dbus.mainloop.glib import DBusGMainLoop

def dum1(val):
    print "dum1 %i" % val

def dum2(*args):
    print "dum2", args

dbus_loop = DBusGMainLoop()
session = SessionBus(mainloop=dbus_loop)
proxy = session.get_object('com.example.Service2', '/')
test_i = dbus.Interface(proxy, dbus_interface='com.example.Service2')

bus = SessionBus(mainloop=DBusGMainLoop())
gobject.threads_init()
loop = gobject.MainLoop()

test_i.expose(reply_handler=dum1, error_handler=dum2)
test_i.expose(reply_handler=dum1, error_handler=dum2)
test_i.expose(reply_handler=dum1, error_handler=dum2)
test_i.expose(reply_handler=dum1, error_handler=dum2)

loop.run()
