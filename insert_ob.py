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
obsrun.instrument_id = 'emir'
obsrun.state = 'FINISHED'
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
otask = ObservingTask()
otask.state = 0
otask.creation_time = datetime.utcnow()
otask.label = 'mosaic-J-K'

session.add(otask)

otaskj = ObservingTask()
otaskj.state = 0
otaskj.creation_time = datetime.utcnow()
otaskj.parent = otask
otaskj.label = 'mosaic-J'
session.add(otaskj)

for i in range(1, 4):
    otaskp = ObservingTask()
    otaskp.state = 0
    otaskp.creation_time = datetime.utcnow()
    otaskp.parent = otaskj
    otaskp.label = 'pointing%d' %i
    session.add(otaskp)

otaskk = ObservingTask()
otaskk.state = 0
otaskk.creation_time = datetime.utcnow()
otaskk.parent_id = otask.id
otaskk.label = 'mosaic-K'
session.add(otaskk)

for i in range(1, 4):
    otaskp = ObservingTask()
    otaskp.state = 0
    otaskp.creation_time = datetime.utcnow()
    otaskp.parent = otaskk
    otaskp.label = 'pointing%d' %i
    session.add(otaskp)

dd = get_last_image_index(session)

def new_image(number, exposure, imgtype, oresult):
    im = Image()
    im.name = 'r0%02d.fits' % number
    im.exposure = exposure
    im.imgtype = imgtype
    im.observing_result = oresult
    return im

for (oj, ok) in zip(otaskj.children, otaskk.children):

    for i in range(1, 4):
        im = new_image(dd, 100, 'science', oj)
        dd += 1
        session.add(im)
        oj.state = 1
        oj.completion_time = datetime.utcnow()

    for i in range(1, 4):
        im = new_image(dd, 100, 'science', ok)
        dd += 1
        session.add(im)
        ok.state = 1
        ok.completion_time = datetime.utcnow()



otaskj.completion_time = datetime.utcnow()
otaskj.state = 1

otaskk.completion_time = datetime.utcnow()
otaskk.state = 1

oblock.completion_time = datetime.utcnow()

obsrun.completion_time = datetime.utcnow()
obsrun.state = 'FINISHED'

ptask = DataProcessingTask()
ptask.host = 'localhost'
ptask.state = 0
ptask.creation_time = datetime.utcnow()
ptask.method = 'process'
ptask.request = '{}'

session.add(ptask)

pctask = DataProcessingTask()
pctask.host = 'localhost'
pctask.parent = ptask
pctask.state = 0
pctask.creation_time = datetime.utcnow()
pctask.method = 'processPointing'
pctask.request = '{task=%s}' % otaskn.id

otask.start_time = datetime.utcnow()
otask.completion_time = datetime.utcnow()

#ptask.start_time = datetime.utcnow()
# task runs here
#pctask.start_time = datetime.utcnow()
# task runs here
#pctask.completion_time = datetime.utcnow()
#ptask.completion_time = datetime.utcnow()

session.commit()



