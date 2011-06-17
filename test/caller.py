#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import logging
import logging.config

import gobject
import dbus
from dbus import SessionBus
from dbus.service import Object, BusName, signal, method
from dbus.mainloop.glib import DBusGMainLoop

dbus_loop = DBusGMainLoop()
session = SessionBus(mainloop=dbus_loop)
proxy = session.get_object('com.example.Service2', '/')
test_i = dbus.Interface(proxy, dbus_interface='com.example.Service2')
test_i.expose()


