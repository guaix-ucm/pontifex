#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

from datetime import datetime

from model import session
from model import ObsRun, ObsBlock, Images
from model import RecipeParameters

obsrun = ObsRun()
obsrun.piData = 'spr1'
obsrun.status = 'FINISHED'
obsrun.end = datetime.utcnow()
session.add(obsrun)

oblock = ObsBlock()
oblock.instrument = 'megara'
oblock.mode = 'bias'
oblock.obsrun = obsrun

r = RecipeParameters()
r.instrument = 'megara'
r.mode = 'bias'
r.parameters = {'param1': 1, 'param2': 'hola'}
session.add(r)
r = RecipeParameters()
r.instrument = 'megara'
r.mode = 'dark'
r.parameters = {'param1': 1, 'param2': 'hola'}
session.add(r)
r = RecipeParameters()
r.instrument = 'megara'
r.mode = 'flat'
r.parameters = {'param1': 1, 'param2': 'hola', 'param3': True}
session.add(r)

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
session.add(im)

session.commit()
