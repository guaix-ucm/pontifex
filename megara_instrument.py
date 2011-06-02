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

dirad = {'bias': 'BIAS', 'dark': 'DARK'}

class MegaraInstrumentManager(InstrumentManager):
    def __init__(self, description, bus, loop):
        super(MegaraInstrumentManager, self).__init__(description.name, bus, loop, _logger)

        self.fw0 = InstrumentFilterWheel(bus, self.busname, self.path, _logger, cwid=0)
        self.fw1 = InstrumentFilterWheel(bus, self.busname, self.path, _logger, cwid=1)

        self.detectors = []

        for cid, detinfo in enumerate(description.detectors):
            self.detectors.append(InstrumentDetector(detinfo, bus, self.busname, 
                                    self.path, _logger, cid=cid))

        self.db = bus.get_object('es.ucm.Pontifex.DBengine', '/es/ucm/Pontifex/DBengine')
        self.dbi = dbus.Interface(self.db, dbus_interface='es.ucm.Pontifex.DBengine')
        # Metadata in a dictionary

        self.meta = {}
        _logger.info('Loading default FITS headers')
        sfile = 'megara_header.txt'
        self.header = pyfits.Header(txtfile=sfile)
        self.header.update('INSTRUME', 'MEGARA')
        self.header.update('ORIGIN', 'Pontifex')
        self.header.update('OBSERVER', 'Pontifex')
        _logger.info('Ready')

    @method(dbus_interface='es.ucm.Pontifex.Instrument',
            in_signature='sd', out_signature='')
    def expose(self, imgtyp, exposure):
        filtid = self.fw0.fwpos
        _logger.info('Exposing image type=%s, exposure=%6.1f, filter ID=%d', imgtyp, exposure, filtid)
        for det in self.detectors:
            det.expose(exposure)
        _logger.info('Reading out')
        alldata = [det.readout() for det in self.detectors]

        self.meta['exposure'] = exposure
        self.meta['imgtyp'] = str(imgtyp)
        self.create_fits_file(alldata)

    def create_fits_file(self, alldata):
        # Add headers, etc
        # This should run in a thread, probably...
        _logger.info('Creating FITS data')
        hdr = self.header.copy()
        hdr['EXPOSED'] = self.meta['exposure']
        hdr['IMGTYP'] = self.meta['imgtyp']
        hdr['FILTER'] = self.fw0.fwpos
        hdr['OBSTYPE'] = self.meta['imgtyp']
        hdr['IMAGETY'] = self.meta['imgtyp']
        # These fields should be updated
        hdr['OBS_MODE'] = 'FALSE'
        hdr['DATE'] = '2010-02-01T03:03:45'        
        hdr['DATE-OBS'] = '2010-02-01T03:03:45'
        hdr['MDJ-OBS'] = 238237283
        hdr['AIRMASS'] = 1.23234
        
        hdu0 = pyfits.PrimaryHDU(alldata[0], hdr)
        hdu0.header['FILTER'] = self.fw0.fwpos

        hdus = [pyfits.ImageHDU(data, hdr) for data in alldata[1:]]

        #hdu1.header['FILTER'] = self.fw1.fwpos

        hdulist = pyfits.HDUList([hdu0] + hdus)

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

import numina3

_logger.info('Loading instrument configuration')
idescrip = numina3.parse_instrument('megara.instrument')

im = MegaraInstrumentManager(idescrip, dsession, loop)
loop.run()

