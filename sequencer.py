#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import threading
from Queue import Queue
import logging
import logging.config
from xmlrpclib import Server

import gobject
import dbus
from dbus import SessionBus
from dbus.service import Object, BusName, signal, method
from dbus.mainloop.glib import DBusGMainLoop

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("sequencer")

queue = Queue()

instruments = ['test']

dbserver = Server('http://localhost:8050')
insserver = Server('http://localhost:9010')

class SeqManager(Object):
    def __init__(self, bus, loop):
        name = BusName('es.ucm.Pontifex.Sequencer', bus)
        path = '/es/ucm/Pontifex/Sequencer'
        super(SeqManager, self).__init__(name, path)
        self.loop = loop

        _logger.info('Looking for instruments')
        for i in session.list_names():
            if str(i).startswith('es.ucm.Pontifex.Instrument'):
                _logger.info('Instrument %s', str(i))

        _logger.info('Waiting for commands')

    @method(dbus_interface='es.ucm.Pontifex.Sequencer')
    def quit(self):
        _logger.info('Ending')
        self.loop.quit()

    @method(dbus_interface='es.ucm.Pontifex.Sequencer',
            in_signature='di', out_signature='')
    def obsmode_dark_test(self, exposure, repeat):
        # what we need
        bus = dbus.SessionBus()
        test_i = bus.get_object('es.ucm.Pontifex.Instrument.Test', '/es/ucm/Pontifex/Instrument/Test')
        test_i_if = dbus.Interface(test_i, dbus_interface='es.ucm.Pontifex.Instrument')

        db_i = bus.get_object('es.ucm.Pontifex.DBengine', '/es/ucm/Pontifex/DBengine')
        db_i_if = dbus.Interface(db_i, dbus_interface='es.ucm.Pontifex.DBengine')

        obsrunid = db_i_if.start_obsrun('Test')
        db_i_if.start_obsblock('test', 'dark')
        for i in range(repeat):
            test_i_if.expose('dark', exposure)
        db_i_if.end_obsblock()
        db_i_if.end_obsrun()

    @method(dbus_interface='es.ucm.Pontifex.Sequencer',
            in_signature='i', out_signature='')
    def obsmode_bias_test(self, repeat):
        # what we need
        bus = dbus.SessionBus()
        test_i = bus.get_object('es.ucm.Pontifex.Instrument.Test', '/es/ucm/Pontifex/Instrument/Test')
        test_i_if = dbus.Interface(test_i, dbus_interface='es.ucm.Pontifex.Instrument')

        db_i = bus.get_object('es.ucm.Pontifex.DBengine', '/es/ucm/Pontifex/DBengine')
        db_i_if = dbus.Interface(db_i, dbus_interface='es.ucm.Pontifex.DBengine')

        obsrunid = db_i_if.start_obsrun('Test')
        db_i_if.start_obsblock('test', 'bias')
        for i in range(repeat):
            test_i_if.expose('bias', 0)
        db_i_if.end_obsblock()
        db_i_if.end_obsrun()

    @method(dbus_interface='es.ucm.Pontifex.Sequencer',
            in_signature='dii', out_signature='')
    def obsmode_flat_test(self, exposure, repeat, filterpos):
        # what we need
        bus = dbus.SessionBus()
        test_i = bus.get_object('es.ucm.Pontifex.Instrument.Test', '/es/ucm/Pontifex/Instrument/Test')
        test_i_if = dbus.Interface(test_i, dbus_interface='es.ucm.Pontifex.Instrument')

        fw_i = bus.get_object('es.ucm.Pontifex.Instrument.Test', '/es/ucm/Pontifex/Instrument/Test/FilterWheel0')
        fw_i_if = dbus.Interface(test_i, dbus_interface='es.ucm.Pontifex.FilterWheel')

        db_i = bus.get_object('es.ucm.Pontifex.DBengine', '/es/ucm/Pontifex/DBengine')
        db_i_if = dbus.Interface(db_i, dbus_interface='es.ucm.Pontifex.DBengine')

        obsrunid = db_i_if.start_obsrun('Test')
        db_i_if.start_obsblock('test', 'flat')
        # Put the filter
        #r = fw_i_if.set(filterpos)
        for i in range(repeat):
            test_i_if.expose('flat', exposure)
        db_i_if.end_obsblock()
        db_i_if.end_obsrun()

    @method(dbus_interface='es.ucm.Pontifex.Sequencer.Console',
            in_signature='s', out_signature='')
    def console(self, command):
        _logger.info('Console command: "%s"', command)

class SequenceManager(object):
    def __init__(self):
        self._instruments = instruments
        self._c_obsrun_id = 0
        self._c_obsblock_id = 0
        self._c_image_id = 0

    # Console
    def run_command(self, args):
        _logger.info('Received console command %s', args)
        argslist = args.split()
        if argslist[0] in instruments:
    	    queue.put(('instrument',) + tuple(argslist))
            return True
        if argslist[0] == 'startobsrun':
    	    queue.put(tuple(argslist))
            return True
        if argslist[0] == 'endobsrun':
    	    queue.put(tuple(argslist))
            return True
        else:
            _logger.warning('No such instrument')
            return False

    def version(self):
    	return True

    # Instrument
    def return_image(self, cmd):
        _logger.info('Received instrument command % s', cmd)
        queue.put(cmd)
        return True

    def obsrun_id(self, newid):
        _logger.info('Current observing block id=% d', newid)
        self._c_obsrun_id = newid

sm = SequenceManager()

def sequencer():
    global queue
    _logger.info('Waiting for commands')
    while True:
        cmd = queue.get()
        # This cmd comes from the console
        if cmd[0] == 'instrument':
            _logger.info('Observation instrument=%s mode=%s started', cmd[1], cmd[2])
            # Create obsblock
            try:
                insserver.command(cmd[1:])
            except Exception, ex:
                _logger.error('Error %s', ex)
        # This cmd comes from the console
        elif cmd[0] == 'startobsrun':
            _logger.info('Creating ObservingRun entry with info=%s', cmd[1])
            # Create obsblock
            try:
        		dbserver.startobsrun(cmd)
            except Exception, ex:
                _logger.error('Error %s', ex)
        elif cmd[0] == 'endobsrun':
            _logger.info('Ending current ObservingRun')
            try:
        		dbserver.endobsrun()
            except Exception, ex:
                _logger.error('Error %s', ex)
        # This cmd comes from the instrument
        elif cmd[0] == 'startobsblock':
            dbserver.startobsblock(cmd)
        # This cmd comes from the instrument
        elif cmd[0] == 'storeob':
            dbserver.endobsblock()
        # This cmd comes from the instrument
        elif cmd[0] == 'store':
            _logger.info('Sending command to storage engine')
            dbserver.store_image(cmd)
        else:
            _logger.warning('Command %s does not exist', cmd[0])

dbus_loop = DBusGMainLoop()
session = SessionBus(mainloop=dbus_loop)

loop = gobject.MainLoop()
gobject.threads_init()

seq = SeqManager(session, loop)
loop.run()

