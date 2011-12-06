#!/usr/bin/python

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

#engine = create_engine('sqlite:///devdata.db', echo=False)
engine = create_engine('sqlite:///devdata.db', echo=True)
engine.execute('pragma foreign_keys=on')

model.init_model(engine)
model.metadata.create_all(engine)
session = model.Session()

ins = session.query(Instrument).filter_by(name='clodia').first()
user = session.query(Users).first()

context1 = session.query(ContextDescription).filter_by(instrument_id=ins.name, name='detector0.mode').first()

ccdmode = session.query(ContextValue).filter_by(definition=context1, value='normal').first()

obsrun = create_obsrun(user.id, ins.name)
session.add(obsrun)

# Observing block

# The layout of observing tasks can be arbitrary...

# Observing trees (siblings)
ores = ObservingTree()
ores.state = 0
ores.label = 'pointing'
ores.mode = 'bias'
ores.waiting = True
ores.awaited = False
ores.context.append(ccdmode)
session.add(ores)

oblock = create_observing_block('bias', user.id, obsrun)
oblock.observing_tree = ores
session.add(oblock)
session.commit()

# Create corresponding reduction tasks
ptask = create_reduction_task(oblock, ores)
ptask.waiting = False
ptask.obstree_node_id = ores.id
request = {'pset': 'default', 'instrument': ins.name}
ptask.request = str(request)
session.add(ptask)

# OB started
oblock.start_time = datetime.utcnow()

# OR started
ores.start_time = datetime.utcnow()
ores.state = 1
session.commit()

dd = get_last_image_index(session)

for i in range(3):
    im = new_image(dd, 0, 'bias', ores)
    dd += 1
    session.add(im)

# OR ended
ores.completion_time = datetime.utcnow()
ores.state = 2

ptask.instrument_id = ins.name
ptask.state = 1
session.commit()

# OB finished
oblock.state = 1
oblock.completion_time = datetime.utcnow()
session.commit()

# OR finished
obsrun.completion_time = datetime.utcnow()
obsrun.state = 'FINISHED'

session.commit()

