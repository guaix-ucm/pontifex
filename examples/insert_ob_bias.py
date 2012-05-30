#!/usr/bin/python

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
from pontifex.model import ObservingRun, ObservingBlock, Frame, Instrument, Users, ObservingMode
from pontifex.model import DataProcessingTask, ObservingTree, InstrumentConfiguration

from pontifex.model import ContextDescription, ContextValue
from pontifex.model import get_last_frame_index
from pontifex.model import create_fits_keyword 

def new_image(session, number, exposure, imgtype, oresult):
    im = Frame()
    im.name = 'r0%03d.fits' % number
    im.object = 'TEST'
    im.racoor = 1
    im.deccoor = 1
    data = numpy.zeros((1,1), dtype='int16')
    hdu = pyfits.PrimaryHDU(data)
    hdu.header.update('ccdmode', 'normal')
    hdu.header.update('imgtype', 'BIAS')
    hdu.header.update('obsmode', 'BIAS')
    hdu.header.update('instrume', 'EMIR')
    hdu.writeto(os.path.join(datadir, im.name), clobber=True)

    # keywords
    for i in hdu.header:
        key = i
        value = hdu.header[i]
        k = create_fits_keyword(im, key, value)
        session.add(k)

    im.exposure = exposure
    im.imgtype = imgtype
    im.observing_tree = oresult    
    return im

def create_reduction_task(oblock, oresult):
    ptask = DataProcessingTask(state=0)
    ptask.observing_result = oresult
    ptask.method = 'process%s' % oresult.label.capitalize()
    return ptask

def create_reduction_tree(oresult, parent):

    ptask = DataProcessingTask(state=0)
    ptask.host = 'localhost'
    ptask.parent = parent
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

engine = create_engine('sqlite:///devdata.sqlite', echo=False)
#engine = create_engine('sqlite:///devdata.db', echo=True)
engine.execute('pragma foreign_keys=on')

model.init_model(engine)
model.metadata.create_all(engine)
session = model.Session()

ins = session.query(Instrument).filter_by(name='EMIR').first()
if ins is None:
    print 'mal'
    raise RuntimeError
user = session.query(Users).first()

#context1 = session.query(ContextDescription).filter_by(instrument_id=ins.name, name='detector0.mode').first()

#ccdmode = session.query(ContextValue).filter_by(definition=context1, value='normal').first()

obsrun = ObservingRun(instrument=ins, pi=user)
session.add(obsrun)

# Observing block

# The layout of observing tasks can be arbitrary...
obsmode = session.query(ObservingMode).filter_by(instrument=ins, key='bias_image').first()

# Observing trees (siblings)
ores = ObservingTree(state=0, label='pointing',
                    waiting=True, awaited=False,
                    observing_mode=obsmode)
#ores.context.append(ccdmode)
session.add(ores)

oblock = ObservingBlock(observing_mode=obsmode, 
                        object='TEST', observer=user, 
                        observing_tree=ores, obsrun=obsrun)
session.add(oblock)
#session.commit()

# Create corresponding reduction tasks
ptask = create_reduction_task(oblock, ores)
ptask.waiting = False
ptask.obstree_node = ores
request = {'pset': 'default', 'instrument': ins.name}
ptask.request = str(request)
session.add(ptask)

# OB started
oblock.start_time = datetime.utcnow()

# OR started
ores.start_time = datetime.utcnow()
ores.state = 1
session.commit()

dd = get_last_frame_index(session)

for i in range(3):
    im = new_image(session, dd, 0, 'bias', ores)
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

# OR finished
obsrun.completion_time = datetime.utcnow()
obsrun.state = 'FINISHED'

session.commit()

