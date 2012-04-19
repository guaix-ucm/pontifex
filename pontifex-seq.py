#!/usr/bin/python

from datetime import datetime
import os.path
import sys
from StringIO import StringIO 
import json
import math
import logging.config

logging.config.fileConfig("logging.ini")

import yaml
from sqlalchemy import create_engine
import pyfits
from pyfits import Header
import numpy
from numina.treedict import TreeDict
# Import simulators
from numina.pipeline import init_pipeline_system
from numina.instrument import Sky, Lamp, ThermalBackground

import pontifex.model as model
from pontifex.model import datadir
from pontifex.model import ObservingRun, ObservingBlock, Frame, Instrument, Users
from pontifex.model import DataProcessingTask, ObservingTree, InstrumentConfiguration

from pontifex.model import ContextDescription, ContextValue
from pontifex.model import get_last_frame_index

from datetime import datetime

pipelines = init_pipeline_system()

import emir as emirmod
import megara as megaramod
simulators = {}

for key, mod in [('emir', emirmod), ('megara', megaramod)]:
    try:
        if 'Instrument' in mod.__all__ and 'ImageFactory' in mod.__all__:
            print key, 'provides simulator'
            simulators[key] = (mod.Instrument(), mod.ImageFactory())
    except AttributeError as err:
        print err, 'module is %s' % mod.__name__
        if key in simulators:
            del simulators[key]

print simulators
print 'done'

# Processing tasks STATES
CREATED, COMPLETED, ENQUEUED, PROCESSING, FINISHED, ERROR = range(6)

class Telescope(object):
    def __init__(self):
        self.meta = TreeDict()
        
        class NullSource(object):
            def emit(self):
                return 0.0
        
        self._illum = False
        
        self.lamp = Lamp(10000.0)
        self.thermal = ThermalBackground(1000.0)
        
        self.source = NullSource()
        
        
    def connect(self, source):
        self.source = source
        
    def emit(self):
        thermal = self.thermal.emit()
        if self._illum:
            return thermal + self.lamp.emit()
        return thermal + self.source.emit()
        
    def illum(self, on):
        self._illum = on
        
    def guide(self, on):
        pass

    def point_(self, ha, alt):
        pass

    def point(self, ra, dec):
        self.meta['pointing.airmass'] = 1.0
        self.meta['pointing.ra'] = ra
        self.meta['pointing.dec'] = dec

    def point_offset(self, deltara, deltadec):
        '''
        deltara and deltadec in arc-seconds
        '''
        self.meta['pointing.airmass'] = 1.0
        dec_rad = self.meta['pointing.dec'] / 180 * math.pi
        self.meta['pointing.ra'] += (deltara / 3600.0) / math.cos(dec_rad)
        self.meta['pointing.dec'] += (deltadec / 3600.0)
    

class Sequencer(object):
    def __init__(self, imgfact):
        self.session = model.Session()
        
        # Status is stored
        self.current_obs_run = None
        self.current_obs_block = None
        self.current_obs_tree_node = None

        self.meta = TreeDict()
        self.meta['control.name'] = 'NUMINA'
        self.meta['control.runid'] = lambda :get_last_frame_index(self.session)
        self.meta['control.date'] = lambda : datetime.now().isoformat()
        #self.meta['dateobs'] = lambda : datetime.now().isoformat()
        self.meta['proposal.id'] = 203
        self.meta['proposal.pi_id'] = 'sergiopr'
        self.meta['pointing.airmass'] = 1.0
        self.meta['pointing.ra'] = '10:01:04.000'
        self.meta['pointing.dec'] = '04:05:00.40'

        self.imgfact = imgfact
        self.components = []

    def connect(self, component):
        self.components.append(component)
    
    def add(self, image):

        name = 'megara'
        
        meta, data = image
        
        allmeta = self.meta
        allmeta[name] = meta

        for c in self.components:
            allmeta.update(c.meta)

        hdulist = self.imgfact[name].create(allmeta, data)
        
        im = Frame()
        im.name = 'r0%03d.fits' % self.meta['control.runid']()
        print 'add frame', im.name
        hdulist.writeto(os.path.join(datadir, im.name), clobber=True, checksum=True)
        # FIXME: extract this from the FITS header
        im.object = hdulist['primary'].header['object']
        im.exposure = hdulist['primary'].header['exposed']
        im.imgtype = hdulist['primary'].header['imagety']
        im.racoor = hdulist['primary'].header['ra']
        im.deccoor = hdulist['primary'].header['dec']
        im.observing_tree = self.current_obs_tree_node    
        
        self.session.add(im)

    def create_ob(self, mode, object):
        print 'create ob', mode
        
        # Observing Tree Node
        ores = ObservingTree()
        ores.state = 0
        ores.label = 'pointing'
        ores.mode = mode
        ores.waiting = True
        ores.awaited = False
        #ores.context.append(ccdmode)
        session.add(ores)
        
        print 'ot created'
        self.current_obs_tree_node = ores

        # Observing Block
        oblock = ObservingBlock()
        oblock.observing_mode = mode
        oblock.object = object
        oblock.observer = observer
        
        oblock.observing_tree = ores
        oblock.obsrun = self.current_obs_run

        self.meta['ob.object'] = object
        self.meta['ob.mode'] = mode
        # this field is Unicode
        self.meta['ob.observer'] = str(oblock.observer.name) 
                        
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
        insname = oblock.obsrun.instrument.name
        
        # Print file with ob
        
        frames = []
        ob = {'frames': frames, 'instrument': str(insname), 'mode': 
              str(oblock.observing_mode), 'id': oblock.id, 'children': []}
        
        
        for im in self.current_obs_tree_node.frames:
            frames.append([str(im.name), 
                           str(im.imgtype)
                           ])
        
        with open('ob-%d.json' % oblock.id, 'w') as fd:
            json.dump(ob, fd, indent=1)

        with open('ob-%d.yaml' % oblock.id, 'w') as fd:
            yaml.dump(ob, fd)
        
        ores = self.current_obs_tree_node
        # OR ended
        self.current_obs_tree_node.completion_time = datetime.utcnow()
        #ores.completion_time = datetime.utcnow()
        ores.state = 2

        
        # OB finished
        oblock.state = 1
        oblock.completion_time = datetime.utcnow()
        session.commit()
        
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
                create_reduction_tree(session, child, rtask, instrument, pset=pset)

            return rtask

        pset = 'default'        
        rtask = create_reduction_tree(self.session, oblock.observing_tree, None,
                                        oblock.obsrun.instrument_id, pset)
        print 'new root processing task is %d' % rtask.id
        self.session.commit()

        self.current_obs_tree_node = None
        self.current_obs_block = None
        
    def start_or(self, user, ins):
        
        def create_obsrun(userid, insname):
            obsrun = ObservingRun()
            obsrun.pi_id = userid
            obsrun.instrument_id = insname
            obsrun.state = 'RUNNING'
            obsrun.start_time = datetime.utcnow()
            return obsrun
                
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

loc = {}
img_factory = {}
glob = {}

telescope = Telescope()

for key, (instrument, factory) in simulators.iteritems():
    try:
        instrument.connect(telescope)
        glob[key] = instrument
        img_factory[key] = factory
    except AttributeError as error:
        print 'some error', error

print glob

sequencer = Sequencer(img_factory)
sequencer.connect(telescope)

glob['telescope'] = telescope
glob['sequencer'] = sequencer

ins = session.query(Instrument).filter_by(name='megara').first()
user = session.query(Users).first()
observer = session.query(Users).filter_by(name='Observer').first()
astronomer = session.query(Users).filter_by(name='Astronomer').first()

#context1 = session.query(ContextDescription).filter_by(instrument_id=ins.name, name='spec1.detector.mode').first()

#ccdmode = session.query(ContextValue).filter_by(definition=context1, value='normal').first()

sequencer.start_or(user, ins)

if not sys.argv[1:]:
    print 'Error, no sequence'
    sys.exit(1)

try:
    execfile(sys.argv[1], glob, loc)
except Exception:
    print 'Error in sequence'
    raise

sequencer.end_or()
