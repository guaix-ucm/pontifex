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

from sqlalchemy import create_engine

from pontifex.model import Users, Instrument, Channel, InstrumentConfiguration
from pontifex.model import Recipe, RecipeConfiguration
from pontifex.model import ContextValue, ContextDescription, ProcessingSet
from pontifex.model import init_model, metadata, Session
from pontifex.model import ObservingMode

import os

try:
    os.remove('devdata.sqlite')
except OSError:
    pass

engine = create_engine('sqlite:///devdata.sqlite', echo=False)
#engine = create_engine('sqlite:///devdata.db', echo=True)
engine.execute('pragma foreign_keys=on')

init_model(engine)
metadata.create_all(engine)
session = Session()

from numina.core import init_drp_system
import numina.pipelines as namespace

drps = init_drp_system(namespace)

user = Users(name='auto', status=1, usertype=1)
session.add(user)

user = Users()
user.name = 'Observer'
user.status = 1
user.usertype = 1
session.add(user)

user = Users()
user.name = 'Astronomer'
user.status = 1
user.usertype = 1
session.add(user)

channel = Channel(name='default')
session.add(channel)

channel = Channel(name='fast')
session.add(channel)

fridaconf = {'name': 'FRIDA'}
miradasconf = {'name': 'MIRADAS'}

megaraconf = {
                 'name': 'MEGARA',
                 'detectors': [(2048, 2048)],
		 'metadata' : {'imagetype': 'IMGTYP',
	                'airmass': 'AIRMASS',
        	        'exposure': 'EXPOSED',
                	'juliandate': 'MJD-OBS',
                	'detector.mode': 'CCDMODE',
                	'filter0': 'FILTER'
                	},
		'channels' : [[((0, 2048), (0, 1024)),
		                 ((0, 2048), (1024, 2048))]]
                }

emirconf = {
                 'name': 'EMIR',
                 'detectors': [(2048, 2048)],
		 'metadata' : {'imagetype': 'IMGTYP',
	                'airmass': 'AIRMASS',
        	        'exposure': 'EXPOSED',
                	'juliandate': 'MJD-OBS',
                	'detector.mode': 'CCDMODE',
                	'filter0': 'FILTER'
                	},
		'channels': [
			[((1024, 2048), (896, 1024)), 
			((1024, 2048), (768, 896)), 
			((1024, 2048), (640, 768)), 
			((1024, 2048), (512, 640)), 
			((1024, 2048), (384, 512)), 
			((1024, 2048), (256, 384)), 
			((1024, 2048), (128, 256)), 
			((1024, 2048), (0, 128)), 
			((896, 1024), (0, 1024)), 
			((768, 896), (0, 1024)), 
			((640, 768), (0, 1024)), 
			((512, 640), (0, 1024)), 
			((384, 512), (0, 1024)), 
			((256, 384), (0, 1024)), 
			((128, 256), (0, 1024)), 
			((0, 128), (0, 1024)), 
			((0, 1024), (1024, 1152)), 
			((0, 1024), (1152, 1280)), 
			((0, 1024), (1280, 1408)), 
			((0, 1024), (1408, 1536)), 
			((0, 1024), (1536, 1664)), 
			((0, 1024), (1664, 1792)), 
			((0, 1024), (1792, 1920)), 
			((0, 1024), (1920, 2048)), 
			((1024, 1152), (1024, 2048)), 
			((1152, 1280), (1024, 2048)), 
			((1280, 1408), (1024, 2048)), 
			((1408, 1536), (1024, 2048)), 
			((1536, 1664), (1024, 2048)), 
			((1664, 1792), (1024, 2048)), 
			((1792, 1920), (1024, 2048)), 
			((1920, 2048), (1024, 2048))]
			],
                }


insconf = {'EMIR':emirconf, 'FRIDA':fridaconf,
            'MEGARA': megaraconf, 'MIRADAS': miradasconf}

# FIXME, just for a fake recipe name
i = 0
for key in drps:
    thisins = drps[key]
    ii = Instrument(name=key)
    session.add(ii)

    ic = InstrumentConfiguration(instrument=ii, parameters=insconf[key], 
                    description='Default', active=True)
    session.add(ic)

    pset_d = ProcessingSet(instrument=ii, name='default')
    session.add(pset_d)
    pset_t = ProcessingSet(instrument=ii, name='test')
    session.add(pset_t)

    for mode in thisins.modes:
        i += 1
        om = ObservingMode(name=mode.name, key=mode.key, 
            instrument=ii)
        session.add(om)
        rr = Recipe(module='dum%s' % i)
        session.add(rr)

        b = RecipeConfiguration(parameters={},
                                description='Description', processing_set=pset_d)

        session.add(b)

desc = ContextDescription(instrument_id='MEGARA',
                        name='spec1.detector.mode',
                        description='Megara detector readout mode')
session.add(desc)

for name in ['normal', 'slow', 'turbo']:
    vl = ContextValue(definition=desc, value=name)
    session.add(vl)

desc = ContextDescription(instrument_id='MEGARA',
                        name='spec1.grism',
                        description='Megara grism')
session.add(desc)

for name in ['A', 'B', 'C', 'D', 'E', 'F']:
    vl = ContextValue(definition=desc, value=name)
    session.add(vl)

session.add(desc)

session.commit()
