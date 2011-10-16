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

from sqlalchemy import create_engine

from pontifex.model import Users, Instrument, Channel
from pontifex.model import ContextValue, ContextDescription
from pontifex.model import init_model, metadata, Session

#engine = create_engine('sqlite:///devdata.db', echo=False)
engine = create_engine('sqlite:///devdata.db', echo=True)
engine.execute('pragma foreign_keys=on')

init_model(engine)
metadata.create_all(engine)
session = Session()

user = Users()
user.name = 'auto'
user.status = 1
user.usertype = 1
session.add(user)

user = Users()
user.name = 'sergiopr'
user.status = 1
user.usertype = 1
session.add(user)

channel = Channel()
channel.name = 'default'
session.add(channel)

channel = Channel()
channel.name = 'fast'
session.add(channel)

ii = Instrument()
ii.name = 'megara'
ii.parameters = {}
session.add(ii)

ii = Instrument()
ii.name = 'emir'
ii.parameters = {
                 'name': 'emir',
                 'detectors': [[2048, 2048]],
		 'metadata' : {'imagetype': 'IMGTYP',
	                'airmass': 'AIRMASS',
        	        'exposure': 'EXPOSED',
                	'juliandate': 'MJD-OBS',
                	'detector.mode': 'CCDMODE',
                	'filter0': 'FILTER'
                	},
		'amplifiers' : [[
[(slice(1024, 2048, None), slice(896, 1024, None)),
 (slice(1024, 2048, None), slice(768, 896, None)),
 (slice(1024, 2048, None), slice(640, 768, None)),
 (slice(1024, 2048, None), slice(512, 640, None)),
 (slice(1024, 2048, None), slice(384, 512, None)),
 (slice(1024, 2048, None), slice(256, 384, None)),
 (slice(1024, 2048, None), slice(128, 256, None)),
 (slice(1024, 2048, None), slice(0, 128, None)),
 (slice(896, 1024, None), slice(0, 1024, None)),
 (slice(768, 896, None), slice(0, 1024, None)),
 (slice(640, 768, None), slice(0, 1024, None)),
 (slice(512, 640, None), slice(0, 1024, None)),
 (slice(384, 512, None), slice(0, 1024, None)),
 (slice(256, 384, None), slice(0, 1024, None)),
 (slice(128, 256, None), slice(0, 1024, None)),
 (slice(0, 128, None), slice(0, 1024, None)),
 (slice(0, 1024, None), slice(1024, 1152, None)),
 (slice(0, 1024, None), slice(1152, 1280, None)),
 (slice(0, 1024, None), slice(1280, 1408, None)),
 (slice(0, 1024, None), slice(1408, 1536, None)),
 (slice(0, 1024, None), slice(1536, 1664, None)),
 (slice(0, 1024, None), slice(1664, 1792, None)),
 (slice(0, 1024, None), slice(1792, 1920, None)),
 (slice(0, 1024, None), slice(1920, 2048, None)),
 (slice(1024, 1152, None), slice(1024, 2048, None)),
 (slice(1152, 1280, None), slice(1024, 2048, None)),
 (slice(1280, 1408, None), slice(1024, 2048, None)),
 (slice(1408, 1536, None), slice(1024, 2048, None)),
 (slice(1536, 1664, None), slice(1024, 2048, None)),
 (slice(1664, 1792, None), slice(1024, 2048, None)),
 (slice(1792, 1920, None), slice(1024, 2048, None)),
 (slice(1920, 2048, None), slice(1024, 2048, None))]
]]
                }
session.add(ii)

ii = Instrument()
ii.name = 'frida'
ii.parameters = {}
session.add(ii)

ii = Instrument()
ii.name = 'clodia'
ii.parameters = {
                 'name': 'clodia',
                 'detectors': [[256, 256]],
		 'metadata' : {'imagetype': 'IMGTYP',
	                'airmass': 'AIRMASS',
        	        'exposure': 'EXPOSED',
                	'juliandate': 'MJD-OBS',
                	'detector.mode': 'CCDMODE',
                	'filter0': 'FILTER'
                	},
		'amplifiers' : [[[(slice(0, 256), slice(0,256))]]],
                }
session.add(ii)

desc = ContextDescription()
desc.instrument_id = 'clodia'
desc.name = 'detector0.mode'
desc.description = 'Clodia detector readout mode'
session.add(desc)
session.commit()

for name in ['normal', 'slow', 'turbo']:
    vl = ContextValue()
    vl.definition = desc
    vl.value = name
    session.add(vl)

desc = ContextDescription()
desc.instrument_id = 'clodia'
desc.name = 'filter0'
desc.description = 'Clodia filter'
session.add(desc)
session.commit()

for name in ['310', '311', '312', '313', '314', '315']:
    vl = ContextValue()
    vl.definition = desc
    vl.value = name
    session.add(vl)

session.add(desc)

session.commit()
