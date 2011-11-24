#!/usr/bin/python

from datetime import datetime
import os.path
import sys
from StringIO import StringIO 

from sqlalchemy import create_engine
import pyfits
from pyfits import Header
import numpy
from numina.treedict import TreeDict

import pontifex.model as model
from pontifex.model import datadir
from pontifex.model import ObservingRun, ObservingBlock, Image, Instrument, Users
from pontifex.model import DataProcessingTask, ObservingTree, InstrumentConfiguration

from pontifex.model import ContextDescription, ContextValue
from pontifex.model import get_last_image_index

from datetime import datetime

from megara.simulator import Megara, MegaraImageFactory

# Processing tasks STATES
CREATED, COMPLETED, ENQUEUED, PROCESSING, FINISHED, ERROR = range(6)

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

def create_observing_block(mode, parent):
    oblock = ObservingBlock()
    oblock.observing_mode = mode
    oblock.observer = observer
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
    def __init__(self):
        self.meta = TreeDict()

    def guide(self, on):
        pass

    def point_(self, ha, alt):
        pass

    def point(self, ra, dec):
        self.meta['pointing.airmass'] = 1.0
        self.meta['pointing.ra'] = ra
        self.meta['pointing.dec'] = dec


class Sequencer(object):
    def __init__(self):
        self.session = model.Session()
        
        # Status is stored
        self.current_obs_run = None
        self.current_obs_block = None
        self.current_obs_tree_node = None

        self.meta = TreeDict()
        self.meta['control.name'] = 'NUMINA'
        self.meta['control.runid'] = lambda :get_last_image_index(self.session)
        self.meta['control.date'] = lambda : datetime.now().isoformat()
        self.meta['proposal.id'] = 203
        self.meta['proposal.pi_id'] = 'sergiopr'
        self.meta['pointing.airmass'] = 1.0
        self.meta['pointing.ra'] = '10:01:04.000'
        self.meta['pointing.dec'] = '04:05:00.40'

        self.image_factory = MegaraImageFactory()
        self.components = []

    def connect(self, component):
        self.components.append(component)
    
    def add(self, image):
        
        meta, data = image
        
        allmeta = self.meta
        allmeta['megara'] = meta

        for c in self.components:
            allmeta.update(c.meta)

        hdulist = self.image_factory.create(allmeta, data)
        
        im = Image()
        im.name = 'r0%03d.fits' % self.meta['control.runid']()
        print 'add image', im.name
        hdulist.writeto(os.path.join(datadir, im.name), clobber=True, checksum=True)

        im.exposure = allmeta['megara.detector.exposed']
        im.imgtype = allmeta['megara.imagetype']
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
        ores.context.append(ccdmode)
        session.add(ores)
        
        print 'ob created'
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

megara = Megara()

sequencer = Sequencer()
sequencer.connect(telescope)

loc = {}
glob = {'telescope': telescope, 
        'megara': megara, 
        'sequencer': sequencer}

ins = session.query(Instrument).filter_by(name='megara').first()
user = session.query(Users).first()
observer = session.query(Users).filter_by(name='Observer').first()
astronomer = session.query(Users).filter_by(name='Astronomer').first()

context1 = session.query(ContextDescription).filter_by(instrument_id=ins.name, name='spec1.detector.mode').first()

ccdmode = session.query(ContextValue).filter_by(definition=context1, value='normal').first()

sequencer.start_or(user, ins)

if not sys.argv[1:]:
    print 'Error, no sequence'
    sys.exit(1)

try:
    execfile(sys.argv[1], glob, loc)
except Exception:
    print 'Error in sequence'
    raise



#ptask.instrument_id = ins.name
#ptask.state = 1
#session.commit()

# OR finished

sequencer.end_or()

