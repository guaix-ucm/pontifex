#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import datetime
import StringIO
import logging
import logging.config
import os.path
import os
from datetime import datetime
from threading import Semaphore

import pyfits
import gobject
import dbus
from dbus import SessionBus
from dbus.service import Object, BusName, signal, method
from dbus.mainloop.glib import DBusGMainLoop, threads_init
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import model
from model import datadir
from model import ObservingRun, ObservingBlock, Image, get_last_image_index

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("sequence")

FORMAT = 'r%05d.fits'

engine = create_engine('sqlite:///devdata.db', echo=False)
#engine = create_engine('sqlite:///devdata.db', echo=True)
engine.execute('pragma foreign_keys=on')

from dbus.mainloop.glib import threads_init
threads_init()

model.init_model(engine)
model.metadata.create_all(engine)
from sqlalchemy.orm import scoped_session, sessionmaker
Session = scoped_session(sessionmaker())

dbus_loop = DBusGMainLoop(set_as_default=True)
bus = SessionBus(mainloop=dbus_loop)

loop = gobject.MainLoop()

def create_observing_run(userid, instrument):
    obsrun = ObservingRun()
    obsrun.pi_id = userid
    obsrun.instrument_id = instrument
    obsrun.state = 'RUNNING'
    obsrun.start_time = datetime.utcnow()
    Session.add(obsrun)
    return obsrun

def create_observing_block(mode, observer, parent):
    oblock = ObservingBlock()
    oblock.observing_mode = mode
    oblock.observer_id = observer
    parent.obsblocks.append(oblock)
    Session.add(oblock)
    return oblock


def dum(p='a'):
    print p

def end_observing_run(obsrun):
    #obsrun.completion_time = datetime.utcnow()
    #obsrun.state = 'FINISHED'
    pass
    
def end_observing_block(oblock):
    oblock.completion_time = datetime.utcnow()

meg = bus.get_object('es.ucm.Pontifex.Instrument.megara', '/')
meg_iface = dbus.Interface(meg, dbus_interface='es.ucm.Pontifex.Instrument')

shutter = bus.get_object('es.ucm.Pontifex.Instrument.megara', '/Spectrograph0/Shutter0')
shutter_iface = dbus.Interface(shutter, dbus_interface='es.ucm.Pontifex.Shutter')

wheel = bus.get_object('es.ucm.Pontifex.Instrument.megara', '/Spectrograph0/Wheel0')
wheel_iface = dbus.Interface(wheel, dbus_interface='es.ucm.Pontifex.Wheel')


import dbus.service

class Seq(dbus.service.Object):
    def __init__(self):
        # Observing run
        self.obr = create_observing_run(1, 'megara')

        obk1 = create_observing_block('bias', 1, self.obr)
        obk2 = create_observing_block('dark', 1, self.obr)
        obk3 = create_observing_block('flat', 1, self.obr)

        seq1 = [shutter_iface.close, lambda : meg_iface.expose('bias', 2, 0.0)]
        seq2 = [shutter_iface.close, lambda : meg_iface.expose('dark', 2, 100.0)]
        seq3 = [lambda : wheel_iface.set_position(5), 
            shutter_iface.open, 
            lambda : meg_iface.expose('flat', 2
        , 100.0)]

        self.obks = [obk1, obk2, obk3]
        self.seqs = [seq1, seq2, seq3]

        self.obk = self.obks[0]
        self.seq = self.seqs[0]
        self.my = 0

    def mainfunc(self):
        # Tree of Observing Results
        self.obk.start_time = datetime.utcnow()
        # Loop
    
        # Start sequence
        for oper in self.seq:
            # On end exposure signal insert image on database
            oper()
    
        # On end observing result create reduction task
        return False

    def end_obs_run(self):
        end_observing_run(self.obsrun)
        Session.commit()
        loop.quit()
        return False

    def end_block(self):
        print 'hola'
        end_observing_block(self.obk)
        Session.commit()
        
       
        self.my += 1
        #val = gobject.source_remove(self.cid)
        #print val

        if self.my < len(self.obks):
            self.obk = self.obks[self.my]
            self.seq = self.seqs[self.my]
            print 'new sequence'
            self.cid = gobject.idle_add(sequ.mainfunc)
            print self.cid
        else:
            print 'end obsrun'
            self.cid = gobject.idle_add(sequ.end_obsrun)

    def handle_image(self, filepath):
        print 'handle %s' % filepath
        os.system('rm -f %s' % filepath)
    

sequ = Seq()

bus.add_signal_receiver(sequ.handle_image,
                        dbus_interface="es.ucm.Pontifex.Instrument",
                        signal_name="ImageWritten")

bus.add_signal_receiver(sequ.end_block,
                        dbus_interface="es.ucm.Pontifex.Instrument",
                        signal_name="SequenceEnded")
    
sequ.cid = gobject.idle_add(sequ.mainfunc)
print sequ.cid

loop.run()

