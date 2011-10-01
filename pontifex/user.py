
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
import logging.config
from Queue import Queue
from xmlrpclib import ServerProxy
import os.path
from datetime import datetime
import signal
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pontifex.process as process
from pontifex.ptimer import PeriodicTimer
from pontifex.txrServer import txrServer
import pontifex.model as model
from pontifex.model import Session, datadir
from pontifex.model import ObservingRun, ObservingBlock, Image
from pontifex.model import DataProcessingTask, ReductionResult
from pontifex.model import get_last_image_index, get_unprocessed_obsblock, DataProcessing



# create logger
_logger = logging.getLogger("pontifex.server")



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
        _logger.info('ready')

    def quit(self):
        _logger.info('ending')
        self.doned = True
        self.qback.put(None)
        self.queue.put(None)

    def version(self):
    	return '1.0'

    def register(self, hostid, host, port, capabilities):
        with self.clientlock:
            if hostid not in self.client_hosts:
                self.nclient_hosts += 1
                self.client_hosts[hostid]= (ServerProxy('http://%s:%d' % (host, port)), (host, port), capabilities, True)
                _logger.info('host registered %s %s:%d %s', hostid, host, port, capabilities)

    def unregister(self, hostid):
        with self.clientlock:
            _logger.info('unregistering host %s', hostid)
            self.nclient_hosts -= 1
            del self.client_hosts[hostid]


    def find_client(self, session, task):
        _logger.info('finding host for task=%d', task.id)
        for idx in self.client_hosts:
            server, (host, port), cap, idle = self.client_hosts[idx]
            if idle:

                task.state = PROCESSING
                task.host = '%s:%d' % (host, port)
                _logger.info('sending to host %s', task.host)
                session.commit()
                server.pass_info(task.id)
                with self.clientlock:
                    self.nclient_hosts -= 1
                    self.client_hosts[idx] = (server, (host, port), cap, False)
                return idx
        else:
            _logger.info('no server for taskid=%d', task.id)
        
        return None

    def watchdog(self, pollfreq):
        session_w = Session()
        while True:
            if self.doned:
                _logger.info('cleaning up pending jobs')
                for task in session_w.query(DataProcessingTask).filter_by(state=ENQUEUED):
                    task.state = COMPLETED
                session_w.commit()
                _logger.info('watchdog finished')
                return
            else:            
                time.sleep(pollfreq)                
                for task in session_w.query(DataProcessingTask).filter_by(state=COMPLETED)[:self.nclient_hosts]:
                    _logger.info('enqueueing task %d ', task.id)
                    task.state = ENQUEUED
    
                    session_w.commit()
                    self.queue.put(task.id)

    def inserter(self):
        session_i = Session()
        # clean up on startup
        q = session_i.query(DataProcessingTask).filter_by(state=ENQUEUED)
        for i in q:
            _logger.info('fixing job %d', i.id)
            i.state = COMPLETED
        session_i.commit()

        while True:
            val = self.qback.get()
            if self.doned or val is None:
                _logger.info('inserter finished')
                return
            else:
                cid, state, taskid = val
                _logger.info('updating done work, ProcessingTask %d', int(taskid))
                task = session_i.query(DataProcessingTask).filter_by(id=taskid).one() 

                task.completion_time = datetime.utcnow()
                if state == 0:
                    task.state = FINISHED

                    rr = ReductionResult()
                    rr.other = str({})
                    rr.task_id = task.id
                    session_i.add(rr)
                else:
                    task.state = ERROR

                session_i.commit()
                self.qback.task_done()

    def consumer(self):
        session = Session()
        while True:
            taskid = self.queue.get()
            if self.doned or taskid is None:
                _logger.info('consumer is finished')
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
                        _logger.info('query for result of ob id=%d', child)
                        rr = session.query(ReductionResult).filter_by(obsres_id=child).first()
                        if rr is not None:
                            _logger.info('reduction result id is %d', rr.id)
                    fun(**kwds)
                except OSError, AttributeError:
                    task.completion_time = datetime.utcnow()
                    task.state = ERROR
                    session.commit()
                    continue

                cid = self.find_client(session, task)
                if cid is not None:
                    _logger.info('processing taskid %d in host %s', taskid, cid)
                else:
                    self.queue.task_done()                    
                    self.qback.put((0, 1, task.id))
                session.commit()



    def receiver(self, cid, state, taskid):
        self.queue.task_done()
        self.qback.put((cid, state, taskid))
        with self.clientlock:
            self.nclient_hosts += 1
            r = self.client_hosts[cid]
            self.client_hosts[cid] = (r[0], r[1], r[2], True)

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
    _logger.info('polling database for new ProcessingTasks every %d seconds', POLL)
    timer = threading.Thread(target=im.watchdog, args=(POLL, ), name='timer')
    timer.start()

    inserter = threading.Thread(target=im.inserter, name='inserter')
    inserter.start()

    consumer = threading.Thread(target=im.consumer, name='consumer')
    consumer.start()

    while not im.doned:
        signal.pause()
