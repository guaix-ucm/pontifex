#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

from dbus.service import Object, BusName, signal, method

class InstrumentFilterWheel(Object):
    def __init__(self, bus, ipath, logger, fwid=0):
        name = BusName('es.ucm.Pontifex.Instrument', bus)
        path = '%s/FilterWheel%d' % (ipath, fwid)

        self.fwid = fwid
        self.fwpos = 0
        self.fwmax = 4

        super(InstrumentFilterWheel, self).__init__(name, path)
 
    @method(dbus_interface='es.ucm.Pontifex.Instrument.FilterWheel',
            in_signature='i', out_signature='i')
    def turn_filter_wheel(self, position):
        self.fwpos += (position % self.fwmax)
        self.logger.info('Turning filter wheel %d %d positions', self.fwid, position)
        return self.fwpos

class InstrumentManager(Object):
    def __init__(self, name, bus, loop, logger):

        self.name = name

        bname = BusName('es.ucm.Pontifex.Instrument', bus)
        self.path = '/es/ucm/Pontifex/Instrument/%s' % self.name

        self.loop = loop
        self.logger = logger
        super(InstrumentManager, self).__init__(bname, self.path)

    @method(dbus_interface='es.ucm.Pontifex.Instrument')
    def quit(self):
        self.logger.info('Ending')
        self.loop.quit()
    
    def version(self):
    	return '1.0'

