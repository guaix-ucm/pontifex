#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import time
import threading
import logging
import logging.config
from Queue import Queue
import hashlib
import datetime

import gobject
import dbus
from dbus import SessionBus
from dbus.service import Object, BusName, signal, method
from dbus.mainloop.glib import DBusGMainLoop
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
    
from sql import Base
from ptimer import PeriodicTimer
from dbins import datadir
from sql import ObsRun, ObsBlock, Images, ProcessingBlockQueue, get_last_image_index, get_unprocessed_obsblock, DataProcessing

engine = create_engine('sqlite:///operation.db', echo=True)
Base.metadata.create_all(engine) 
Session = sessionmaker(bind=engine)

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("datafactory")

dbus_loop = DBusGMainLoop()
dsession = SessionBus(mainloop=dbus_loop)

class DatafactoryManager(Object):
    def __init__(self, bus, loop):
        name = BusName('es.ucm.Pontifex.DFP', bus)
        path = '/'

        self.loop = loop
        self.timer = None
        self.repeat = 5
        self.doned = False
        self.queue = Queue(4)
        self.qback = Queue()
        self.images = 0
        super(DatafactoryManager, self).__init__(name, path)
        _logger.info('Waiting for commands')

        self.session_w = Session()


    @method(dbus_interface='es.ucm.Pontifex.DFP')
    def quit(self):
        _logger.info('Ending')
        self.doned = True
        self.qback.put(None)
        self.queue.put(None)
        self.queue.put(None)
        self.loop.quit()

    def version(self):
    	return '1.0'

    def watchdog(self):
        if self.doned:
            _logger.info('Cleaning up PENDING jobs')
            for i in self.session_w.query(ProcessingBlockQueue).filter_by(status='PENDING'):
                i.status = 'NEW'
            self.session_w.commit()            
            return
        else:
            _logger.info('Checking database for ObsBlocks')
            # do something here ...
            for i in get_unprocessed_obsblock(self.session_w):
                if i.status == 'NEW':
                    _logger.info('Enqueueing job %d for obsblock %d', i.pblockId, i.obsId)
                    self.queue.put((i.obsblock.instrument, i.obsblock.mode, i.pblockId, i.obsId))
                    i.status = 'PENDING'
                    self.session_w.commit()

    def inserter(self):
        session_i = Session()
        # clean up
        for i in get_unprocessed_obsblock(session_i):
            if i.status == 'PENDING':
                _logger.info('Fixing job %d', i.obsId)
                i.status = 'NEW'
            session_i.commit()

        while True:
            val = self.qback.get()
            if self.doned or val is None:
                _logger.info('Insert thread finished')
                return
            else:
                _, pid, oid = val
                _logger.info('Updating done work, obsblock %d', oid)
                myobsblock = session_i.query(ProcessingBlockQueue).filter_by(pblockId=pid).one() 
                myobsblock.status = 'DONE'
                dp = DataProcessing()
                dp.obsId = oid
                dp.status = 'DONE'
                dp.stamp = datetime.datetime.utcnow()
                m = hashlib.md5()
                m.update(str(time.time()))
                dp.hashdir = m.digest()
                session_i.add(dp)
                session_i.commit()
                self.qback.task_done()

    def consumer(self):
        while True:
            val = self.queue.get()
            if self.doned:
                return
            if val is not None:
                ins, mod, pid, oid = val
                _logger.info('Processing %s, %s, %d, %d', ins, mod, pid, oid)
                time.sleep(20)
                self.queue.task_done()
                self.qback.put(('workdone', pid, oid))
            else:
                return


loop = gobject.MainLoop()
gobject.threads_init()

im = DatafactoryManager(dsession, loop)

POLL = 5
timer = PeriodicTimer(POLL, im.watchdog)
timer.start()

inserter = threading.Thread(target=im.inserter)
inserter.start()

consumer = threading.Thread(target=im.consumer)
consumer.start()

consumer2 = threading.Thread(target=im.consumer)
consumer2.start()

try:
    loop.run()
except KeyboardInterrupt:
    im.quit()
    timer.end()
