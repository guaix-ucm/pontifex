
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
import json
import shutil

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from numina import main2
import pontifex.process as process
from pontifex.ptimer import PeriodicTimer
from pontifex.txrServer import txrServer
import pontifex.model as model
from pontifex.model import Session, datadir, productsdir
from pontifex.model import ObservingRun, ObservingBlock, Image
from pontifex.model import DataProcessingTask, ReductionResult, DataProduct
from pontifex.model import get_last_image_index, get_unprocessed_obsblock, DataProcessing

# create logger
_logger_s = logging.getLogger("pontifex.server")

# Processing tasks STATES
CREATED, COMPLETED, ENQUEUED, PROCESSING, FINISHED, ERROR = range(6)

class PontifexServer(object):
    def __init__(self):
        super(PontifexServer, self).__init__()

        self.doned = False
        self.queue = Queue()
        self.qback = Queue()
        self.clientlock = threading.Lock()
        self.client_hosts = {}
        self.nclient_hosts = 0
        _logger_s.info('ready')

    def quit(self):
        _logger_s.info('ending')
        self.doned = True
        self.qback.put(None)
        self.queue.put(None)

    def version(self):
    	return '1.0'

    def register(self, hostid, host, port, capabilities):
        with self.clientlock:
            if hostid not in self.client_hosts:
                self.nclient_hosts += 1
                self.client_hosts[hostid]= [ServerProxy('http://%s:%d' % (host, port)), (host, port), capabilities, True]
                _logger_s.info('host registered %s %s:%d %s', hostid, host, port, capabilities)

    def unregister(self, hostid):
        with self.clientlock:
            _logger_s.info('unregistering host %s', hostid)
            self.nclient_hosts -= 1
            del self.client_hosts[hostid]


    def find_client(self, session, task):
        _logger_s.info('finding host for task=%d', task.id)
        for idx in self.client_hosts:
            server, (host, port), cap, idle = self.client_hosts[idx]
            if idle:

                task.state = PROCESSING
                task.host = '%s:%d' % (host, port)
                _logger_s.info('sending to host %s', task.host)
                session.commit()
                server.pass_info(task.id)
                with self.clientlock:
                    self.nclient_hosts -= 1
                    self.client_hosts[idx][3] = False
                return idx
        else:
            _logger_s.info('no server for taskid=%d', task.id)
        
        return None

    def watchdog(self, pollfreq):
        session_w = Session()
        while True:
            if self.doned:
                _logger_s.info('cleaning up pending jobs')
                for task in session_w.query(DataProcessingTask).filter_by(state=ENQUEUED):
                    task.state = COMPLETED
                session_w.commit()
                _logger_s.info('watchdog finished')
                return
            else:            
                time.sleep(pollfreq)                
                for task in session_w.query(DataProcessingTask).filter_by(state=COMPLETED)[:self.nclient_hosts]:
                    _logger_s.info('enqueueing task %d ', task.id)
                    task.state = ENQUEUED
    
                    session_w.commit()
                    self.queue.put(task.id)

    def inserter(self):
        session_i = Session()
        # clean up on startup
        q = session_i.query(DataProcessingTask).filter_by(state=ENQUEUED)
        for i in q:
            _logger_s.info('fixing job %d', i.id)
            i.state = COMPLETED
        session_i.commit()

        while True:
            val = self.qback.get()
            if self.doned or val is None:
                _logger_s.info('inserter finished')
                return
            else:
                cid, result, taskid = val
                _logger_s.info('updating done work, ProcessingTask %d', int(taskid))
                task = session_i.query(DataProcessingTask).filter_by(id=taskid).one() 

                task.completion_time = datetime.utcnow()
                if 'error' not in result:
                    task.state = FINISHED
                    
                    results = {}
                    results['control'] = ['task-control.json']
                    results['log'] = ['processing.log']
                    results['products'] = result['products']

                    task.result = str(results)
                    rr = ReductionResult()

                    # Read result.json
                    # Store it here
                    rr.other = str(result)
                    # cd back
                    #os.chdir(pwd)
                    rr.task_id = task.id

                    # processing data products
                    for prod, desc in result['products'].items():
                        # FIXME: this is a hack
                        # because fits files get a list of entries
                        # instead of a single entry

                        if isinstance(desc, list) and desc:
                            mdesc = desc[0]
                        dp = DataProduct()
                        # FIXME, hardcoded instrument name
                        dp.instrument = "clodia"
                        dp.datatype = prod
                        dp.reference = mdesc
                        # copy or hardlink the file
                        _logger.debug('copying product in %s', productsdir)
                        shutil.copy(mdesc, productsdir)
                        # in 'products'
                        dp.task = task
                        session_i.add(dp)

                    session_i.add(rr)
                else:
                    _logger.warning('error in task %d', task.id)
                    _logger.warning('error is task %d', result['error']['type'])
                    task.result = str(results)
                    task.state = ERROR

                session_i.commit()
                self.qback.task_done()

    def consumer(self):
        session = Session()
        while True:
            taskid = self.queue.get()
            if self.doned or taskid is None:
                _logger_s.info('consumer is finished')
                return
            else:
                task = session.query(DataProcessingTask).filter_by(id=taskid).first()
                task.start_time = datetime.utcnow()

                assert(task.state == ENQUEUED)
                try:
                    fun = getattr(process, task.method)
                    #kwds = eval(task.request)
                    kwds = {}
                    kwds['id'] = task.id
                    kwds['children'] = []
                    kwds['images'] = task.observing_result.images
                    kwds['mode'] = task.observing_result.mode
                    kwds['instrument'] = task.observing_result.instrument_id

                    # get images...
                    # get children results
                    for child in kwds['children']:
                        _logger_s.info('query for result of ob id=%d', child)
                        rr = session.query(ReductionResult).filter_by(obsres_id=child).first()
                        if rr is not None:
                            _logger_s.info('reduction result id is %d', rr.id)
                    val = fun(session, **kwds)
                except Exception:
                    task.completion_time = datetime.utcnow()
                    task.state = ERROR
                    _logger_s.warning('error creating root for task %d', taskid)
                    session.commit()
                    continue

                cid = self.find_client(session, task)
                if cid is not None:
                    _logger_s.info('processing taskid %d in host %s', taskid, cid)
                else:
                    self.queue.task_done()                    
                    self.qback.put((0, 1, task.id))
                session.commit()

    def receiver(self, cid, result, taskid):
        self.queue.task_done()
        self.qback.put((cid, result, taskid))
        with self.clientlock:
            self.nclient_hosts += 1
            self.client_hosts[cid][3] = True

# create logger for host
_logger = logging.getLogger("pontifex.host")

class PontifexHost(object):
    def __init__(self, master, host, port):
        super(PontifexHost, self).__init__()
        uid = uuid.uuid5(uuid.NAMESPACE_URL, 'http://%s:%d' % (host, port))
        self.cid = uid.hex
        self.host = host
        self.port = port
        self.rserver = ServerProxy(master)
        self.rserver.register(self.cid, host, port, ['clodia'])

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
                result = main2(['-d','--basedir', 'task/%s' % taskid, 
                    '--datadir', 'data', '--run', filename])
                
                _logger.info('finished')
                
                self.queue.task_done()
                self.rserver.receiver(self.cid, result, taskid)
            else:
                _logger.info('ending worker thread')
                return


def main_host():

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

def main_server():

    logging.config.fileConfig("logging.ini")

    df_server = ServerProxy('http://127.0.0.1:7080')

    engine = create_engine('sqlite:///devdata.db', echo=False)
    #engine = create_engine('sqlite:///devdata.db', echo=True)
    engine.execute('pragma foreign_keys=on')

    model.init_model(engine)
    model.metadata.create_all(engine)
    session = model.Session()

    im = PontifexServer()

    tserver = txrServer(('localhost', 7081), allow_none=True, logRequests=False)
    tserver.register_function(im.register)
    tserver.register_function(im.unregister)
    tserver.register_function(im.receiver)

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

    POLL = 5
    _logger_s.info('polling database for new ProcessingTasks every %d seconds', POLL)
    timer = threading.Thread(target=im.watchdog, args=(POLL, ), name='timer')
    timer.start()

    inserter = threading.Thread(target=im.inserter, name='inserter')
    inserter.start()

    consumer = threading.Thread(target=im.consumer, name='consumer')
    consumer.start()

    while not im.doned:
        signal.pause()
