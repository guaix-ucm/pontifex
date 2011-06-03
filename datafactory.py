#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

from dbins import session, datadir
from sql import ObsRun, ObsBlock, Images, ProcessingBlockQueue, get_last_image_index

import logging
import logging.config

import gobject
import dbus
from dbus import SessionBus
from dbus.service import Object, BusName, signal, method
from dbus.mainloop.glib import DBusGMainLoop

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("datafactory")

dbus_loop = DBusGMainLoop()
dsession = SessionBus(mainloop=dbus_loop)

class DatafactoryManager(Object):
    def __init__(self, bus, loop):
        name = BusName('es.ucm.Pontifex.DFP', bus)
        path = '/'

        self.loop = loop

        super(DatafactoryManager, self).__init__(name, path)
        _logger.info('Waiting for commands')

    @method(dbus_interface='es.ucm.Pontifex.DFP')
    def quit(self):
        _logger.info('Ending')
        self.loop.quit()

    def version(self):
    	return '1.0'

loop = gobject.MainLoop()
gobject.threads_init()

im = DatafactoryManager(dsession, loop)

def my_func(obid):
    _logger.info('Observing block %d ended, preparing to process', obid)

dsession.add_signal_receiver(my_func, dbus_interface="es.ucm.Pontifex.DBengine",
                    signal_name="signal_end_obsblock")

loop.run()

