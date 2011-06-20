#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import logging
import logging.config

import gobject
import dbus
from dbus import SessionBus
from dbus.service import Object, BusName, signal, method
from dbus.mainloop.glib import DBusGMainLoop

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("sequencer")

def handle_image_error(e):
    _logger.error("Exception! That's not meant to happen... %s", str(e))

class SeqManager(Object):
    def __init__(self, bus, loop):
        name = BusName('es.ucm.Pontifex.Sequencer', bus)
        path = '/'
        super(SeqManager, self).__init__(name, path)
        self.loop = loop

        self.instruments = {}

        _logger.info('Looking for instruments')
        for i in session.list_names():
            if str(i).startswith('es.ucm.Pontifex.Instrument'):
                shortname = i[27:]
                _logger.info('Instrument %s', shortname)
                proxy = bus.get_object(i, '/')
                proxy.connect_to_signal('SequenceEnded', self.handle_seq_ended)
                self.instruments[shortname] = proxy

        self.db_i = bus.get_object('es.ucm.Pontifex.DBengine', '/')
        self.db_i_if = dbus.Interface(self.db_i, dbus_interface='es.ucm.Pontifex.DBengine')

        _logger.info('Waiting for commands')

    @method(dbus_interface='es.ucm.Pontifex.Sequencer')
    def quit(self):
        _logger.info('Ending')
        self.loop.quit()

    @method(dbus_interface='es.ucm.Pontifex.Sequencer',
            in_signature='', out_signature='as')
    def available_instruments(self):
        return self.instruments.keys()

    def handle_seq_ended(self):
        _logger.info('Sequence finished')
        self.db_i_if.end_obsblock()

    def handle_image_reply(self, value):
        _logger.info('Exposure process with id %i', value)

    @method(dbus_interface='es.ucm.Pontifex.ObservingModes',
            in_signature='i', out_signature='')
    def bias_megara(self, repeat):
        
        name = 'MEGARA'
        ins = self.instruments[name]

        ins_if = dbus.Interface(ins, dbus_interface='es.ucm.Pontifex.Instrument')

        check = self.db_i_if.start_obsblock(name, 'bias')
        if check:
            ins_if.expose('bias', repeat, 0.0, reply_handler=self.handle_image_reply, 
                            error_handler=handle_image_error)
        else:
            _logger.info('Current observing block has not finished yet')   
        

    @method(dbus_interface='es.ucm.Pontifex.ObservingModes',
            in_signature='di', out_signature='')
    def dark_megara(self, exposure, repeat):
        
        name = 'MEGARA'
        ins = self.instruments[name]

        ins_if = dbus.Interface(ins, dbus_interface='es.ucm.Pontifex.Instrument')

        check = self.db_i_if.start_obsblock(name, 'dark')
        if check:
            for i in range(repeat):
                ins_if.expose('dark', exposure)
            self.db_i_if.end_obsblock()
        else:
            _logger.info('Current observing block has not finished')

    @method(dbus_interface='es.ucm.Pontifex.ObservingModes',
            in_signature='dii', out_signature='')
    def flat_megara(self, exposure, repeat, filterpos):

        name = 'MEGARA'
        ins = self.instruments[name]
        ins_if = dbus.Interface(ins, dbus_interface='es.ucm.Pontifex.Instrument')

        fw_i = dbus.SessionBus().get_object('es.ucm.Pontifex.Instrument.MEGARA', '/Spectrograph0/Wheel0')
        fw_i_if = dbus.Interface(fw_i, dbus_interface='es.ucm.Pontifex.Wheel')

        self.db_i_if.start_obsblock(name, 'flat')
        fw_i_if.set_position(filterpos)
        for i in range(repeat):
            ins_if.expose('flat', exposure)
        self.db_i_if.end_obsblock()

    @method(dbus_interface='es.ucm.Pontifex.ObservingModes',
            in_signature='di', out_signature='')
    def dark_test(self, exposure, repeat):
        # what we need
        bus = dbus.SessionBus()

        self.db_i_if.start_obsblock('test', 'dark')
        for i in range(repeat):
            self.test_i_if.expose('dark', exposure)
        self.db_i_if.end_obsblock()

    @method(dbus_interface='es.ucm.Pontifex.ObservingModes',
            in_signature='i', out_signature='')
    def bias_test(self, repeat):
        # what we need
        bus = dbus.SessionBus()
        test_i = bus.get_object('es.ucm.Pontifex.Instrument.Test', '/')
        test_i_if = dbus.Interface(test_i, dbus_interface='es.ucm.Pontifex.Instrument')

        self.db_i_if.start_obsblock('test', 'bias')
        for i in range(repeat):
            test_i_if.expose('bias', 0)
        self.db_i_if.end_obsblock()

    @method(dbus_interface='es.ucm.Pontifex.ObservingModes',
            in_signature='dii', out_signature='')
    def flat_test(self, exposure, repeat, filterpos):
        # what we need
        bus = dbus.SessionBus()
        test_i = bus.get_object('es.ucm.Pontifex.Instrument.Test', '/')
        test_i_if = dbus.Interface(test_i, dbus_interface='es.ucm.Pontifex.Instrument')

        fw_i = bus.get_object('es.ucm.Pontifex.Instrument.Test', '/Wheel0')
        fw_i_if = dbus.Interface(test_i, dbus_interface='es.ucm.Pontifex.Wheel')


        self.db_i_if.start_obsblock('test', 'flat')
        # Put the filter
        #r = fw_i_if.set(filterpos)
        for i in range(repeat):
            test_i_if.expose('flat', exposure)
        self.db_i_if.end_obsblock()
        self.db_i_if.end_obsrun()

    def parse_run_cmd(self, args):
        # arg0 -> instrument
        # arg1 -> obsmode
        # arg2 -> repeat
            
        if args[0] == 'test':
            if args[1] == 'bias':
                try:
                    self.bias_test(int(args[2]))
                except Exception,e:
                    _logger.error('%s', str(e))
            elif args[1] == 'dark':
                try:
                    repeat = int(args[2])
                    exposure = float(args[3])
                    self.dark_test(exposure, repeat)
                except Exception,e:
                    _logger.error('%s', str(e))
            elif args[1] == 'flat':
                try:
                    repeat = int(args[2])
                    exposure = float(args[3])
                    filterpos = int(args[4])
                    self.flat_test(exposure, repeat, filterpos)
                except Exception,e:
                    _logger.error('%s', str(e))
                pass
            else:
                _logger.info('Observing mode %s not implemented', args[1])
        if args[0].lower() == 'megara':
            if args[1] == 'bias':
                try:
                    self.bias_megara(int(args[2]))
                except Exception,e:
                    _logger.error('%s', str(e))
            elif args[1] == 'dark':
                try:
                    repeat = int(args[2])
                    exposure = float(args[3])
                    self.dark_megara(exposure, repeat)
                except Exception,e:
                    _logger.error('%s', str(e))
            elif args[1] == 'flat':
                try:
                    repeat = int(args[2])
                    exposure = float(args[3])
                    filterpos = int(args[4])
                    self.flat_megara(exposure, repeat, filterpos)
                except Exception,e:
                    _logger.error('%s', str(e))
                pass
            else:
                _logger.info('Observing mode %s not implemented', args[1])                
        else:
            _logger.info('Instrument %s not implemented', args[0])        



    @method(dbus_interface='es.ucm.Pontifex.Sequencer.Console',
            in_signature='s', out_signature='')
    def console(self, command):
        _logger.info('Console command: "%s"', command)
        # More inteligent split is needed
        # Something that respects ws betwwen ""
        cmdline = command.split()
        npar = len(cmdline)
        if cmdline[0] == 'startobsrun':
            if npar != 2:
                _logger.warning('Malformed command line  "%s"', command)
            else:
                arg = str(cmdline[1])
                obsrunid = self.db_i_if.start_obsrun(arg)    
                _logger.info('Observing run started')        
                _logger.info('Observing runId %i', obsrunid)        
        elif cmdline[0] == 'endobsrun':
            self.db_i_if.end_obsrun()
            _logger.info('Observing run ended')
#            _logger.info('Observing runId %i', obsrunid) 
        elif cmdline[0] == 'run':
            if npar < 4:
                _logger.warning('Malformed command line  "%s"', command)
            self.parse_run_cmd(cmdline[1:])
        else:
            _logger.warning('Command line  "%s" not recognized', command)
        
dbus_loop = DBusGMainLoop()
session = SessionBus(mainloop=dbus_loop)

loop = gobject.MainLoop()
gobject.threads_init()

seq = SeqManager(session, loop)
loop.run()

