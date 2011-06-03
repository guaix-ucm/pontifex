#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import time
from StringIO import StringIO
import logging
import logging.config

import pyfits
import numpy
import gobject
import dbus
from dbus import SessionBus
from dbus.service import Object, BusName, signal, method
from dbus.mainloop.glib import DBusGMainLoop

from instrument import InstrumentManager, InstrumentFilterWheel, InstrumentDetector

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("instrument.test")

dbus_loop = DBusGMainLoop()
dsession = SessionBus(mainloop=dbus_loop)

cards = [pyfits.Card('EXPOSED', 0, 'Exposure time')]
cards.append(pyfits.Card('IMGTYP', 'NONE', 'Image type'))
cards.append(pyfits.Card('FILTER', '0', 'Filter'))
head = pyfits.Header(cards)

dirad = {'bias': 'BIAS', 'dark': 'DARK'}

class TestObservingModes(Object):
    def __init__(self, bus):
        self.name = 'Test'
        self.busname = 'es.ucm.Pontifex.Instrument.%s' % self.name
        self.path = '/ObservingModes' % self.name

        bname = BusName(self.busname, bus)

        self.obsmodes = ['bias', 'dark']

        super(TestObservingModes, self).__init__(bname, self.path)

    @method(dbus_interface='es.ucm.Pontifex.ObservingModes',
            in_signature='', out_signature='as')
    def observing_modes(self):
        return self.obsmodes

class TestSequencer(Object):
    def __init__(self, bus):
        self.name = 'Test'
        self.busname = 'es.ucm.Pontifex.Instrument.%s' % self.name
        self.path = '/Secuencer' % self.name

        bname = BusName(self.busname, bus)

        super(TestSequencer, self).__init__(bname, self.path)

    @method(dbus_interface='es.ucm.Pontifex.Sequencer',
            in_signature='os', out_signature='')
    def dum(self, path, method):
        print path


class TestInstrumentManager(InstrumentManager):
    def __init__(self, bus, loop):
        super(TestInstrumentManager, self).__init__('Test', bus, loop, _logger)

        self.fw = InstrumentFilterWheel(bus, self.busname, self.path, _logger)
        self.detector = InstrumentDetector(bus, self.busname, self.path, _logger)

        self.db = bus.get_object('es.ucm.Pontifex.DBengine', '/')
        self.dbi = dbus.Interface(self.db, dbus_interface='es.ucm.Pontifex.DBengine')
        _logger.info('Waiting for commands')

    @method(dbus_interface='es.ucm.Pontifex.Instrument',
            in_signature='sd', out_signature='')
    def expose(self, imgtyp, exposure):
        filtid = self.fw.fwpos
        _logger.info('Exposing image type=%s, exposure=%6.1f, filter ID=%d', imgtyp, exposure, filtid)
        self.detector.expose(exposure)
        _logger.info('Reading out')
        data = self.detector.readout()

        # Add headers, etc
        _logger.info('Creating FITS data')
        hdu = pyfits.PrimaryHDU(data, head)
        hdu.header['EXPOSED'] = exposure        
        hdu.header['IMGTYP'] = str(imgtyp)
        hdu.header['FILTER'] = filtid
        hdulist = pyfits.HDUList([hdu])
        #hdulist.writeto('test.fits', clobber=True)

        # Preparing to send binary data back to sequencer
        handle = StringIO()
        hdulist.writeto(handle)
        hdub = dbus.ByteArray(handle.getvalue())
        # valor 'ay'
        self.dbi.store_image(hdub)

    def version(self):
    	return '1.0'

loop = gobject.MainLoop()
gobject.threads_init()

bm = TestSequencer(dsession)
im = TestInstrumentManager(dsession, loop)
loop.run()

