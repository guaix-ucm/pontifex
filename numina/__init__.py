#
# Copyright 2011 Sergio Pascual
# 
# This file is part of Numina
# 
# Numina is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Numina is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Numina.  If not, see <http://www.gnu.org/licenses/>.
#

# -*- coding: utf-8 -*-

import logging
import json

import pyfits

from numina.recipes import RecipeBase, Image

__version__ = '0.4.1'

class ReductionResult(object):
    def __init__(self):
        self.id = None
        self.reduction_block = None
        self.other = None
        self.status = 0
        self.picklable = {}

class ObservingResult(object):
    def __init__(self):
        self.id = None
        self.images = []

# FIXME: pyfits.core.HDUList is treated like a list
# each extension is stored separately
class FitsEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pyfits.core.PrimaryHDU):
            filename = 'result.fits'
            if obj.header.has_key('FILENAME'):
                filename = obj.header['FILENAME']
            obj.writeto(filename, clobber=True)
            return filename
        return json.JSONEncoder.default(self, obj)

class FITSHistoryHandler(logging.Handler):
    '''Logging handler using HISTORY FITS cards'''
    def __init__(self, header):
        logging.Handler.__init__(self)
        self.header = header

    def emit(self, record):
        msg = self.format(record)
        self.header.add_history(msg)




