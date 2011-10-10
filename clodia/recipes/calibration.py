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

from numina import RecipeBase, Image, __version__
from numina import FITSHistoryHandler
from numina import Image, Keyword

__all__ = ['BiasRecipe', 'DarkRecipe']

_logger = logging.getLogger('clodia.recipes')

_imgtype_key = Keyword('imagetype_key', 
                       comment='Name of image type header keyword',
                       default='IMGTYP')

_airmass_key = Keyword('airmass_key', 
                       comment='Name of airmass header keyword',
                       default='AIRMASS')

_exposure_key = Keyword('exposure_key', 
                       comment='Name of exposure header keyword',
                       default='EXPOSED')

_juliandate_key = Keyword('juliandate_key', 
                       comment='Name of Julian date header keyword',
                       default='MJD-OBS')

class BiasRecipe(RecipeBase):

    __author__ = "Sergio Pascual <sergiopr@fis.ucm.es>"
    __version__ = "0.1.0"
    __requires__ = [_imgtype_key]
    __provides__ = [Image('master_bias', comment='Master bias image')]

    def __init__(self, pp, cp):
        pass

    def run(self, rb):

        history_header = pyfits.Header()

        fh =  FITSHistoryHandler(history_header)
        fh.setLevel(logging.INFO)
        _logger.addHandler(fh)


    	_logger.info('starting bias reduction')

        images = rb.images

        cdata = []

        try:
            for image in images:
                hdulist = pyfits.open(image, memmap=True, mode='readonly')
                cdata.append(hdulist)

            _logger.info('stacking images')
            data = numpy.zeros(cdata[0]['PRIMARY'].data.shape, dtype='float32')
            for hdulist in cdata:
                data += hdulist['PRIMARY'].data

            data /= len(cdata)
            data += 2.0

            hdu = pyfits.PrimaryHDU(data, header=cdata[0]['PRIMARY'].header)
    
            # update hdu header with
            # reduction keywords
            hdr = hdu.header
            hdr.update('FILENAME', 'master_bias.fits')
            hdr.update('IMGTYP', 'BIAS', 'Image type')
            hdr.update('NUMTYP', 'MASTER_BIAS', 'Data product type')
            hdr.update('NUMXVER', __version__, 'Numina package version')
            hdr.update('NUMRNAM', 'BiasRecipe', 'Numina recipe name')
            hdr.update('NUMRVER', self.__version__, 'Numina recipe version')
        
            hdulist = pyfits.HDUList([hdu])

            _logger.info('bias reduction ended')

            # merge header with HISTORY log
            hdr.ascardlist().extend(history_header.ascardlist())    

            return {'result': {'master_bias': hdulist, 'qa': 1}}
        except OSError as error:
            return {'error' : {'exception': str(error)}}
        finally:
            _logger.removeHandler(fh)

            for hdulist in cdata:
                hdulist.close()

class DarkRecipe(RecipeBase):

    __author__ = "Sergio Pascual <sergiopr@fis.ucm.es>"
    __version__ = "0.1.0"
    __requires__ = [_imgtype_key, Image('master_bias', comment='Master bias image')]
    __provides__ = [Image('master_dark', comment='Master dark image')]

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



