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
import sys
import json
import os
from pkgutil import walk_packages
from importlib import import_module

import recipes

import pyfits

__version__ = '0.4.1'

_logger = logging.getLogger("numina")

_recipe_logger = logging.getLogger('numina.recipes')

_recipe_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class ReductionResult(object):
    def __init__(self):
        self.id = None
        self.reduction_block = None
        self.other = None
        self.status = 0
        self.picklable = {}

class ObservingResult(object):
    def __init__(self):
        self.id = None
        self.images = []

# FIXME: pyfits.core.HDUList is treated like a list
# each extension is stored separately
class FitsEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pyfits.core.PrimaryHDU):
            filename = 'result.fits'
            if obj.header.has_key('FILENAME'):
                filename = obj.header['FILENAME']
            obj.writeto(filename, clobber=True)
            return filename
        return json.JSONEncoder.default(self, obj)

def main_internal(entry_point, obsres, parameters):
    _logger.info('entry point is %s', entry_point)

    # Set custom logger
    fh = logging.FileHandler('processing.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(_recipe_formatter)

    _recipe_logger.addHandler(fh)

    mod, klass = entry_point.split(':')

    module = import_module(mod)
    RecipeClass = getattr(module, klass)

    cp = {}
    pp = {}
    
    recipe = RecipeClass(pp, cp)

    recipe.configure(parameters)

    try:
        result = recipe(obsres)
    finally:
        _recipe_logger.removeHandler(fh)
    return result

def main2(args=None):
    _logger.info('Args are %s', args)

    try:
        pwd = os.getcwd()

        os.chdir(args[2])

        with open('task-control.json', 'r') as fd:
            control = json.load(fd)

        entry_point = control['reduction']['recipe']
        parameters = control['reduction']['parameters']

        obsres = ObservingResult()

        obsres.__dict__ = control['observing_result']

        # We are running arbitrary code here
        try:
            result = main_internal(entry_point, obsres, parameters)
        except Exception as error:
            result = {'error': str(error)}

        with open('result.json', 'w+') as fd:
            json.dump(result, fd, indent=1, cls=FitsEncoder)

        with open('result.json', 'r') as fd:
            result = json.load(fd)
    
    except (ImportError, ValueError, OSError) as error:
        _logger.error('%s', error)
    finally:
        os.chdir(pwd)    

    return result

def main(block):

    _logger.info('Creating Reduction Result')
    rr = ReductionResult()
    rr.reduction_block = block
    rr.other = 'Other info'

    try:
        entry_point = recipes.find_recipe(block.instrument, block.mode)

        result = main_internal(entry_point, block)

    except ValueError as msg:
        _logger.error('Something has happened: %s', str(msg))
        rr.status = 'ERROR'
    else:
        rr.status = 'OK'
        rr.picklable = {'result': result}

    return rr

class RecipeBase(object):
    '''Base class for all instrument recipes'''

    def __init__(self, author, version):
        self.__author__ = author
        self.__version__ = version
        self.environ = {}
        self.parameters = {}
    
    def configure(self, parameters):
        self.parameters = parameters

    def __call__(self, block, environ=None):

        self.environ = {}

        if environ is not None:
            self.environ.update(environ)

        self.environ['block_id'] = block.id

        result = self.run(block)

        return result

class RecipeType(object):
    def __init__(self, tag, comment='', default=None):
        self.tag = tag
        self.comment = comment
        self.default = default

class Keyword(RecipeType):
    def __init__(self, tag, comment='', default=None):
        RecipeType.__init__(self, tag, comment, default)        

class Image(RecipeType):
    def __init__(self, tag, comment='', default=None):
        RecipeType.__init__(self, tag, comment, default)        

class Map(RecipeType):
    def __init__(self, tag, comment='', default=None):
        RecipeType.__init__(self, tag, comment, default)        
        

def list_recipes():
    '''List all defined recipes'''
    return RecipeBase.__subclasses__() # pylint: disable-msgs=E1101
    
def recipes_by_obs_mode(obsmode):
    for rclass in list_recipes():
        if obsmode in rclass.capabilities:
            yield rclass
    
def walk_modules(mod):
    module = import_module(mod)
    for _, nmod, _ in walk_packages(path=module.__path__,
                                    prefix=module.__name__ + '.'):
        yield nmod
        
def init_recipe_system(modules):
    '''Load all recipe classes in modules'''
    for mod in modules:
        for sub in walk_modules(mod):
            import_module(sub)

class FITSHistoryHandler(logging.Handler):
    '''Logging handler using HISTORY FITS cards'''
    def __init__(self, header):
        logging.Handler.__init__(self)
        self.header = header

    def emit(self, record):
        msg = self.format(record)
        self.header.add_history(msg)




