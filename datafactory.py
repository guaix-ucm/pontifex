#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import time
import threading
import logging
import logging.config
from Queue import Queue
import hashlib
import datetime
from xmlrpclib import Server, ProtocolError, Error

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
from txrServer import txrServer

engine = create_engine('sqlite:///operation.db', echo=True)
Base.metadata.create_all(engine) 
Session = sessionmaker(bind=engine)

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("datafactory")

dbus_loop = DBusGMainLoop()
dsession = SessionBus(mainloop=dbus_loop)

df_server = Server('http://127.0.0.1:7080')

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
        self.slaves = {}
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

    def register(self, hostid, host, port, capabilities):
        if hostid not in self.slaves:
            self.slaves[hostid]= (Server('%s:%d' % (host, port)), capabilities, True)
            _logger.info('Host registered %s %s %s %s', id, host, port, capabilities)

    def find_server(self, number, recipe, instrument, slaves):
        _logger.info('Finding server for observation number=%s, mode=%s, instrument=%s', number, recipe, instrument)
        
        for idx in self.slaves:
            server, cap, idle = self.slaves[idx]
            if idle and instrument in cap:
                _logger.info('Sending to server number=%s', idx)
                server.pass_info(number, recipe, instrument)
                self.slaves[idx] = (server, cap, False)
                return idx


        #pending.put((number, recipe, instrument))
        _logger.info('No server for observation number=%s, mode=%s, instrument=%s', number, recipe, instrument)
        
        return None


    def watchdog(self):
        session_w = Session()
        while True:
            if self.doned:
                _logger.info('Cleaning up PENDING jobs')
                for i in session_w.query(ProcessingBlockQueue).filter_by(status='PENDING'):
                    i.status = 'NEW'
                session_w.commit()
                _logger.info('Watchdog thread is finished')          
                return
            else:            
                time.sleep(5)
                for i in session_w.query(ProcessingBlockQueue).filter_by(status='NEW')[:4]:
                    _logger.info('Enqueueing job %d for obsblock %d', i.pblockId, i.obsId)
                    self.queue.put((i.obsblock.instrument, i.obsblock.mode, i.pblockId, i.obsId))
                    i.status = 'PENDING'
                    session_w.commit()

    def inserter(self):
        session_i = Session()
        # clean up
        q = session_i.query(ProcessingBlockQueue).filter_by(status='PENDING')
        for i in q:
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
            if self.doned or val is None:
                _logger.info('Consumer thread is finished')
                return
            else:
                ins, mod, pid, oid = val
                _logger.info('Processing %s, %s, %d, %d', ins, mod, pid, oid)
                time.sleep(20)
                self.queue.task_done()
                self.qback.put(('workdone', pid, oid))

loop = gobject.MainLoop()
gobject.threads_init()

im = DatafactoryManager(dsession, loop)

tserver = txrServer(('localhost', 7081), allow_none=True, logRequests=False)
tserver.register_instance(im.register)
xmls = threading.Thread(target=tserver.serve_forever)
xmls.start()

POLL = 5
_logger.info('Polling database for new ObsBlocks every %d seconds', POLL)
timer = threading.Thread(target=im.watchdog)
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
    tserver.shutdown()

