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

'''Products of the Clodia Pipeline'''


'''
    RAW_BIAS Image
    RAW_DARK Image
    RAW_FLAT Image
    RAW_ILLUM Image
    RAW_SCIENCE Image

    MASTER_BIAS  Image(detector)
    MASTER_DARK  Image(detector, exposure)
    MASTER_FLAT  Image(detector, filter)
    MASTER_ILLUM Image(detector, filter)

    POINTING Image
    MOSAIC Image

'''

import pyfits

def metadata_extractor_master_bias(name):
    hdr = pyfits.getheader(name)

    yield 'detector0.mode', hdr['ccdmode']

    yield 'filter0', hdr['filter']


def metadata_extractor_master_dark(name):
    hdr = pyfits.getheader(name)

    yield 'detector0.mode', hdr['ccdmode']

    yield 'filter0', hdr['filter']


def metadata_extractor_master_flat(name):
    hdr = pyfits.getheader(name)

    yield 'detector0.mode', hdr['ccdmode']

    yield 'filter0', hdr['filter']


class Product(object):
    pass

class Image(Product):
    pass

MasterBias = type("MasterBias", (Image,), {})

class MasterBias(Image):
    def __init__(self, hdu):
        pass

class MasterDark(Image):
    pass

class MasterFlat(Image):
    pass

class MasterIllum(Image):
    pass

class PointingImage(Image):
    pass

class Mosaic(Image):
    pass

class Recipe(object):
    def superrun(self, ob):
        print 'base'
        return self.run(ob)

import pyfits
import numpy

class BiasRecipe(Recipe):

    __produces__ = {'master_bias': MasterBias, 'master_bias2': tuple}

    def run(self, ob):
        
        result = {'products': {}, 'error': None}
    
        products = result['products']

        data = numpy.zeros((10, 10), dtype='float32')

        img = pyfits.PrimaryHDU(data)

        master_bias = img

        products['master_bias'] = MasterBias(master_bias)
        products['master_bias2'] = (img, "MASTER_BIAS", "QA=1")

        return result


if __name__ == '__main__':

    bb = BiasRecipe()

    res = bb.superrun([])

    if 'error' in res and res['error'] is not None:
        print 'some error'
    elif 'products' in res:
        print 'check products'
        for key,val in res['products'].items():
            print key, bb.__produces__[key]
            print key, isinstance(val, bb.__produces__[key])
    
    else:
        print 'malformed result' 
    print res
