#!/usr/bin/python

#
# Copyright 2011 Sergio Pascual
# 
# This file is part of Pontifex
# 
# Pontifex is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# PyEmir is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with PyEmir.  If not, see <http://www.gnu.org/licenses/>.
#

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import sys
import threading
import logging
import logging.config
from Queue import Queue
import uuid
import ConfigParser
from xmlrpclib import ServerProxy
import signal
    
from numina import main2
from txrServer import txrServer

logging.config.fileConfig("logging.ini")

# create logger
_logger = logging.getLogger("pontifex.host")

class PontifexHost(object):
    def __init__(self, master, host, port):
        super(PontifexHost, self).__init__()
        uid = uuid.uuid5(uuid.NAMESPACE_URL, 'http://%s:%d' % (host, port))
        self.cid = uid.hex
        self.host = host
        self.port = port
        self.rserver = ServerProxy(master)
        self.rserver.register(self.cid, host, port, ['emir', 'frida', 'megara'])

        self.doned = False
        self.queue = Queue()

        _logger.info('ready')

    def quit(self):
        _logger.info('ending')
        self.rserver.unregister(self.cid)
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

# signal handler
def handler(signum, frame):
    im.quit()
    tserver.shutdown()
    im.doned = True
    sys.exit(0)

# Set the signal handler on SIGTERM and SIGINT
signal.signal(signal.SIGTERM, handler)
signal.signal(signal.SIGINT, handler)

xmls = threading.Thread(target=tserver.serve_forever)
xmls.start()

worker = threading.Thread(target=im.worker)
worker.start()

while not im.doned:
    signal.pause()


