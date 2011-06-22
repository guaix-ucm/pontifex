#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import os

from model import session, datadir
from model import ObsBlock


# 
obid = 7
workdir = 'ff04c82288946d71e881ff42d02987e8'

if not os.path.exists(workdir):
    os.makedirs(workdir)

print 'processing OB', obid

result = session.query(ObsBlock).filter_by(obsId=obid).one()



os.chdir(workdir)

for im in result.images:
    print 'copy image', im.name, 'here'
    # fake copy
    f = open(im.name, 'w')
    f.close()

print 'instrument', result.instrument
print 'observing mode', result.mode

print 'recipe for instrument', result.instrument, 'and mode', result.mode, 'is'

