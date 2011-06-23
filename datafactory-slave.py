#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import time
import threading
import logging
import logging.config
from Queue import Queue
import hashlib
import datetime
import uuid
from xmlrpclib import ServerProxy, ProtocolError, Error

import gobject
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
    
from ptimer import PeriodicTimer
from model import Session, datadir
from model import ObsRun, ObsBlock, Images, ProcessingBlockQueue 
from model import get_last_image_index, get_unprocessed_obsblock
from model import DataProcessing
from txrServer import txrServer

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("DF slave")

class DatafactorySlave(object):
    def __init__(self, loop, cid=0):
        super(DatafactorySlave, self).__init__()
        host = 'http://127.0.0.1'
        port = 7090 + cid
        uid = uuid.uuid5(uuid.NAMESPACE_URL, '%s:%d' % (host, port))
        self.cid = uid.hex
        
        self.loop = loop
        self.rserver = ServerProxy('http://127.0.0.1:7081')
        self.rserver.register(self.cid, host, port, ['megara'])

        self.timer = None
        self.repeat = 5
        self.doned = False
        self.queue = Queue()
        self.qback = Queue()
        self.images = 0

        _logger.info('Waiting for commands')
        self.slaves = {}


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

im = DatafactorySlave(loop, cid=cid)

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

