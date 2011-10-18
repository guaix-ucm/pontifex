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
from numina.recipes import Image

_logger = logging.getLogger("pontifex.proc")

def processPointing(session, **kwds):
    _logger.info('process called wth kwds %s', kwds)
    _logger.info('creating root directory')

    basedir = str(kwds['id'])
    os.chdir(taskdir)
    _logger.info('root directory is %s', basedir)

    basedir = os.path.abspath(basedir)
    workdir = os.path.join(basedir, 'work')
    resultsdir = os.path.join(basedir, 'results')

    os.mkdir(basedir)
    os.mkdir(workdir)
    os.mkdir(resultsdir)

    os.chdir(basedir)

    _logger.info('create config files, put them in root dir')

    filename = os.path.join(resultsdir, 'task-control.json')

    try:
        _logger.info('instrument=%(instrument)s mode=%(mode)s', kwds)
        entry_point = recipes.find_recipe(kwds['instrument'], kwds['mode'])
        _logger.info('entry point is %s', entry_point)
    except ValueError:
        _logger.warning('cannot find entry point for %(instrument)s and %(mode)s', kwds)
        raise
        
    mod, klass = entry_point.split(':')

    try:
        module = import_module(mod)
        RecipeClass = getattr(module, klass)
    except Exception as error:
        _logger.error(error)

    _logger.info('matching parameters')
    
    parameters = {}

    for req in RecipeClass.__requires__:
        _logger.info('recipe requires %s', req.tag)
        if isinstance(req, Image):
            # query here
            _logger.info('query for %s', req.tag)
            # FIXME: this query should be updated
            dps = session.query(DataProduct).filter_by(instrument_id=kwds['instrument'],   datatype=req.tag).order_by(desc(DataProduct.id))

            _logger.info('checking context')
            for cdp in dps:
                if all((c in kwds['context']) for c in cdp.context):
                    _logger.info('found requirement with acceptable context: %s', cdp.reference)
                    break
            else:
                cdp = None

            if cdp is None:
                _logger.warning("can't find %s", req.tag)
                raise ValueError("can't find %s", req.tag)
            else:
                parameters[req.tag] = cdp.reference
                _logger.debug('copy %s', cdp.reference)
                shutil.copy(os.path.join(productsdir, cdp.reference), workdir)
        else:
            parameters[req.tag] = req.default

    for req in RecipeClass.__provides__:
        _logger.info('recipe provides %s', req.tag)

    instrument = session.query(Instrument).filter_by(name=kwds['instrument']).first()
    
    _logger.info('copying the images')
    images = []
    for image in kwds['images']:
        _logger.debug('copy %s', image.name)
        images.append(image.name)
        shutil.copy(os.path.join(datadir, image.name), workdir)

    _logger.info('copying the children results')
    children_results = []
    for child in kwds['children']:
        for dp in child.product:
            _logger.debug('copy %s', dp.reference)
            children_results.append(dp.reference)
            shutil.copy(os.path.join(productsdir, dp.reference), workdir)

    config = {'observing_result': {'id': kwds['id'], 
        'images': images,
        'children': children_results,
        'instrument': kwds['instrument'],
        'mode': kwds['mode'],
        }, 
        'reduction': {'recipe': entry_point, 'parameters': parameters},
        'instrument': instrument.parameters,
        }
    with open(filename, 'w+') as fp:
        json.dump(config, fp, indent=1)

    return 0

processMosaic = processPointing

processCollect = processPointing

