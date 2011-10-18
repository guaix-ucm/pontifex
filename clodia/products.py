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

from numina.recipes import Image2

class MasterBias(Image2):
    def __init__(self, hdu):
        super(MasterBias, self).__init__(hdu)

    def metadata(self):
        hdr = self.image[0].header
        yield 'detector0.mode', hdr['ccdmode']

class MasterDark(Image2):
    def __init__(self, hdu):
        super(MasterDark, self).__init__(hdu)

    def metadata(self):
        hdr = self.image[0].header
        yield 'detector0.mode', hdr['ccdmode']

class MasterFlat(Image2):
    def __init__(self, hdu):
        super(MasterFlat, self).__init__(hdu)

    def metadata(self):
        hdr = self.image[0].header
        yield 'detector0.mode', hdr['ccdmode']
        yield 'filter0', hdr['filter']

class MasterIllum(Image2):
    def __init__(self, hdu):
        super(MasterIllum, self).__init__(hdu)

    def metadata(self):
        hdr = self.image[0].header
        yield 'detector0.mode', hdr['ccdmode']
        yield 'filter0', hdr['filter']

class PointingImage(Image2):
    def __init__(self, hdu):
        super(PointingImage, self).__init__(hdu)

    def metadata(self):
        hdr = self.image[0].header
        yield 'detector0.mode', hdr['ccdmode']
        yield 'filter0', hdr['filter']

class Mosaic(Image2):
    def __init__(self, hdu):
        super(Mosaic, self).__init__(hdu)

    def metadata(self):
        hdr = self.image[0].header
        yield 'detector0.mode', hdr['ccdmode']
        yield 'filter0', hdr['filter']

