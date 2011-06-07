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
_logger = logging.getLogger("DF slave")

dbus_loop = DBusGMainLoop()
dsession = SessionBus(mainloop=dbus_loop)

class DatafactorySlave(Object):
    def __init__(self, bus, loop, cid=0):
        name = BusName('es.ucm.Pontifex.DFP.Slave', bus)
        path = '/%d' % cid
        super(DatafactorySlave, self).__init__(name, path)
        self.cid = cid
        
        self.loop = loop

        self.rserver = Server('http://127.0.0.1:7081')
        self.rserver.register(self.cid, 'http://127.0.0.1', 7090 + self.cid, ['megara'])

        self.timer = None
        self.repeat = 5
        self.doned = False
        self.queue = Queue()
        self.qback = Queue()
        self.images = 0

        _logger.info('Waiting for commands')
        self.slaves = {}
        self.session_w = Session()


    @method(dbus_interface='es.ucm.Pontifex.DFP')
    def quit(self):
        _logger.info('Ending')
        self.rserver.unregister(self.cid)
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

    def pass_info(self, pid, n, tr, i, workdir):
        _logger.info('Received observation number=%s, recipe=%s, instrument=%s', n, tr, i)
        self.queue.put((pid, n, tr, i, workdir))

    def worker(self):
        while True:
            v = self.queue.get()
            if v is not None:
                pid, oid, tr, i, workdir = v
                name = threading.current_thread().name
                _logger.info('Processing observation number=%s, recipe=%s, instrument=%s', oid, tr, i)
                _logger.info('on directory %s', workdir)
                time.sleep(20)
                _logger.info('Finished')
                self.queue.task_done()
                self.rserver.receiver(self.cid, pid, oid, workdir)
            else:
                _logger.info('Ending worker thread')
                return

loop = gobject.MainLoop()
gobject.threads_init()

cid = 0

im = DatafactorySlave(dsession, loop, cid=cid)

tserver = txrServer(('localhost', 7090 + cid), allow_none=True, logRequests=False)
tserver.register_function(im.pass_info)
xmls = threading.Thread(target=tserver.serve_forever)
xmls.start()

worker = threading.Thread(target=im.worker)
worker.start()
try:
    loop.run()
except KeyboardInterrupt:
    im.quit()
    tserver.shutdown()

