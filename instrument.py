#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import logging
import logging.config

import numpy
import numpy.random
from dbus.service import Object, BusName, signal, method

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("instrument")

class InstrumentDetector(Object):
    def __init__(self, description, bus, ibusname, ipath, logger=None, cid=0):
        name = BusName(ibusname, bus)
        path = '%s/Detector%d' % (ipath, cid)
        super(InstrumentDetector, self).__init__(name, path)

        self.logger = logger if logger is not None else _logger
        self.shape = description.shape
        self.model = description.model
        self.biaslevel = description.bias
        self.dark = description.dark
        self.gain = description.gain
        self.ron = description.ron
        self.buffer = numpy.zeros(self.shape)

    @method(dbus_interface='es.ucm.Pontifex.Instrument.Detector',
            in_signature='', out_signature='')
    def reset(self):
        self.buffer.fill(0)

    @method(dbus_interface='es.ucm.Pontifex.Instrument.Detector',
            in_signature='d', out_signature='')
    def expose(self, exposure):
        self.logger.info('Exposing exposure=%6.1f', exposure)
        #time.sleep(exposure)
        self.buffer += self.dark * exposure

    def readout(self):
        data = numpy.random.normal(self.buffer, self.ron, self.buffer.shape)
        # readout destroys data
        self.reset()
        
        data /= self.gain
        data += self.biaslevel
        data = data.astype('int32')
        return data

class InstrumentFilterWheel(Object):
    def __init__(self, bus, ibusname, ipath, logger=None, cwid=0):
        name = BusName(ibusname, bus)
        path = '%s/FilterWheel%d' % (ipath, cwid)
        self.logger = logger if logger is not None else _logger
        self.fwpos = 0
        self.fwmax = 4

        super(InstrumentFilterWheel, self).__init__(name, path)
 
    @method(dbus_interface='es.ucm.Pontifex.FilterWheel',
            in_signature='i', out_signature='i')
    def turn(self, position):
        self.fwpos += (position % self.fwmax)
        self.logger.info('Turning filter wheel %d %d positions', self.fwid, position)
        return self.fwpos

    @method(dbus_interface='es.ucm.Pontifex.FilterWheel',
            in_signature='i', out_signature='i')
    def set(self, position):
        self.fwpos = (position % self.fwmax)
        self.logger.info('Setting filter wheel to %d position', self.fwid)
        return self.fwpos


class InstrumentManager(Object):
    def __init__(self, name, bus, loop, logger):

        self.name = name
        self.busname = 'es.ucm.Pontifex.Instrument.%s' % self.name
        self.path = '/es/ucm/Pontifex/Instrument/%s' % self.name

        bname = BusName(self.busname, bus)

        self.loop = loop
        self.logger = logger
        super(InstrumentManager, self).__init__(bname, self.path)

    @method(dbus_interface='es.ucm.Pontifex.Instrument')
    def quit(self):
        self.logger.info('Ending')
        self.loop.quit()
    
    def version(self):
    	return '1.0'

