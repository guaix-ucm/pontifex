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

'''Calibration Recipes for Clodia'''

import logging
import time

import numpy
import pyfits

from numina import RecipeBase

__all__ = ['BiasRecipe', 'DarkRecipe']

_logger = logging.getLogger('numina.recipes.clodia')

class BiasRecipe(RecipeBase):

    __author__ = "Sergio Pascual <sergiopr@fis.ucm.es>"
    __version__ = "0.1.0"
    __requires__ = []
    __provides__ = ['master_bias']

    def __init__(self, pp, cp):
        pass

    def run(self, rb):
    	_logger.info('starting bias reduction')

        # Mock result        
        data = numpy.zeros((10, 10), dtype='float32')

        hdu = pyfits.PrimaryHDU(data)
    
        # update hdu header with
        # reduction keywords
        hdr = hdu.header
        hdr.update('IMGTYP', 'BIAS', 'Image type')
        hdr.update('NUMTYP', 'MASTER_BIAS', 'Data product type')
        hdr.update('NUMXVER', __version__, 'Numina package version')
        hdr.update('NUMRNAM', 'BiasRecipe', 'Numina recipe name')
        hdr.update('NUMRVER', self.__version__, 'Numina recipe version')
        
        hdulist = pyfits.HDUList([hdu])

        _logger.info('bias reduction ended')
        return {'result': {'master_bias': hdulist, 'qa': 1}}

class DarkRecipe(RecipeBase):

    __author__ = "Sergio Pascual <sergiopr@fis.ucm.es>"
    __version__ = "0.1.0"
    __requires__ = ['master_bias']
    __provides__ = ['master_dark']

    def __init__(self, pp, cp):
        pass

    def run(self, rb):
        _logger.info('starting dark reduction')
        # Mock result        
        data = numpy.zeros((10, 10), dtype='float32')

        hdu = pyfits.PrimaryHDU(data)
    
        # update hdu header with
        # reduction keywords
        hdr = hdu.header
        hdr.update('IMGTYP', 'DARK', 'Image type')
        hdr.update('NUMTYP', 'MASTER_DARK', 'Data product type')
        hdr.update('NUMXVER', __version__, 'Numina package version')
        hdr.update('NUMRNAM', 'DarkRecipe', 'Numina recipe name')
        hdr.update('NUMRVER', self.__version__, 'Numina recipe version')
        
        hdulist = pyfits.HDUList([hdu])

        _logger.info('dark reduction ended')
        return {'result': {'master_dark': hdulist, 'qa': 1}}



