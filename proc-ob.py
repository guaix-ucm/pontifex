#!/usr/bin/python

# Processing observation number=2, recipe=bias, instrument=megara

# Process obsblock id = 2

import sys
import logging
import logging.config
import importlib
from datetime import datetime

from sqlalchemy import create_engine

from numina import recipes
import model
import process
from model import datadir, ObservingBlock, ReductionResult, DataProcessingTask

logging.config.fileConfig("logging.ini")

# create logger
_logger = logging.getLogger("pontifex")

def myprint(i):
    print i.insId
    print i.mode
    for im in i.images:
        myprint2(im)

def myprint2(im):
    print im.name

def main(rb):
    return Tasks.process(rb.obsrun.instrument.name, rb.observing_mode, rb)


engine = create_engine('sqlite:///devdata.db', echo=False)
#engine = create_engine('sqlite:///devdata.db', echo=True)
engine.execute('pragma foreign_keys=on')

model.init_model(engine)
model.metadata.create_all(engine)
session = model.Session()



def print_leaves(node, pre=''):
    if node.children:
        for subnode in node.children:
            print_leaves(subnode, pre='|_')
    else:
        print pre, node.id, node.host, node.parent.id, node.label

def print_all(node, pre='', sp=0):
    front = '%s%s' % (sp * ' ', pre)
    print front, node.id, node.host, node.method, node.request, node.state
    for subnode in node.children:
        print_all(subnode, pre='|_', sp=sp+2)

def find_open_leave(node):
    if node.children:
        for subnode in node.children:
            if subnode.state == 1:
                return find_open_leave(subnode)
            else:
                return node
    else:
        if node.state == 1:
            return node
        else:
            return None

def fun(node):
    node.state = 1

def rec_set(node, fun):
    '''recursive setter'''
    fun(node)
    for c in node.children:
        rec_set(c, fun)
    return fun

while True:
    task = session.query(DataProcessingTask).filter_by(state=0).first()

    if task is None:
        break

    task.start_time = datetime.utcnow()
    task.state = 1
    fun = getattr(process, task.method)
    kwds = eval(task.request)
    # get images...
    # get children results
    for child in kwds['children']:
        _logger.info('query for result of ob id=%d', child)
        rr = session.query(ReductionResult).filter_by(obsres_id=child).first()
        if rr is not None:
            _logger.info('reduction result id is %d', rr.id)
    result = fun(**kwds)
    task.completion_time = datetime.utcnow()
    task.state = 2

    if result['base'] == 'ReductionResult':
        rr = ReductionResult()
        rr.other = str({'rootdir': result['rootdir']})
        rr.task_id = task.id
        session.add(rr)

    session.commit()

#if rb is not None:
#    rr = main(rb)
#
#    _logger.info('result stored in database')
#    session.add(rr)
#else:
#    _logger.info('no observing block')
    

