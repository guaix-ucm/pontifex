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
ii.parameters = {}
session.add(ii)

ii = Instrument()
ii.name = 'frida'
ii.parameters = {}
session.add(ii)

ii = Instrument()
ii.name = 'clodia'
ii.parameters = {
                 'detectors': [[10, 10]],
                 'imagetype_key': 'IMGTYP',
                 'airmass_key': 'AIRMASS',
                 'exposure_key': 'EXPOSED',
                 'juliandate_key': 'MJD-OBS'
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
