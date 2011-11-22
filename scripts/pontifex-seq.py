#!/usr/bin/python

from datetime import datetime
import os.path
import sys

from sqlalchemy import create_engine
import pyfits
import numpy

import pontifex.model as model
from pontifex.model import datadir
from pontifex.model import ObservingRun, ObservingBlock, Image, Instrument, Users
from pontifex.model import DataProcessingTask, ObservingTree, InstrumentConfiguration

from pontifex.model import ContextDescription, ContextValue
from pontifex.model import get_last_image_index

def new_image(number, exposure, imgtype, oresult):
    im = Image()
    im.name = 'r0%03d.fits' % number
    data = numpy.zeros((1,1), dtype='int16')
    hdu = pyfits.PrimaryHDU(data)
    hdu.header.update('ccdmode', 'normal')
    hdu.header.update('filter', 311)
    hdu.writeto(os.path.join(datadir, im.name), clobber=True)

    im.exposure = exposure
    im.imgtype = imgtype
    im.observing_tree = oresult    
    return im

def create_obsrun(userid, insname):
    obsrun = ObservingRun()
    obsrun.pi_id = userid
    obsrun.instrument_id = insname
    obsrun.state = 'RUNNING'
    obsrun.start_time = datetime.utcnow()
    return obsrun

def create_observing_block(mode, observer, parent):
    oblock = ObservingBlock()
    oblock.observing_mode = mode
    oblock.observer_id = observer
    parent.obsblocks.append(oblock)
    return oblock

def create_reduction_task(oblock, oresult):
    ptask = DataProcessingTask()
    ptask.observing_result = oresult
    ptask.state = 0
    ptask.method = 'process%s' % oresult.label.capitalize()
    return ptask

def create_reduction_tree(oresult, parent):

    ptask = DataProcessingTask()
    ptask.host = 'localhost'
    ptask.state = 0
    ptask.parent = parent
    ptask.creation_time = datetime.utcnow()
    ptask.method = 'process%S' % oresult.label
#    request = {'id': otaskp.id,
#                'images': [image.name for image in otaskp.images],
#                'children': [],
#                'instrument': ins.name,
#                'observing_mode': oblock.observing_mode,
#              }
#    ptask.request = str(request)
    for child in oresult.children:
        create_reduction_tree(child, ptask)
    return ptask

class Telescope(object):
    def guide(self, on):
        pass

    def point_(self, ha, alt):
        pass

class Clodia(object):
    def filter(self, name):
        pass

    class Shutter:
        def close(self):
            pass

    shutter = Shutter()

    class Detector:
        def mode(self, name):
            pass

    detector = Detector()

    def expose(self, time):
        pass

    def readout(self):
        data = numpy.zeros((1,1), dtype='int16')
        hdu = pyfits.PrimaryHDU(data)
        hdu.header.update('ccdmode', 'normal')
        hdu.header.update('filter', 311)
        
        # collect metadata
        
        meta = {'ccdmode': 'normal', 'filter': 311}
                
        return meta, data

class Sequencer(object):
    def __init__(self):
        self.session = model.Session()
        
        self.imagenum = get_last_image_index(self.session)
        
        # Status is stored
        self.current_obs_run = None
        self.current_obs_block = None
        self.current_obs_tree_node = None
    
    def add(self, image):
        
        meta, data = image
        
        # collect metadata
        hdu = pyfits.PrimaryHDU(data)
        for key, val in meta.items():
            hdu.header.update(key, val)
            hdu.header.update(key, val)
        
        
        
        im = Image()
        im.name = 'r0%03d.fits' % self.imagenum
        print 'add image', im.name
        #hdu.writeto(os.path.join(datadir, im.name), clobber=True)

        im.exposure = 0 #exposure
        im.imgtype = '' # imgtype
        im.observing_tree = self.current_obs_tree_node    
        
        self.session.add(im)
        self.imagenum += 1

    def create_ob(self, mode):
        print 'create ob', mode
        
        # Observing Tree Node
        ores = ObservingTree()
        ores.state = 0
        ores.label = 'pointing'
        ores.mode = mode
        ores.waiting = True
        ores.awaited = False
        ores.context.append(ccdmode)
        session.add(ores)
        
        print 'ot created'
        self.current_obs_tree_node = ores

        # Observing Block
        oblock = ObservingBlock()
        oblock.observing_mode = mode
        oblock.observer_id = user.id
        
        oblock.observing_tree = ores
        
        oblock.obsrun = self.current_obs_run
                        
        self.session.add(oblock)
        
        self.session.commit()        
        self.current_obs_block = oblock
        return oblock.id

    def start_ob(self):
        
        oblock = self.current_obs_block
        print 'start ob', oblock.observing_mode
        # OB finished
        
        oblock.start_time = datetime.utcnow()
        session.commit()

    def end_ob(self):
        oblock = self.current_obs_block
        
        print 'end ob', oblock.observing_mode
        
        ores = self.current_obs_tree_node
        # OR ended
        self.current_obs_tree_node.completion_time = datetime.utcnow()
        #ores.completion_time = datetime.utcnow()
        ores.state = 2

        
        # OB finished
        oblock.state = 1
        oblock.completion_time = datetime.utcnow()
        session.commit()
        
        self.current_obs_tree_node = None
        self.current_obs_block = None
        
        
    def start_or(self, user, ins):
        self.current_obs_run = create_obsrun(user.id, ins.name)
        self.session.add(self.current_obs_run)
        self.session.commit()

    def end_or(self):
        # OR finished
        obsrun = self.current_obs_run
        if obsrun is not None:
            obsrun.completion_time = datetime.utcnow()
            obsrun.state = 'FINISHED'
            self.session.commit()
            obsrun = None


engine = create_engine('sqlite:///devdata.db', echo=False)
engine.execute('pragma foreign_keys=on')


model.init_model(engine)
model.metadata.create_all(engine)
session = model.Session()

telescope = Telescope()

clodia = Clodia()

sequencer = Sequencer()

loc = {}
glob = {'telescope': telescope, 
        'clodia': clodia, 
        'sequencer': sequencer}

ins = session.query(Instrument).filter_by(name='clodia').first()
user = session.query(Users).first()

context1 = session.query(ContextDescription).filter_by(instrument_id=ins.name, name='detector0.mode').first()

ccdmode = session.query(ContextValue).filter_by(definition=context1, value='normal').first()


sequencer.start_or(user, ins)

try:
    execfile('sequence.txt', glob, loc)
except Exception:
    print 'Error in sequence'
    raise



#ptask.instrument_id = ins.name
#ptask.state = 1
#session.commit()

# OR finished

sequencer.end_or()

