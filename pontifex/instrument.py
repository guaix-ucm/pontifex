#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import logging
import logging.config
import datetime

import numpy
from numpy.random import normal
import dbus
from dbus.service import Object, BusName, signal, method

from astrotime import datetime_to_mjd

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("instrument")

class InstrumentDetector(Object):
    def __init__(self, description, bus, ibusname, ipath, logger=None, cid=0):
        busname = BusName(ibusname, bus=dbus.SessionBus())
        if ipath == '/':
            path = '/Detector%d' % (cid,)
        else:
            path = '%s/Detector%d' % (ipath,cid)
        super(InstrumentDetector, self).__init__(busname, path)

        self.logger = logger if logger is not None else _logger
        self.shape = description.shape
        self.model = description.model
        self.biaslevel = description.bias
        self.dark = description.dark
        self.gain = description.gain
        self.ron = description.ron
        self.buffer = numpy.zeros(self.shape)
        self.amplifiers = description.amps
        self.meta = {}

    @method(dbus_interface='es.ucm.Pontifex.Instrument.Detector',
            in_signature='', out_signature='')
    def reset(self):
        self.buffer.fill(0)

    @method(dbus_interface='es.ucm.Pontifex.Instrument.Detector',
            in_signature='d', out_signature='')
    def expose(self, exposure):
        self.logger.info('exposing exposure=%6.1f', exposure)
        now = datetime.datetime.now()
        # Recording time of start of exposure
        self.meta['DATE-OBS'] = now.isoformat()
        self.meta['MDJ-OBS'] = datetime_to_mjd(now)
        self.buffer += self.dark * exposure

    def readout(self):        
        data = self.buffer.copy()
        for amp in self.amplifiers:            
            if amp.ron > 0:
                try:
                    data[amp.shape] = normal(self.buffer[amp.shape], amp.ron)
                except Exception, e:
                    self.logger.error(str(e))
            data[amp.shape] /= amp.gain
        data += self.biaslevel
        data = data.astype('int32')
        # readout destroys data
        self.buffer.fill(0)
        return data

class InstrumentWheel(Object):
    def __init__(self, bus, ibusname, ipath, logger=None, cid=0):
        name = BusName(ibusname, bus)
        if ipath == '/':
            path = '/Wheel%d' % (cid,)
        else:
            path = '%s/Wheel%d' % (ipath, cid)

        super(InstrumentWheel, self).__init__(name, path)
        self.logger = logger if logger is not None else _logger
        self.cid = cid
        self.fwpos = 0
        self.fwmax = 4

    @method(dbus_interface='es.ucm.Pontifex.Wheel',
            in_signature='i', out_signature='i')
    def turn(self, position):
        self.fwpos += (position % self.fwmax)
        self.logger.info('Turning Wheel%d %d positions', self.cid, position)
        return self.fwpos

    @method(dbus_interface='es.ucm.Pontifex.Wheel',
            in_signature='i', out_signature='i')
    def set(self, position):
        self.fwpos = (position % self.fwmax)
        self.logger.info('Setting Wheel%d to %d position', self.cid, self.fwpos)
        return self.fwpos

class InstrumentShutter(Object):
    def __init__(self, bus, ibusname, ipath, logger=None, cid=0):
        name = BusName(ibusname, bus)
        if ipath == '/':
            path = '/Shutter%d' % (ipath, cid)
        else:
            path = '%s/Shutter%d' % (ipath, cid)
        super(InstrumentShutter, self).__init__(name, path)
        self.logger = logger if logger is not None else _logger
        self.cid = cid
        self.opened = True

    @method(dbus_interface='es.ucm.Pontifex.Shutter',
            in_signature='', out_signature='')
    def open(self):
        self.opened = True

    @method(dbus_interface='es.ucm.Pontifex.Shutter',
            in_signature='', out_signature='')
    def close(self):
        self.opened = False
    

class InstrumentManager(Object):
    def __init__(self, name, bus, loop, logger):

        self.name = name
        self.busname = 'es.ucm.Pontifex.Instrument.%s' % self.name
        self.path = '/'
        bname = BusName(self.busname, bus=dbus.SessionBus())
        super(InstrumentManager, self).__init__(bname, '/')

        self.loop = loop
        self.logger = logger
        self.started()

    @method(dbus_interface='es.ucm.Pontifex.Instrument')
    def quit(self):
        self.logger.info('Ending')
        self.loop.quit()
    
    @signal(dbus_interface='es.ucm.Pontifex.Instrument', signature='')
    def started(self):
        pass

    def version(self):
    	return '1.0'

