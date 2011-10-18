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

'''Science Recipes for Clodia'''

import logging

import numpy
import pyfits
from numina import RecipeBase, __version__

from clodia.products import MasterBias, MasterDark, MasterFlat, PointingImage

__all__ = ['DirectImage']

__author__ = "Sergio Pascual <sergiopr@fis.ucm.es>"

_logger = logging.getLogger('clodia.recipes')

class DirectImage(RecipeBase):

    __requires__ = [MasterBias, MasterDark, MasterFlat]
    __provides__ = [PointingImage]

    def __init__(self):
        super(DirectImage, self).__init__(author=__author__, version="0.1.0")

    def run(self, block):
    	_logger.info('starting direct image mode')

        # Mock result        
        data = numpy.zeros((10, 10), dtype='float32')

        hdu = pyfits.PrimaryHDU(data)
    
        # update hdu header with
        # reduction keywords
        hdr = hdu.header
        hdr.update('FILENAME', 'science-%(block_id)d.fits' % self.environ)
        hdr.update('IMGTYP', 'SCIENCE', 'Image type')
        hdr.update('NUMTYP', 'SCIENCE', 'Data product type')
        hdr.update('NUMXVER', __version__, 'Numina package version')
        hdr.update('NUMRNAM', 'DirectImage', 'Numina recipe name')
        hdr.update('NUMRVER', self.__version__, 'Numina recipe version')
        hdr.update('ccdmode', 'normal')
        hdr.update('filter', 315)
        
        hdulist = pyfits.HDUList([hdu])

        _logger.info('direct image reduction ended')
        return {'products': [PointingImage(hdulist)]}

class MosaicImage(RecipeBase):

    __requires__ = []
    __provides__ = [Image('mosaic')]

    def __init__(self):
        super(MosaicImage, self).__init__(author=__author__, version="0.1.0")

    def run(self, block):
    	_logger.info('starting mosaic mode')

        # Mock result        
        data = numpy.zeros((10, 10), dtype='float32')

        hdu = pyfits.PrimaryHDU(data)
    
        # update hdu header with
        # reduction keywords
        hdr = hdu.header
        hdr.update('FILENAME', 'mosaic-%(block_id)d.fits' % self.environ)
        hdr.update('IMGTYP', 'SCIENCE', 'Image type')
        hdr.update('NUMTYP', 'MOSAIC', 'Data product type')
        hdr.update('NUMXVER', __version__, 'Numina package version')
        hdr.update('NUMRNAM', 'MosaicImage', 'Numina recipe name')
        hdr.update('NUMRVER', self.__version__, 'Numina recipe version')
        hdr.update('ccdmode', 'normal')
        hdr.update('filter', 315)

        hdulist = pyfits.HDUList([hdu])

        _logger.info('mosaic reduction ended')
        return {'products': [Mosaic(hdulist)]}


class Null(RecipeBase):
    __requires__ = []
    __provides__ = []

    def __init__(self):
        super(Null, self).__init__(author=__author__, version="0.1.0")

    def run(self, block):
        return {'products': []}


