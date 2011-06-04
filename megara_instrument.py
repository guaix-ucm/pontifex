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

        self.fw = InstrumentWheel(bus, ibusname, path, _logger, cwid=0)

        self.st = InstrumentShutter(bus, ibusname, path, _logger, cwid=0)

        detinfo = description
        self.detector = InstrumentDetector(detinfo, bus, ibusname, 
                                    path, _logger, cid=0)

        # Metadata in a dictionary

        self.meta = {}
        _logger.info('Ready')



class MegaraInstrumentManager(InstrumentManager):
    def __init__(self, description, bus, loop):
        super(MegaraInstrumentManager, self).__init__(description.name, bus, loop, _logger)
        self.sps = []
        for cid, detinfo in enumerate(description.detectors):
            st = MegaraInstrumentSpectrograph(detinfo, bus, self.busname, self.path, _logger, cwid=cid)
            self.sps.append(st)


        #self.db = bus.get_object('es.ucm.Pontifex.DBengine', '/')
        #self.dbi = dbus.Interface(self.db, dbus_interface='es.ucm.Pontifex.DBengine')
        # Metadata in a dictionary

        self.meta = {}
        _logger.info('Loading default FITS headers')
        sfile = 'megara_header.txt'
        self.header = pyfits.Header(txtfile=sfile)
        self.header.update('ORIGIN', 'Pontifex')
        self.header.update('OBSERVER', 'Pontifex')
        _logger.info('Ready')

    @method(dbus_interface='es.ucm.Pontifex.Instrument',
            in_signature='sd', out_signature='')
    def expose(self, imgtyp, exposure):
        filtid = self.sps[0].fw.fwpos
        _logger.info('Exposing image type=%s, exposure=%6.1f, filter ID=%d', imgtyp, exposure, filtid)
        for sp in self.sps:
            sp.detector.expose(exposure)
        _logger.info('Reading out')
        alldata = [sp.detector.readout() for det in self.sps]

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
        hdr['FILTER'] = self.sps[0].fw.fwpos
        hdr['OBSTYPE'] = self.meta['imgtyp']
        hdr['IMAGETY'] = self.meta['imgtyp']
        # These fields should be updated
        hdr['OBS_MODE'] = 'FALSE'
        now = datetime.datetime.now()
        hdr['DATE'] = now.isoformat()
        hdr['DATE-OBS'] = self.sps[0].detector.meta['DATE-OBS']
        hdr['MDJ-OBS'] = self.sps[0].detector.meta['MDJ-OBS']
        hdr['GAIN'] = self.sps[0].detector.gain
        hdr['READNOIS'] = self.sps[0].detector.ron
        #hdr['AIRMASS'] = 1.23234
        #hdr.update('RA', str(target.ra))    
        #hdr.update('DEC', str(target.dec))
        
        hdu0 = pyfits.PrimaryHDU(alldata[0], hdr)
        hdu0.header['FILTER'] = self.sps[0].fw.fwpos

        hdus = [pyfits.ImageHDU(data, hdr) for data in alldata[1:]]
        hdulist = pyfits.HDUList([hdu0] + hdus)

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
loop.run()

