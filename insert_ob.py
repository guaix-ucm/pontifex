#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

from datetime import datetime

from sqlalchemy import create_engine

import model
from model import ObservingRun, ObservingBlock, Image, Instrument, Users
from model import DataProcessingTask, ObservingResult
from model import RecipeParameters, ProcessingBlockQueue
from model import get_last_image_index

def new_image(number, exposure, imgtype, oresult):
    im = Image()
    im.name = 'r0%02d.fits' % number
    im.exposure = exposure
    im.imgtype = imgtype
    im.obsresult_id = oresult.id
    return im

#engine = create_engine('sqlite:///devdata.db', echo=False)
engine = create_engine('sqlite:///devdata.db', echo=True)
engine.execute('pragma foreign_keys=on')

model.init_model(engine)
model.metadata.create_all(engine)
session = model.Session()

ins = session.query(Instrument).first()
user = session.query(Users).first()

obsrun = ObservingRun()
obsrun.pi_id = user.id
obsrun.instrument_id = ins.name
obsrun.state = 'RUNNING'
obsrun.start_time = datetime.utcnow()
session.add(obsrun)

# Observing block
oblock = ObservingBlock()
oblock.observing_mode = 'mosaic'
oblock.observer_id = user.id
oblock.start_time = datetime.utcnow()
#oblock.task_id = otask.id
obsrun.obsblocks.append(oblock)
session.add(oblock)

# Observing tasks
otask = ObservingResult()
otask.state = 0
otask.creation_time = datetime.utcnow()
otask.label = 'collect'

session.add(otask)

# The result of this ob
oblock.task = otask

# One mosaic
otaskj = ObservingResult()
otaskj.state = 0
otaskj.creation_time = datetime.utcnow()
otaskj.parent = otask
otaskj.label = 'mosaic'
session.add(otaskj)

dd = get_last_image_index(session)

for j in range(3):

    # One pointing
    otaskp = ObservingResult()
    otaskp.state = 0
    otaskp.creation_time = datetime.utcnow()
    otaskp.parent = otaskj
    otaskp.label = 'pointing'
    session.add(otaskp)
    session.commit()

    for i in range(3):
        im = new_image(dd, 100, 'science', otaskp)
        dd += 1
        session.add(im)

    otaskp.state = 1
    otaskp.completion_time = datetime.utcnow()

    ptask = DataProcessingTask()
    ptask.host = 'localhost'
    ptask.state = 0
    ptask.creation_time = datetime.utcnow()
    ptask.method = 'processPointing'
    request = {'id': otaskp.id,
                'images': [image.name for image in otaskp.images],
                'children': [],
                'instrument': ins.name,
                'observing_mode': oblock.observing_mode,
              }
    ptask.request = str(request)
    session.add(ptask)

# Create a reduction task, otaskp is complete

otaskj.completion_time = datetime.utcnow()
otaskj.state = 1

# Create a reduction task, otaskj is complete

ptask = DataProcessingTask()
ptask.host = 'localhost'
ptask.state = 0
ptask.creation_time = datetime.utcnow()
ptask.method = 'processMosaic'
request = {'id': otaskj.id,
    'children': [child.id for child in otaskj.children],
    'images': [],
                'instrument': ins.name,
                'observing_mode': oblock.observing_mode,
              }
ptask.request = str(request)
session.add(ptask)

otask.completion_time = datetime.utcnow()
otask.state = 1

# Create a reduction task, otask is complete

ptask = DataProcessingTask()
ptask.host = 'localhost'
ptask.state = 0
ptask.creation_time = datetime.utcnow()
ptask.method = 'processCollect'
ptask.request = str({ 'id':otask.id,
    'children': [child.id for child in otask.children],
    'images': [],
    'observing_mode': oblock.observing_mode,
    'instrument': ins.name})
session.add(ptask)

# OB finished
oblock.completion_time = datetime.utcnow()

# OR finished
obsrun.completion_time = datetime.utcnow()
obsrun.state = 'FINISHED'

session.commit()

