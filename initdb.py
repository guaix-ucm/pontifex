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

import model
from model import Users, Instrument

#engine = create_engine('sqlite:///devdata.db', echo=False)
engine = create_engine('sqlite:///devdata.db', echo=True)
engine.execute('pragma foreign_keys=on')

model.init_model(engine)
model.metadata.create_all(engine)
session = model.Session()

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

session.commit()
