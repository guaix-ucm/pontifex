#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

from datetime import datetime

from model import session
from model import ObsRun, ObsBlock, Images, Instruments
from model import RecipeParameters, ProcessingBlockQueue
from model import get_last_image_index

ins = session.query(Instruments).first()

obsrun = ObsRun()
obsrun.piData = 'spr1'
obsrun.status = 'FINISHED'
obsrun.end = datetime.utcnow()
session.add(obsrun)

oblock = ObsBlock()
oblock.instrument = ins
oblock.mode = 'bias'
obsrun.obsblocks.append(oblock)
session.add(oblock)

dd = get_last_image_index(session)

im = Images()
im.name = 'r0%02d.fits' % dd
dd += 1
im.exposure = 0.0
im.imgtype = 'BIAS'
im.obsblock = oblock
session.add(im)

im = Images()
im.name = 'r0%02d.fits' % dd
dd += 1
im.exposure = 0.0
im.imgtype = 'BIAS'
im.obsblock = oblock
session.add(im)
im = Images()
im.name = 'r0%02d.fits' % dd
dd += 1
im.exposure = 0.0
im.imgtype = 'BIAS'
im.obsblock = oblock
session.add(im)
im = Images()
im.name = 'r0%02d.fits' % dd
dd += 1
im.exposure = 0.0
im.imgtype = 'BIAS'
im.obsblock = oblock
session.add(im)
im = Images()
im.name = 'r0%02d.fits' % dd
dd += 1
im.exposure = 0.0
im.imgtype = 'BIAS'
im.obsblock = oblock

oblock.end = datetime.utcnow()
pbq = ProcessingBlockQueue()
pbq.obsblock = oblock
pbq.status = 'NEW'
session.add(pbq) 
session.commit()
session.add(im)

session.commit()
