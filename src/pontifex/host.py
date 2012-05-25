#
# Copyright 2011 Universidad Complutense de Madrid
# 
# This file is part of Pontifex
# 
# Pontifex is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Pontifex is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Pontifex.  If not, see <http://www.gnu.org/licenses/>.
#

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import time
import threading
import logging
from Queue import Queue
from xmlrpclib import ServerProxy
import os.path
from datetime import datetime
import signal
import sys
import uuid
import ConfigParser
import shutil

import yaml
from sqlalchemy import create_engine
from numina.user import run_recipe_from_file
from numina.pipeline import init_pipeline_system
from numina.serialize import lookup as lookup_serializer

import pontifex.process as process
from pontifex.txrServer import txrServer
import pontifex.model
from pontifex.model import Session, productsdir
from pontifex.model import ObservingBlock, Instrument, ProcessingSet
from pontifex.model import ContextDescription, ContextValue
from pontifex.model import DataProcessingTask, ReductionResult, DataProduct
from pontifex.server import PontifexServer

# create logger
_logger_s = logging.getLogger("pontifex.server")

# Processing tasks STATES
CREATED, COMPLETED, ENQUEUED, PROCESSING, FINISHED, ERROR = range(6)

# create logger for host
_logger = logging.getLogger("pontifex.host")

# FIXME: global variables
sdum = None
sload = None

class PontifexHost(object):
    def __init__(self, master, host, port):
        super(PontifexHost, self).__init__()
        uid = uuid.uuid5(uuid.NAMESPACE_URL, 'http://%s:%d' % (host, port))
        self.cid = uid.hex
        self.host = host
        self.port = port
        self.rserver = ServerProxy(master)
        self.rserver.register(self.cid, host, port, ['EMIR', 'MEGARA'])

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
        taskdir = os.path.abspath('task')
        while True:
            taskid = self.queue.get()            
            if taskid is not None:
                _logger.info('processing taskid %d', taskid)
                basedir = os.path.join(taskdir, str(taskid))
                workdir = os.path.join(basedir, 'work')
                resultsdir = os.path.join(basedir, 'results')
                filename = os.path.join(resultsdir, 'task-control.json')
                _logger.debug('%s', basedir)
                _logger.debug('%s', workdir)
                _logger.debug('%s', resultsdir)

                # FIXME: global variables
                serformat = 'yaml'
                try:
                    sname, sdump, sload = lookup_serializer(serformat)
                except LookupError:
                    _logger.info('Serialization format %s is not define', serformat)
                    raise

                result = run_recipe_from_file(filename, sload, sdump, workdir=workdir, 
                                    resultsdir=resultsdir, cleanup=False)

                _logger.info('finished')
                
                self.queue.task_done()
                _logger.info('sending to server')
                self.rserver.receiver(self.cid, result, taskid)
                os.chdir(taskdir)
            else:
                _logger.info('ending worker thread')
                return
