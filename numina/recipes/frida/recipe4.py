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

import logging
import time

__all__ = ['run']

_logger = logging.getLogger('numina.recipes.frida')

def run(rb, pp, cp):
    return None

class Recipe:
    def __init__(self, pp, cp):
        pass

    @classmethod
    def requires(cls):
        return []

    def run(self, rb):
    	_logger.info('starting direct imaging reduction')
        _logger.info('basic processing')
        _logger.info('resizing images and masks')
        _logger.info('superflat correction')
        _logger.info('simple sky correction')
        _logger.info('stacking science images')
    	time.sleep(5)
    	_logger.info('direct imaging reduction ended')
        return {'result': {'direct_image': 0, 'qa': 1}}

