#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import time
import threading
import logging
import logging.config
from Queue import Queue
import hashlib
import datetime
from xmlrpclib import ServerProxy, ProtocolError, Error
import os
import os.path
from datetime import datetime

import gobject
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import process
from ptimer import PeriodicTimer
import model
from model import Session, datadir
from model import ObservingRun, ObservingBlock, Image
from model import DataProcessingTask, ReductionResult
from model import get_last_image_index, get_unprocessed_obsblock, DataProcessing
from txrServer import txrServer

logging.config.fileConfig("logging.ini")

# create logger
_logger = logging.getLogger("pontifex.server")

df_server = ServerProxy('http://127.0.0.1:7080')

# Processing tasks STATES
CREATED, COMPLETED, ENQUEUED, PROCESSING, FINISHED, ERROR = range(6)

class PontifexServer(object):
    def __init__(self, loop):
        super(PontifexServer, self).__init__()

        self.loop = loop
        self.doned = False
        self.queue = Queue()
        self.qback = Queue()
        self.clientlock = threading.Lock()
        self.client_hosts = {}
        self.nclient_hosts = 0
        _logger.info('Started')

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
        with self.clientlock:
            if hostid not in self.client_hosts:
                self.nclient_hosts += 1
                self.client_hosts[hostid]= (ServerProxy('%s:%d' % (host, port)), capabilities, True)
                _logger.info('Host registered %s %s:%d %s', hostid, host, port, capabilities)

    def unregister(self, hostid):
        with self.clientlock:
            self.nclient_hosts -= 1
            del self.client_hosts[hostid]
            _logger.info('Unregistering host %s', hostid)

    def find_client(self, session, task):
        _logger.info('Finding host for task=%d', task.id)
        for idx in self.client_hosts:
            host, cap, idle = self.client_hosts[idx]
            if idle:
                _logger.info('Sending to host %s', idx)
                task.state = PROCESSING
                task.host = idx
                session.commit()
                host.pass_info(task.id)
                with self.clientlock:
                    self.nclient_hosts -= 1
                    self.client_hosts[idx] = (host, cap, False)
                return idx
        else:
            _logger.info('No server for taskid=%d', task.id)
        
        return None

    def watchdog(self):
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
                time.sleep(POLL)                
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
                _logger.info('Updating done work, ProcessingTask %d', int(taskid))
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
                    _logger.info('Processing taskid=%d in host %s', taskid, cid)
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
            self.client_hosts[cid] = (r[0], r[1], True)


engine = create_engine('sqlite:///devdata.db', echo=False)
#engine = create_engine('sqlite:///devdata.db', echo=True)
engine.execute('pragma foreign_keys=on')
engine.execute('pragma timeout=5000')

model.init_model(engine)
model.metadata.create_all(engine)
session = model.Session()

loop = gobject.MainLoop()
gobject.threads_init()

im = PontifexServer(loop)

tserver = txrServer(('localhost', 7081), allow_none=True, logRequests=False)
tserver.register_function(im.register)
tserver.register_function(im.unregister)
tserver.register_function(im.receiver)
xmls = threading.Thread(target=tserver.serve_forever)
xmls.start()

POLL = 5
_logger.info('Polling database for new ProcessingTaskss every %d seconds', POLL)
timer = threading.Thread(target=im.watchdog, name='timer')
timer.start()

inserter = threading.Thread(target=im.inserter, name='inserter')
inserter.start()

consumer = threading.Thread(target=im.consumer, name='consumer')
consumer.start()

try:
    loop.run()
except KeyboardInterrupt:
    im.quit()
    tserver.shutdown()

