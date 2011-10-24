#!/usr/bin/python

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
# Pontifex is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Pontifex.  If not, see <http://www.gnu.org/licenses/>.
#

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

from datetime import datetime

from sqlalchemy import create_engine

from pontifex.model import Users, Instrument, Channel, InstrumentConfiguration
from pontifex.model import Recipe, RecipeConfiguration
from pontifex.model import ContextValue, ContextDescription, ProcessingSet
from pontifex.model import init_model, metadata, Session

#engine = create_engine('sqlite:///devdata.db', echo=False)
engine = create_engine('sqlite:///devdata.db', echo=True)
engine.execute('pragma foreign_keys=on')

init_model(engine)
metadata.create_all(engine)
session = Session()

user = Users()
user.name = 'auto'
user.status = 1
user.usertype = 1
session.add(user)

user = Users()
user.name = 'sergiopr'
user.status = 1
user.usertype = 1
session.add(user)

channel = Channel()
channel.name = 'default'
session.add(channel)

channel = Channel()
channel.name = 'fast'
session.add(channel)

ii = Instrument()
ii.name = 'megara'
session.add(ii)

pset = ProcessingSet()
pset.instrument = ii
pset.name = 'default'
session.add(pset)

ii = Instrument()
ii.name = 'emir'
session.add(ii)

recipes = {
    'bias_image': 'auxiliary:Recipe1',
    'dark_current_image': 'auxiliary:Recipe2',
    'intensity_flatfield': 'auxiliary:Recipe3',
    'msm_spectral_flatfield': 'auxiliary:Recipe4',
    'slit_transmission_calibration': 'auxiliary:Recipe5',
    'wavelength_calibration': 'auxiliary:Recipe6',
    'ts_rough_focus': 'auxiliary:Recipe7',
    'ts_fine_focus': 'auxiliary:Recipe8',
    'emir_focus_control': 'auxiliary:Recipe9',
    'image_setup': 'auxiliary:Recipe10',
    'mos_and_longslit_setup': 'auxiliary:Recipe11',
    'target_acquisition': 'auxiliary:Recipe12',
    'mask_imaging': 'auxiliary:Recipe13',
    'msm_and_lsm_check': 'auxiliary:Recipe14',
    'stare_image': 'image:Recipe15',
    'nb_image': 'image:Recipe16',
    'dithered_image':'image:Recipe17',
    'microdithered_image':'image:Recipe18',
    'mosaiced_image': 'image:Recipe19',
    'stare_spectra': 'mos:Recipe20',
    'dn_spectra': 'mos:Recipe21',
    'offset_spectra': 'mos:Recipe22',
    'raster_spectra': 'ls:Recipe23',
}

for r in recipes:
    a = Recipe()
    a.instrument = ii
    a.mode = r
    a.module = recipes[r]
    a.active = True
    session.add(a)

    b = RecipeConfiguration()
    b.instrument = ii
    b.module = recipes[r]
    b.parameters = {}
    b.description = "Description"
    b.active = True
    session.add(b)

cc = InstrumentConfiguration()
cc.instrument = ii
cc.description = 'Default configuration'
cc.active = True
cc.parameters = {
                 'name': 'emir',
                 'detectors': [(2048, 2048)],
		 'metadata' : {'imagetype': 'IMGTYP',
	                'airmass': 'AIRMASS',
        	        'exposure': 'EXPOSED',
                	'juliandate': 'MJD-OBS',
                	'detector.mode': 'CCDMODE',
                	'filter0': 'FILTER'
                	},
		'amplifiers': [
			[((1024, 2048), (896, 1024)), 
			((1024, 2048), (768, 896)), 
			((1024, 2048), (640, 768)), 
			((1024, 2048), (512, 640)), 
			((1024, 2048), (384, 512)), 
			((1024, 2048), (256, 384)), 
			((1024, 2048), (128, 256)), 
			((1024, 2048), (0, 128)), 
			((896, 1024), (0, 1024)), 
			((768, 896), (0, 1024)), 
			((640, 768), (0, 1024)), 
			((512, 640), (0, 1024)), 
			((384, 512), (0, 1024)), 
			((256, 384), (0, 1024)), 
			((128, 256), (0, 1024)), 
			((0, 128), (0, 1024)), 
			((0, 1024), (1024, 1152)), 
			((0, 1024), (1152, 1280)), 
			((0, 1024), (1280, 1408)), 
			((0, 1024), (1408, 1536)), 
			((0, 1024), (1536, 1664)), 
			((0, 1024), (1664, 1792)), 
			((0, 1024), (1792, 1920)), 
			((0, 1024), (1920, 2048)), 
			((1024, 1152), (1024, 2048)), 
			((1152, 1280), (1024, 2048)), 
			((1280, 1408), (1024, 2048)), 
			((1408, 1536), (1024, 2048)), 
			((1536, 1664), (1024, 2048)), 
			((1664, 1792), (1024, 2048)), 
			((1792, 1920), (1024, 2048)), 
			((1920, 2048), (1024, 2048))]
			],
                }

session.add(cc)

pset = ProcessingSet()
pset.instrument = ii
pset.name = 'default'
session.add(pset)

ii = Instrument()
ii.name = 'frida'
session.add(ii)

pset = ProcessingSet()
pset.instrument = ii
pset.name = 'default'
session.add(pset)

ii = Instrument()
ii.name = 'clodia'
session.add(ii)

# equivalence

recipes = {'bias': 'calibration:BiasRecipe',
    'dark': 'calibration:DarkRecipe',
    'flat': 'calibration:FlatRecipe',
    'direct_image': 'science:DirectImage',
    'mosaic_image': 'science:MosaicImage',
    'null': 'science:Null',
}

for r in recipes:
    a = Recipe()
    a.instrument = ii
    a.mode = r
    a.module = recipes[r]
    a.active = True
    session.add(a)

    b = RecipeConfiguration()
    b.instrument = ii
    b.module = recipes[r]
    b.parameters = {}
    b.description = "Description"
    b.active = True
    session.add(b)

cc = InstrumentConfiguration()
cc.instrument = ii
cc.description = 'Default configuration'
cc.parameters = {
                 'name': 'clodia',
                 'detectors': [(256, 256)],
		 'metadata' : {'imagetype': 'IMGTYP',
	                'airmass': 'AIRMASS',
        	        'exposure': 'EXPOSED',
                	'juliandate': 'MJD-OBS',
                	'detector.mode': 'CCDMODE',
                	'filter0': 'FILTER'
                	},
		'amplifiers' : [[((0, 256), (0,256))]],
                }
cc.active = True
session.add(cc)

cc = InstrumentConfiguration()
cc.instrument = ii
cc.description = 'Old configuration'
cc.parameters = {
                 'name': 'clodia',
                 'detectors': [(256, 256)],
		 'metadata' : {'imagetype': 'IMGTYP',
	                'airmass': 'AIRMASS',
        	        'exposure': 'EXPOSED',
                	'juliandate': 'MJD-OBS',
                	'detector.mode': 'CCDMODE',
                	'filter0': 'FILTER'
                	},
		'amplifiers' : [[((0, 256), (0,256))]],
                }
cc.revoke_event = datetime.utcnow()
session.add(cc)

pset = ProcessingSet()
pset.instrument = ii
pset.name = 'default'
session.add(pset)

pset = ProcessingSet()
pset.instrument = ii
pset.name = 'test'
session.add(pset)

desc = ContextDescription()
desc.instrument_id = 'clodia'
desc.name = 'detector0.mode'
desc.description = 'Clodia detector readout mode'
session.add(desc)
session.commit()

for name in ['normal', 'slow', 'turbo']:
    vl = ContextValue()
    vl.definition = desc
    vl.value = name
    session.add(vl)

desc = ContextDescription()
desc.instrument_id = 'clodia'
desc.name = 'filter0'
desc.description = 'Clodia filter'
session.add(desc)
session.commit()

for name in ['310', '311', '312', '313', '314', '315']:
    vl = ContextValue()
    vl.definition = desc
    vl.value = name
    session.add(vl)

session.add(desc)

session.commit()
