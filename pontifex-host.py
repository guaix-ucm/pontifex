#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import sys
import time
import threading
import logging
import logging.config
from Queue import Queue
import hashlib
import datetime
import uuid
import ConfigParser
from xmlrpclib import ServerProxy, ProtocolError, Error
import signal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
    
from numina import main2
from ptimer import PeriodicTimer
from txrServer import txrServer

logging.config.fileConfig("logging.ini")

# create logger
_logger = logging.getLogger("pontifex.host")

class PontifexHost(object):
    def __init__(self, master, host, port):
        super(PontifexHost, self).__init__()
        uid = uuid.uuid5(uuid.NAMESPACE_URL, 'http://%s:%d' % (host, port))
        self.cid = uid.hex
        self.rserver = ServerProxy(master)
        self.rserver.register(self.cid, 'http://%s' % host, port, ['emir', 'frida', 'megara'])

        self.timer = None
        self.repeat = 5
        self.doned = False
        self.queue = Queue()
        self.qback = Queue()
        self.images = 0

        _logger.info('ready')

    def quit(self):
        _logger.info('ending')
        self.rserver.unregister(self.cid)
        self.doned = True
        self.qback.put(None)
        self.queue.put(None)
        self.queue.put(None)

    def version(self):
    	return '1.0'

    def pass_info(self, taskid):
        _logger.info('received taskid=%d', taskid)
        self.queue.put(taskid)

    def worker(self):
        while True:
            taskid = self.queue.get()
            if taskid is not None:
                filename = 'task-control.json'
                _logger.info('processing taskid %d', taskid)
                state = main2(['-d','--basedir', 'task/%s' % taskid, 
                    '--datadir', 'data', '--run', filename])
                
                _logger.info('finished')
                
                self.queue.task_done()
                self.rserver.receiver(self.cid, state, taskid)
            else:
                _logger.info('ending worker thread')
                return

if len(sys.argv) != 2:
    sys.exit(1)

cfgfile = sys.argv[1]

config = ConfigParser.ConfigParser()
config.read(cfgfile)

masterurl = config.get('master', 'url')
host = config.get('slave', 'host')
port = config.getint('slave', 'port')

im = PontifexHost(masterurl, host, port)

tserver = txrServer((host, port), allow_none=True, logRequests=False)
tserver.register_function(im.pass_info)

# signal
RUN = True

def handler1(signum, frame):
    global RUN
    im.quit()
    tserver.shutdown()
    RUN = False
    sys.exit(0)

# Set the signal handler and a 5-second alarm
signal.signal(signal.SIGTERM, handler1)
signal.signal(signal.SIGINT, handler1)

xmls = threading.Thread(target=tserver.serve_forever)
xmls.start()

worker = threading.Thread(target=im.worker)
worker.start()

while RUN:
    signal.pause()


