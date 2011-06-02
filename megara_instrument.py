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
_logger = logging.getLogger("instrument.megara")

dbus_loop = DBusGMainLoop()
dsession = SessionBus(mainloop=dbus_loop)

cards = [pyfits.Card('EXPOSED', 0, 'Exposure time')]
cards.append(pyfits.Card('IMGTYP', 'NONE', 'Image type'))
cards.append(pyfits.Card('FILTER', '0', 'Filter'))
head = pyfits.Header(cards)

dirad = {'bias': 'BIAS', 'dark': 'DARK'}

class MegaraObservingModes(Object):
    def __init__(self, bus):
        self.name = 'Megara'
        self.busname = 'es.ucm.Pontifex.Instrument.%s' % self.name
        self.path = '/es/ucm/Pontifex/Instrument/%s/ObservingModes' % self.name

        bname = BusName(self.busname, bus)

        self.obsmodes = ['bias', 'dark']

        super(MegaraObservingModes, self).__init__(bname, self.path)

    @method(dbus_interface='es.ucm.Pontifex.ObservingModes',
            in_signature='', out_signature='as')
    def observing_modes(self):
        return self.obsmodes

class MegaraSequencer(Object):
    def __init__(self, bus):
        self.name = 'Megara'
        self.busname = 'es.ucm.Pontifex.Instrument.%s' % self.name
        self.path = '/es/ucm/Pontifex/Instrument/%s/Secuencer' % self.name

        bname = BusName(self.busname, bus)

        super(MegaraSequencer, self).__init__(bname, self.path)

    @method(dbus_interface='es.ucm.Pontifex.Sequencer',
            in_signature='os', out_signature='')
    def dum(self, path, method):
        print path


class MegaraInstrumentManager(InstrumentManager):
    def __init__(self, bus, loop):
        super(MegaraInstrumentManager, self).__init__('Megara', bus, loop, _logger)

        self.fw0 = InstrumentFilterWheel(bus, self.busname, self.path, _logger, cwid=0)
        self.fw1 = InstrumentFilterWheel(bus, self.busname, self.path, _logger, cwid=1)
        self.detector0 = InstrumentDetector(bus, self.busname, self.path, _logger, cid=0)
        self.detector1 = InstrumentDetector(bus, self.busname, self.path, _logger, cid=1)

        self.db = bus.get_object('es.ucm.Pontifex.DBengine', '/es/ucm/Pontifex/DBengine')
        self.dbi = dbus.Interface(self.db, dbus_interface='es.ucm.Pontifex.DBengine')
        _logger.info('Ready')

    @method(dbus_interface='es.ucm.Pontifex.Instrument',
            in_signature='sd', out_signature='')
    def expose(self, imgtyp, exposure):
        filtid = self.fw0.fwpos
        _logger.info('Exposing image type=%s, exposure=%6.1f, filter ID=%d', imgtyp, exposure, filtid)
        self.detector0.expose(exposure)
        self.detector1.expose(exposure)
        _logger.info('Reading out')
        data0 = self.detector0.readout()
        data1 = self.detector1.readout()

        # Add headers, etc
        _logger.info('Creating FITS data')
        hdu0 = pyfits.PrimaryHDU(data0, head)
        hdu0.header['EXPOSED'] = exposure        
        hdu0.header['IMGTYP'] = str(imgtyp)
        hdu0.header['FILTER'] = self.fw0.fwpos

        hdu1 = pyfits.ImageHDU(data1, head)
        hdu1.header['EXPOSED'] = exposure        
        hdu1.header['IMGTYP'] = str(imgtyp)
        hdu1.header['FILTER'] = self.fw0.fwpos

        hdulist = pyfits.HDUList([hdu0, hdu1])

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

im = MegaraInstrumentManager(dsession, loop)
loop.run()

