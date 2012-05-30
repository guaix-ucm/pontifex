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
import shutil

import yaml

from numina.pipeline import init_pipeline_system

import pontifex.process as process
from pontifex.model import Session, productsdir
from pontifex.model import ObservingBlock, Instrument, ProcessingSet
from pontifex.model import ContextDescription, ContextValue
from pontifex.model import DataProcessingTask, ReductionResult, DataProduct

# create logger
_logger = logging.getLogger("pontifex.server")

# Processing tasks STATES
CREATED, COMPLETED, ENQUEUED, PROCESSING, FINISHED, ERROR = range(6)

def process_(session, task):
    
    kwds = {}
    kwds['id'] = task.id
    kwds['children'] = task.children
    
    node = task.obstree_node
    obsmode = node.observing_mode
    kwds['frames'] = node.frames
    kwds['mode'] = obsmode.key
    recipe = obsmode.module
    print recipe
    

def create_reduction_tree(session, otask, rparent, instrument, pset='default'):
    '''Climb the tree and create DataProcessingTask in nodes.'''
    rtask = DataProcessingTask()
    rtask.parent = rparent
    rtask.obstree_node = otask
    rtask.creation_time = datetime.utcnow()
    if otask.state == 2:
        rtask.state = COMPLETED
    else:
        rtask.state = CREATED
    rtask.method = 'process%s' % otask.label.capitalize()
    request = {'pset': pset, 'instrument': instrument}
    rtask.request = str(request)

    if otask.children:
        rtask.waiting = True
    else:
        rtask.waiting = False

    session.add(rtask)

    for child in otask.children:
        create_reduction_tree(child, rtask, instrument, pset=pset)
    
    return rtask

class PontifexServer(object):
    def __init__(self):
        super(PontifexServer, self).__init__()

        self.doned = False
        self.queue = Queue()
        self.qback = Queue()
        self.clientlock = threading.Lock()
        self.client_hosts = {}
        self.nclient_hosts = 0

        self.ins_config = {}

        init_pipeline_system()

        session = Session()
        for instrument in session.query(Instrument):
            _logger.debug('loading configurations for %s', instrument.name)
            if instrument.valid_configuration:
                _logger.debug('valid configuration for %s', instrument.name)
                self.ins_config[instrument.name] = instrument.valid_configuration.parameters
            else:
                _logger.debug('no valid configuration for %s', instrument.name)

        _logger.info('loaded configuration for %s', self.ins_config.keys())

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
                self.client_hosts[hostid]= [ServerProxy('http://%s:%d' % (host, port)), (host, port), capabilities, True]
                _logger.info('host registered %s %s:%d %s', hostid, host, port, capabilities)

    def unregister(self, hostid):
        with self.clientlock:
            _logger.info('unregistering host %s', hostid)
            self.nclient_hosts -= 1
            del self.client_hosts[hostid]


    def find_client(self, session, task):
        _logger.info('finding host for task=%d', task.id)
        for idx in self.client_hosts:
            server, (host, port), _, idle = self.client_hosts[idx]
            if idle:

                task.state = PROCESSING
                task.host = '%s:%d' % (host, port)
                _logger.info('sending to host %s', task.host)
                session.commit()
                server.pass_info(task.id)
                with self.clientlock:
                    self.nclient_hosts -= 1
                    self.client_hosts[idx][3] = False
                return idx
        else:
            _logger.info('no server for taskid=%d', task.id)
        
        return None

    def watchdog(self, pollfreq):
        session = Session()
        while True:
            if self.doned:
                _logger.info('cleaning up pending jobs')
                for task in session.query(DataProcessingTask).filter_by(state=ENQUEUED):
                    task.state = COMPLETED
                session.commit()
                _logger.info('watchdog finished')
                return
            else:            
                time.sleep(pollfreq)                
                for task in session.query(DataProcessingTask).filter_by(state=COMPLETED, waiting=False)[:self.nclient_hosts]:
                    _logger.info('enqueueing task %d ', task.id)
                    task.state = ENQUEUED
    
                    session.commit()
                    # sending to consumer
                    self.queue.put(task.id)

    def inserter(self):
        session = Session()
        # clean up on startup
        q = session.query(DataProcessingTask).filter_by(state=ENQUEUED)
        for i in q:
            _logger.info('fixing job %d', i.id)
            i.state = COMPLETED
        session.commit()

        while True:
            val = self.qback.get()
            if self.doned or val is None:
                _logger.info('inserter finished')
                return
            else:
                _, result, taskid = val
                _logger.info('updating done work, ProcessingTask %d', int(taskid))
                task = session.query(DataProcessingTask).filter_by(id=taskid).one() 

                task.completion_time = datetime.utcnow()
                request = eval(task.request)
                results = {}

                if 'error' not in result:
                    task.state = FINISHED
                    
                    #cwd = os.getcwd()
                    os.chdir(os.path.abspath('results'))

                    # Update parent waiting state
                    _logger.debug('checking parent waiting state')
                    if task.parent is not None:
                        parent = task.parent
                        for child in parent.children:
                            if child.id == task.id:
                                # myself, ignoring
                                continue
                            if child.state != FINISHED:
                                break
                        else:
                            _logger.info('updating parent waiting state')
                            parent.waiting = False

                    # finding parent node
                    # FIXME: find a better way of doing this:
                    # Recover the instrument of the task
                    otask = task
                    while(otask.parent):
                        otask = otask.parent
    
                    ob = otask.obstree_node.observing_block
                    
                    iname = ob.obsrun.instrument_id

                    results['control'] = ['task-control.json']
                    results['log'] = ['processing.log']
                    results['products'] = result['products']
                    
                    task.result = str(results)
                    rr = ReductionResult()
                    rr.other = str(result)
                    rr.task_id = task.id
                    rr.obsres_id = task.obstree_node_id

                    # processing data products
                    for pr in result['products']:
                        prod = yaml.load(pr)
                
                        dp = DataProduct()
                        dp.instrument_id = iname
                        dp.datatype = '%s.%s' % (prod.__class__.__module__, prod.__class__.__name__)
                        # FIXME: this is specific for FITS files (classes that subclass Image)
                        dp.reference = prod.filename
                        dp.result = rr
                        dp.pset_name = request['pset']
                        
                        _logger.debug('extracting meta')
                        for key, val in prod.metadata():
                            _logger.debug('metadata is (%s, %s)', key, val)
                            # FIXME: probably there is a better way of doing this
                            q = session.query(ContextDescription).filter_by(instrument_id=dp.instrument_id, name=key).first()
                            v = session.query(ContextValue).filter_by(definition=q, value=val).first()

                            if v is None:
                                _logger.debug('creating metadata for %s', key)
                                v = ContextValue()
                                v.definition[q.together] = q
                                v.value = val
                                session.add(v)
                            
                            dp.context.append(v)

                        # copy or hardlink the file
                        _logger.debug('copying product in %s', productsdir)
                        # FIXME: no description
                        shutil.copy(prod.filename, productsdir)
                        # in 'products'
                        dp.task = task
                        session.add(dp)

                    session.add(rr)
                else:
                    results['error'] = result['error']
                    _logger.warning('error in task %d', task.id)
                    _logger.warning('error is %s', results['error']['type'])
                    _logger.warning('message is %s', results['error']['message'])
                    task.result = str(results)
                    task.state = ERROR

                session.commit()
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
                    kwds = {}
                    kwds['id'] = task.id
                    kwds['children'] = task.children
                    kwds['frames'] = task.obstree_node.frames
                    kwds['mode'] = task.obstree_node.observing_mode.key
                    kwds['request'] = eval(task.request)
                    
                    recipe = task.obstree_node.observing_mode.module
                    print recipe
                    # finding parent node
                    # FIXME: find a better way of doing this:
                    # Recover the instrument of the task
                    otask = task
                    while(otask.parent):
                        otask = otask.parent
                
                    if task.method == 'processPointing':
                        _logger.info('request is %(request)s', kwds)
    
                    ob = otask.obstree_node.observing_block
                    
                    kwds['instrument'] = ob.obsrun.instrument_id
                    kwds['ins_params'] = self.ins_config[ob.obsrun.instrument_id]
                    kwds['context'] = task.obstree_node.context

                    #fun = getattr(process, task.method)
                    
                    val = process_(session, task=task)
                    
                    #val = fun(session, **kwds)
                except Exception as ex:
                    task.completion_time = datetime.utcnow()
                    task.state = ERROR
                    _logger.warning('error creating root for task %d', taskid)
                    _logger.warning('error is %s', ex)
                    session.commit()
                    continue

                cid = self.find_client(session, task)
                if cid is not None:
                    _logger.info('processing taskid %d in host %s', taskid, cid)
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

    def pset_create(self, name, instrument):
        '''Create a new processing set'''

        _logger.info('create a processing set with name %s', name)
        session = Session()
        # check if instrument is valid
        ins = session.query(Instrument).filter_by(name=instrument).first()
        if ins is None:
            _logger.info('instrument %s does not exist', name)
            return

        # check if it exists
        pset = session.query(ProcessingSet).filter_by(name=name, instrument_id=instrument).first()
        if pset is not None:
            _logger.info('processing set with name %s already exists', name)
        else:
            pset = ProcessingSet()
            pset.name = name
            pset.instrument_id = instrument
            session.add(pset)
            session.commit()

    def run(self, obsid, pset='default'):
        '''Insert a new processing task tree in the database.'''

        _logger.info('create a new task tree for obsid %d', obsid)
        session = Session()

        obsblock = session.query(ObservingBlock).filter_by(id=obsid).first()
        if obsblock is not None:
            _logger.info('observing tasks tree')
        
            rtask = create_reduction_tree(session, 
                                          obsblock.observing_tree, None, 
                                        obsblock.obsrun.instrument_id, pset)
            _logger.info('new root processing task is %d', rtask.id)
            session.commit()
        else:
            _logger.warning('No observing block with id %d', obsid)
