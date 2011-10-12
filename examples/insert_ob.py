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
# PyEmir is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with PyEmir.  If not, see <http://www.gnu.org/licenses/>.
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
from pontifex.model import DataProcessingTask, ObservingResult
from pontifex.model import RecipeParameters, ProcessingBlockQueue
from pontifex.model import get_last_image_index

def new_image(number, exposure, imgtype, oresult):
    im = Image()
    im.name = 'r0%02d.fits' % number
    data = numpy.zeros((1,1), dtype='int16')
    pyfits.writeto(os.path.join(datadir, im.name), data, clobber=True)
    im.exposure = exposure
    im.imgtype = imgtype
    im.obsresult_id = oresult.id
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

obsrun = create_obsrun(user.id, ins.name)
session.add(obsrun)

# New Observing block
oblock = create_observing_block('mosaic', user.id, obsrun)
session.add(oblock)

# Observing tasks (siblings)
otask = ObservingResult()
otask.state = 0
otask.label = 'collect'
otask.instrument_id = ins.name
otask.mode = 'null'
session.add(otask)

# The result of this ob
oblock.task = otask
root_a_task = create_reduction_task(oblock, otask)
root_a_task.waiting = True
session.add(root_a_task)
session.commit()

# One mosaic
otaskj = ObservingResult()
otaskj.state = 0
otaskj.creation_time = datetime.utcnow()
otaskj.parent = otask
otaskj.label = 'mosaic'
otaskj.mode = 'mosaic_image'
otaskj.instrument_id = ins.name

root_p_task = create_reduction_task(oblock, otaskj)
root_p_task.parent = root_a_task
root_p_task.waiting = True
session.add(root_p_task)
session.add(otaskj)
session.commit()

dd = get_last_image_index(session)

for j in range(3):

    # One pointing
    otaskp = ObservingResult()
    otaskp.state = 0
    otaskp.creation_time = datetime.utcnow()
    otaskp.parent = otaskj
    otaskp.label = 'pointing'
    otaskp.mode = 'direct_image'
    otaskp.instrument_id = ins.name
    session.add(otaskp)
    session.commit()

    # OB started
    oblock.start_time = datetime.utcnow()
    # OR started
    otaskp.start_time = datetime.utcnow()
    otaskp.state = 1

    for i in range(3):
        im = new_image(dd, 100, 'science', otaskp)
        dd += 1
        session.add(im)

    # OR ended
    otaskp.state = 2
    otaskp.completion_time = datetime.utcnow()
#    session.commit()
    
    # Create a reduction task, otaskp is complete
    ptask = create_reduction_task(oblock, otaskp)
    ptask.state = 1 # Complete
    ptask.parent = root_p_task
    ptask.waiting = False
    session.add(ptask)
    session.commit()

otaskj.completion_time = datetime.utcnow()
otaskj.state = 2

# Create a reduction task, otaskj is complete

root_p_task.state = 1 # Complete

otask.completion_time = datetime.utcnow()
otask.state = 2

root_a_task.state = 1 # Complete

# OB finished
oblock.completion_time = datetime.utcnow()

# OR finished
obsrun.completion_time = datetime.utcnow()
obsrun.state = 'FINISHED'

session.commit()

