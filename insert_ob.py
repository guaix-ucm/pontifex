#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

from datetime import datetime

from sqlalchemy import create_engine

import model
from model import ObservingRun, ObservingBlock, Image, Instrument, Users
from model import ObservingTask, DataProcessingTask
from model import RecipeParameters, ProcessingBlockQueue
from model import get_last_image_index

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
obsrun.state = 'FINISHED'
obsrun.start_time = datetime.utcnow()
session.add(obsrun)

otask = ObservingTask()
otask.state = 0
otask.creation_time = datetime.utcnow()
otask.start_time = datetime.utcnow()
otask.completion_time = datetime.utcnow()
otask.label = 'Bias-padre'

ptask = DataProcessingTask()
ptask.host = 'localhost'
ptask.state = 0
ptask.creation_time = datetime.utcnow()
ptask.label = 'collect'

session.add(ptask)
session.add(otask)
session.commit()

otaskn = ObservingTask()
otaskn.state = 0
otaskn.creation_time = datetime.utcnow()
otaskn.start_time = datetime.utcnow()
otaskn.parent_id = otask.id
otaskn.label = 'Bias-hijo'
session.add(otaskn)
pctask = DataProcessingTask()
pctask.host = 'localhost'
pctask.parent = ptask
pctask.state = 0
pctask.creation_time = datetime.utcnow()
pctask.label = 'bias'

oblock = ObservingBlock()
oblock.observing_mode = 'bias'
oblock.observer_id = user.id
oblock.start_time = datetime.utcnow()
oblock.task_id = otask.id
obsrun.obsblocks.append(oblock)
session.add(oblock)

dd = get_last_image_index(session)

def new_image(number, exposure, imgtype, oblock):
    im = Image()
    im.name = 'r0%02d.fits' % number
    im.exposure = exposure
    im.imgtype = imgtype
    im.observing_block = oblock
    return im

for i in range(10):
    im = new_image(dd, 0.0, 'bias', oblock)
    dd += 1
    session.add(im)

otaskn.completion_time = datetime.utcnow()
otaskn.state = 1
otask.completion_time = datetime.utcnow()
otask.state = 1
oblock.completion_time = datetime.utcnow()

obsrun.completion_time = datetime.utcnow()
obsrun.state = 'FINISHED'

ptask.start_time = datetime.utcnow()
# task runs here
pctask.start_time = datetime.utcnow()
# task runs here
pctask.completion_time = datetime.utcnow()
ptask.completion_time = datetime.utcnow()

session.commit()
