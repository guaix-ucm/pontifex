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

import abc
import importlib

def find_recipe(instrument, mode):
    base = '%s.recipes' % instrument
    try:
        mod = importlib.import_module(base)
    except ImportError:
        msg = 'No instrument %s' % instrument
        raise ValueError(msg)

    try:
        entry = mod.find_recipe(mode)
    except KeyError:
        msg = 'No recipe for mode %s' % mode
        raise ValueError(msg)
        
    return '%s.%s' % (base, entry)

def find_parameters(recipe_name):
    # query somewhere for the precomputed parameters
    return {}

class RecipeBase(object):
    '''Base class for all instrument recipes'''

    __metaclass__ = abc.ABCMeta

    def __init__(self, author, version):
        super(RecipeBase, self).__init__()
        self.__author__ = author
        self.__version__ = version
        self.environ = {}
        self.parameters = {}
        self.instrument = None
    
    def configure(self, **kwds):
        if 'parameters' in kwds:
            self.parameters = kwds['parameters']
        if 'instrument' in kwds:
            self.instrument = kwds['instrument']

    @abc.abstractmethod
    def run(self, block):
        return

    def __call__(self, block, environ=None):

        self.environ = {}

        if environ is not None:
            self.environ.update(environ)

        self.environ['block_id'] = block.id

        try:

            result = self.run(block)

        except Exception as exc:
            result = {'error': {'type': exc.__class__.__name__, 
                                'message': str(e)}}

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

if __name__ == '__main__':
    from frida import find_recipe

    print find_recipe('bias')
