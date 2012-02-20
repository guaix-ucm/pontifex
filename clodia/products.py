#
# Copyright 2011 Universidad Complutense de Madrid
# 
# This file is part of Pontifex
# 
# Pontifex is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Pontifex is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Pontifex.  If not, see <http://www.gnu.org/licenses/>.
#

'''Products of the Clodia Pipeline'''


'''
    RAW_BIAS DataFrame
    RAW_DARK DataFrame
    RAW_FLAT DataFrame
    RAW_ILLUM DataFrame
    RAW_SCIENCE DataFrame

    MASTER_BIAS  DataFrame(detector)
    MASTER_DARK  DataFrame(detector, exposure)
    MASTER_FLAT  DataFrame(detector, filter)
    MASTER_ILLUM DataFrame(detector, filter)

    POINTING DataFrame
    MOSAIC DataFrame

'''

from numina.recipes import DataFrame

class MasterBias(DataFrame):
    def __init__(self, hdu):
        super(MasterBias, self).__init__(hdu)

    def metadata(self):
        hdr = self.image[0].header
        yield 'detector0.mode', hdr['ccdmode']

class MasterDark(DataFrame):
    def __init__(self, hdu):
        super(MasterDark, self).__init__(hdu)

    def metadata(self):
        hdr = self.image[0].header
        yield 'detector0.mode', hdr['ccdmode']

class MasterFlat(DataFrame):
    def __init__(self, hdu):
        super(MasterFlat, self).__init__(hdu)

    def metadata(self):
        hdr = self.image[0].header
        yield 'detector0.mode', hdr['ccdmode']
        yield 'filter0', hdr['filter']

class MasterIllum(DataFrame):
    def __init__(self, hdu):
        super(MasterIllum, self).__init__(hdu)

    def metadata(self):
        hdr = self.image[0].header
        yield 'detector0.mode', hdr['ccdmode']
        yield 'filter0', hdr['filter']

class PointingImage(DataFrame):
    def __init__(self, hdu):
        super(PointingImage, self).__init__(hdu)

    def metadata(self):
        hdr = self.image[0].header
        yield 'detector0.mode', hdr['ccdmode']
        yield 'filter0', hdr['filter']

class Mosaic(DataFrame):
    def __init__(self, hdu):
        super(Mosaic, self).__init__(hdu)

    def metadata(self):
        hdr = self.image[0].header
        yield 'detector0.mode', hdr['ccdmode']
        yield 'filter0', hdr['filter']

