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
from model import datadir, ObservingBlock, ReductionResult, DataProcessingTask

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("demo")


class Tasks(object):
    @staticmethod
    def process(instrument, mode, rb):
        _logger.info('Creating Reduction Result')
        rr = ReductionResult()
        rr.other = 'Other info'
        rr.picklable = {}
        try:
            recipe_name = recipes.find_recipe(instrument, mode)
            _logger.info('recipe name is %s', recipe_name)
    
            # Find precomputed parameters for this recipe
            _logger.info('loading precomputed parameters')
            pp = recipes.find_parameters(recipe_name)
    
            module = importlib.import_module(recipe_name)
            _logger.info('loading requeriments from system')
            cp = {}
            
            for name, value in module.Recipe.requires():
                cp[name] = value        
    
            _logger.info('creating recipe')
            recipe = module.Recipe(pp, cp)
            _logger.info('running recipe')
            result = recipe.run(rb)
    
        except ValueError as msg:
            _logger.error('Something has happened: %s', str(msg))
            rr.state = 1
        else:
            _logger.info('recipe finished')
            rr.state = 0

        return rr

    @staticmethod
    def processPointing():
        print 'processPointing'
        return 0

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

rb  = session.query(ObservingBlock).filter_by(id=2).first()

dbtasklist = session.query(DataProcessingTask).filter_by(parent=None)

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

parents = session.query(DataProcessingTask).filter_by(parent=None, state=0)

def fun(node):
    node.state = 1

def rec_set(node, fun):
    '''recursive setter'''
    fun(node)
    for c in node.children:
        rec_set(c, fun)
    return fun

tasks = []

for dpt in parents:
    rec_set(dpt, fun)
    print_all(dpt)
    r = find_open_leave(dpt)
    r.state = 2 # assigned to be processed
    tasks.append(r)
    print_all(r)

for task in tasks:
    # run task
    fun = getattr(Tasks, task.method)
    val = fun()
    task.state = 3 # Finished
    task.completed_time = datetime.utcnow()

    # Find next child of parent
    # if not, parent itself


#if rb is not None:
#    rr = main(rb)
#
#    _logger.info('result stored in database')
#    session.add(rr)
#else:
#    _logger.info('no observing block')
#    session.commit()

