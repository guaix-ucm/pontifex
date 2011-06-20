#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import time
import datetime
from StringIO import StringIO
import logging
import logging.config
import tempfile
import math
import os

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


def black_body(wl, temp):
    # wl en nm, now in cm
    wl *= 1e-7
    x = 1.43817 / (wl * temp)
    y = 3.742e-05 / wl**5
    return y / (math.exp(x)-1)


class LigthSource:
    def __init__(self, sed, x, y):
        self.sed = sed
        self.x = x
        self.y = y

class MegaraInstrumentSpectrograph(Object):
    def __init__(self, description, bus, ibusname, ipath, logger, cid=0):
        busname = BusName(ibusname, bus=bus)
        path = '%sSpectrograph%d' % (ipath, cid)
        super(MegaraInstrumentSpectrograph, self).__init__(busname, path)
        self.cid = cid
        self.gw = InstrumentWheel(description.wheels[0], bus, ibusname, path, _logger, cid=0)

        self.st = InstrumentShutter(bus, ibusname, path, _logger, cid=0)
        self.detector = InstrumentDetector(description.detectors[0], bus, ibusname, 
                                    path, _logger, cid=0)
        self.data = None # buffer
        # Metadata in a dictionary
        self.meta = {}
        self.logger = logging.getLogger("instrument.megara.spec0")

#    @method(dbus_interface='es.ucm.Pontifex.Instrument',
#            in_signature='sd', out_signature='')
    def expose(self, imgtyp, exposure):
        grismid = self.gw.fwpos
        self.logger.info('Exposing spectrograph %d, mode=%s, exposure=%6.1f, grism ID=%d', self.cid, imgtyp, exposure, grismid)

        # ad hoc number included here
        ls = LigthSource(lambda x: 5e-19 * black_body(x, 5500), 2048, 300)
        ls = self.st.illum(ls)
        ls = self.gw.illum(ls)
        self.detector.illum(ls)

        self.detector.expose(exposure)
        self.logger.info('Reading out')
        self.data = self.detector.readout()

        self.meta['exposure'] = exposure
        self.meta['imgtyp'] = str(imgtyp)
        self.meta['obsmode'] = str(imgtyp)

    def create_fits_hdu(self, hdr):
        if self.data is None:
            return
        # Add headers, etc
        # This should run in a thread, probably...
        self.logger.info('Creating FITS HDU')
        hdr['EXPOSED'] = self.meta['exposure']
        hdr['EXPTIME'] = self.meta['exposure']
        hdr['IMGTYP'] = self.meta['imgtyp']
        hdr['GRISM'] = self.gw.current().name
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

        self.exposing = False
        self.sps = []
        cid = 0
        st = MegaraInstrumentSpectrograph(description.spectrograph, 
                bus, self.busname, self.path, _logger, cid=cid)
        self.sps.append(st)


        self.db = bus.get_object('es.ucm.Pontifex.DBengine', '/')
        self.dbi = dbus.Interface(self.db, dbus_interface='es.ucm.Pontifex.DBengine')
        # Metadata in a dictionary

        self.meta = {}
        
        _logger.info('Ready')


    def quit(self):
        _logger.info('Ending')
        
    @signal(dbus_interface='es.ucm.Pontifex.Instrument', signature='')
    def SequenceStarted(self):
        _logger.info('Sequence started')

    @signal(dbus_interface='es.ucm.Pontifex.Instrument', signature='')
    def SequenceEnded(self):
        _logger.info('Sequence ended (emited)')

    @method(dbus_interface='es.ucm.Pontifex.Instrument',
            in_signature='sid', out_signature='b')
    def expose(self, imgtyp, repeat, exposure):
        if not self.exposing:
            self.exposing = True
            tid = gobject.idle_add(self.internal_expose, imgtyp, repeat, exposure)           
            _logger.info('Thread running id %d', tid)
            return True
        else:
            _logger.info('Already exposing')
            return False

    def internal_expose(self, imgtyp, repeat, exposure):
        self.SequenceStarted()

        for i in range(repeat):

            _logger.info('Exposing image type=%s, exposure=%6.1f', imgtyp, exposure)
            for sp in self.sps:
                sp.expose(imgtyp, exposure)
    
            header = self.header.copy()
            #hdr['AIRMASS'] = 1.23234
            #hdr.update('RA', str(target.ra))    
            #hdr.update('DEC', str(target.dec))    
            alldata = [sp.create_fits_hdu(header) for sp in self.sps]
            self.create_fits_file(alldata)


        self.SequenceEnded()
        self.exposing = False
        return False

    def create_fits_file(self, alldata):
        _logger.info('Creating FITS data')
        hdulist = pyfits.HDUList(alldata)
        # Preparing to send binary data back to database
        fd, filepath = tempfile.mkstemp()
        hdulist.writeto(filepath, clobber=True)
        os.close(fd)
        self.dbi.store_file(filepath)

    def version(self):
    	return '1.0'

loop = gobject.MainLoop()
gobject.threads_init()

import numina3

_logger.info('Loading instrument configuration')
idescrip = numina3.parse_instrument('megara.instrument')

im = MegaraInstrumentManager(idescrip, dsession, loop)

try:
    loop.run()
except KeyboardInterrupt:
    im.quit()
