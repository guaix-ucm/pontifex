#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import time
import datetime
from StringIO import StringIO
import logging
import logging.config
import tempfile

import pyfits
import numpy
import gobject
import dbus
from dbus import SessionBus
from dbus.service import Object, BusName, signal, method
from dbus.mainloop.glib import DBusGMainLoop

from pontifex.instrument import InstrumentManager, InstrumentWheel, InstrumentDetector, InstrumentShutter
from pontifex.astrotime import datetime_to_mjd

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("instrument.megara")

dbus_loop = DBusGMainLoop()
dsession = SessionBus(mainloop=dbus_loop)

dirad = {'bias': 'BIAS', 'dark': 'DARK'}


class MegaraInstrumentSpectrograph(Object):
    def __init__(self, description, bus, ibusname, ipath, logger, cwid=0):
        busname = BusName(ibusname, bus=dbus.SessionBus())
        path = '%sSpectrograph%d' % (ipath, cwid)
        super(MegaraInstrumentSpectrograph, self).__init__(busname, path)
        self.cid = cwid
        self.gw = InstrumentWheel(bus, ibusname, path, _logger, cwid=0)

        self.st = InstrumentShutter(bus, ibusname, path, _logger, cwid=0)
        detinfo = description
        self.detector = InstrumentDetector(detinfo, bus, ibusname, 
                                    path, _logger, cid=0)
        self.data = None # buffer
        # Metadata in a dictionary
        self.meta = {}
        _logger.info('Ready')

    @method(dbus_interface='es.ucm.Pontifex.Instrument',
            in_signature='sd', out_signature='')
    def expose(self, imgtyp, exposure):
        grismid = self.gw.fwpos
        _logger.info('Exposing spectrograph %d, mode=%s, exposure=%6.1f, grism ID=%d', self.cid, imgtyp, exposure, grismid)

        self.detector.expose(exposure)
        _logger.info('Reading out')
        self.data = self.detector.readout()

        self.meta['exposure'] = exposure
        self.meta['imgtyp'] = str(imgtyp)
        self.meta['obsmode'] = str(imgtyp)

    def create_fits_hdu(self, hdr):
        if self.data is None:
            return
        # Add headers, etc
        # This should run in a thread, probably...
        _logger.info('Creating FITS HDU')
        hdr['EXPOSED'] = self.meta['exposure']
        hdr['EXPTIME'] = self.meta['exposure']
        hdr['IMGTYP'] = self.meta['imgtyp']
        hdr['GRISM'] = self.gw.fwpos
        hdr['OBSTYPE'] = self.meta['imgtyp']
        hdr['IMAGETY'] = self.meta['imgtyp']
        hdr['OBS_MODE'] = self.meta['imgtyp'].upper()
        # These fields should be updated

        now = datetime.datetime.now()
        hdr['DATE'] = now.isoformat()
        hdr['DATE-OBS'] = self.detector.meta['DATE-OBS']
        hdr['MDJ-OBS'] = self.detector.meta['MDJ-OBS']
        hdr['GAIN'] = self.detector.gain
        hdr['READNOIS'] = self.detector.ron
        hdr['SUNIT'] = self.cid
        #hdr['AIRMASS'] = 1.23234
        #hdr.update('RA', str(target.ra))    
        #hdr.update('DEC', str(target.dec))
        if self.cid == 0:
            return pyfits.PrimaryHDU(self.data, hdr)
        else:
            return pyfits.ImageHDU(self.data, hdr)


class MegaraInstrumentManager(InstrumentManager):
    def __init__(self, description, bus, loop):
        super(MegaraInstrumentManager, self).__init__(description.name, bus, loop, _logger)
        
        _logger.info('Loading default FITS headers')
        sfile = 'megara_header.txt'
        self.header = pyfits.Header(txtfile=sfile)
        self.header.update('ORIGIN', 'Pontifex')
        self.header.update('OBSERVER', 'Pontifex')        

        self.sps = []
        for cid, detinfo in enumerate(description.detectors):
            st = MegaraInstrumentSpectrograph(detinfo, bus, self.busname, self.path, _logger, cwid=cid)
            self.sps.append(st)


        #self.db = bus.get_object('es.ucm.Pontifex.DBengine', '/')
        #self.dbi = dbus.Interface(self.db, dbus_interface='es.ucm.Pontifex.DBengine')
        # Metadata in a dictionary

        self.meta = {}
        
        _logger.info('Ready')

    @method(dbus_interface='es.ucm.Pontifex.Instrument',
            in_signature='sd', out_signature='')
    def expose(self, imgtyp, exposure):
        _logger.info('Exposing image type=%s, exposure=%6.1f', imgtyp, exposure)
        for sp in self.sps:
            sp.expose(imgtyp, exposure)
    
        header = self.header.copy()


        alldata = [sp.create_fits_hdu(header) for sp in self.sps]
        self.create_fits_file(alldata)

    def create_fits_file(self, alldata):
        _logger.info('Creating FITS data')
        hdulist = pyfits.HDUList(alldata)
        # Preparing to send binary data back to sequencer
        #fd, filepath = tempfile.mkstemp()
        hdulist.writeto('scratch.fits', clobber=True)
        #self.dbi.store_file(filepath)

    def version(self):
    	return '1.0'

loop = gobject.MainLoop()
gobject.threads_init()

import numina3

_logger.info('Loading instrument configuration')
idescrip = numina3.parse_instrument('megara.instrument')

im = MegaraInstrumentManager(idescrip, dsession, loop)
im.expose('dark', 10)
loop.run()

