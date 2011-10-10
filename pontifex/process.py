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
import json
import os
import os.path
import shutil
from importlib import import_module

from sqlalchemy import desc

from model import taskdir, datadir, productsdir, DataProduct
from model import Session, Instrument
import numina.recipes as recipes
from numina import Image

_logger = logging.getLogger("pontifex.proc")

def processPointing(session, **kwds):
    _logger.info('process called wth kwds %s', kwds)
    _logger.info('creating root directory')

    basedir = str(kwds['id'])
    os.chdir(taskdir)
    _logger.info('root directory is %s', basedir)

    os.mkdir(basedir)
    os.chdir(basedir)

    _logger.info('copying the images')
    for image in kwds['images']:
        _logger.debug('copy %s', image.name)
        shutil.copy(os.path.join(datadir, image.name), '.')

    _logger.info('create config files, put them in root dir')

    filename = 'task-control.json'

    try:
        _logger.info('instrument=%(instrument)s mode=%(mode)s', kwds)
        entry_point = recipes.find_recipe(kwds['instrument'], kwds['mode'])
    except ValueError:
        _logger.warning('cannot find entry point')
        raise
        
    _logger.info('recipe entry point is %s', entry_point)

    mod, klass = entry_point.split(':')

    module = import_module(mod)
    RecipeClass = getattr(module, klass)

    parameters = {}
    for req in RecipeClass.__requires__:
        _logger.info('recipe requires %s', req.tag)
        if isinstance(req, Image):
            # query here
            _logger.info('query for %s', req.tag)
            # FIXME: this query should be updated
            dps = session.query(DataProduct).filter_by(instrument=kwds['instrument'],   datatype=req.tag).order_by(desc(DataProduct.id)).first()
            if dps is None:
                _logger.warning("can't find %s", req.tag)
                raise ValueError
            else:
                parameters[req.tag] = dps.reference
                _logger.debug('copy %s', dps.reference)
                shutil.copy(os.path.join(productsdir, dps.reference), '.')
        else:
            parameters[req.tag] = req.default

    for req in RecipeClass.__provides__:
        _logger.info('recipe provides %s', req.tag)

    instrument = session.query(Instrument).filter_by(name=kwds['instrument']).first()

    with open(filename, 'w+') as fp:
        config = {'observing_result': {'id': kwds['id'], 
        'images': [image.name for image in kwds['images']]}, 
        'reduction': {'recipe': entry_point, 'parameters': parameters},
        'instrument': instrument.parameters,
        }
        json.dump(config, fp, indent=2)

    return 0

processMosaic = processPointing

processCollect = processPointing

