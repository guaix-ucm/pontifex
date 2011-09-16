#!/usr/bin/python

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
