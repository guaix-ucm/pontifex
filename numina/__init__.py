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

# -*- coding: utf-8 -*-

import logging
import importlib
import sys
import json
import os

from . import recipes
from . import model

_logger = logging.getLogger("numina")

_recipe_logger = logging.getLogger('numina.recipes')

_recipe_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def main2(args=None):
    _logger.info('Args are %s', args)

    try:
        pwd = os.getcwd()

        os.chdir(args[2])

        with open('task-control.json', 'r') as fd:
            control = json.load(fd)

        recipe_name = control['reduction']['recipe']
        _logger.info('recipe name is %s', recipe_name)

        # Set custom logger
        fh = logging.FileHandler('processing.log')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(_recipe_formatter)

        _recipe_logger.addHandler(fh)

        module = importlib.import_module(recipe_name)

        recipe = module.Recipe({}, {})
        
        result = recipe.run(None)

        _recipe_logger.removeHandler(fh)

        if 'error' in result:
            # we have an error here
            code = 1
            # error structure should go here
        elif 'result' in result:

            with open('result.fits', 'w+') as fd:
                pass
        
            with open('result.json', 'w+') as fd:
                json.dump(result, fd, indent=1)

            code = 0
        else:
            raise ValueError('Malformed recipe result')
    
    except (ImportError, ValueError, OSError) as error:
        _logger.error('%s', error)
        code = 1
    finally:
        os.chdir(pwd)    

    return code

def main(rb):

    _logger.info('Creating Reduction Result')
    rr = model.ReductionResult()
    rr.reduction_block = rb
    rr.other = 'Other info'

    try:
        recipe_name = recipes.find_recipe(rb.instrument, rb.mode)

        # Find precomputed parameters for this recipe
        pp = recipes.find_parameters(recipe_name)

        module = importlib.import_module(recipe_name)

        cp = {}
        
        for name, value in module.Recipe.requires():
            cp[name] = value        

        recipe = module.Recipe(pp, cp)
        result = recipe.run(rb)

    except ValueError as msg:
        _logger.error('Something has happened: %s', str(msg))
        rr.status = 'ERROR'
    else:
        rr.status = 'OK'
        rr.picklable = {'result': result}

    return rr
