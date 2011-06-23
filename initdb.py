#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

from datetime import datetime

from model import session
from model import ObsRun, ObsBlock, Images, Instruments
from model import RecipeParameters, ProcessingBlockQueue

ii = Instruments()
ii.name = 'megara'
ii.parameters = {}
session.add(ii)

r = RecipeParameters()
r.instrument = ii
r.mode = 'bias'
r.parameters = {'param1': 1, 'param2': 'hola'}
session.add(r)

r = RecipeParameters()
r.instrument = ii
r.mode = 'dark'
r.parameters = {'param1': 1, 'param2': 'hola'}
session.add(r)

r = RecipeParameters()
r.instrument = ii
r.mode = 'flat'
r.parameters = {'param1': 1, 'param2': 'hola', 'param3': True}
session.add(r)

obsrun = ObsRun()
obsrun.piData = 'spr1'
obsrun.status = 'FINISHED'
obsrun.end = datetime.utcnow()
session.add(obsrun)

oblock = ObsBlock()
oblock.instrument = ii
oblock.mode = 'bias'
obsrun.obsblocks.append(oblock)
session.add(oblock)

im = Images()
im.name = 'r001.fits'
im.exposure = 0.0
im.imgtype = 'BIAS'
im.obsblock = oblock
session.add(im)

im = Images()
im.name = 'r002.fits'
im.exposure = 0.0
im.imgtype = 'BIAS'
im.obsblock = oblock
session.add(im)
im = Images()
im.name = 'r003.fits'
im.exposure = 0.0
im.imgtype = 'BIAS'
im.obsblock = oblock
session.add(im)
im = Images()
im.name = 'r004.fits'
im.exposure = 0.0
im.imgtype = 'BIAS'
im.obsblock = oblock
session.add(im)
im = Images()
im.name = 'r005.fits'
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
