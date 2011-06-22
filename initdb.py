#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

from model import session
from model import RecipeParameters

r = RecipeParameters()
r.instrument = 'megara'
r.mode = 'bias'
r.parameters = {}
session.add(r)
session.commit()
