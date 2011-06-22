#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import os

from model import session, datadir
from model import ObsBlock, RecipeParameters

class Parameter(object):
    def __init__(self, name=None, default=None, comment=None):
        pass

class Requeriment(object):
    def __init__(self, name=None, default=None, comment=None):
        pass

class Configuration(object):
    def __init__(self, name=None, default=None, comment=None):
        pass
# 
class MegaraBiasRecipe(object):
    required_parameters = ['param1', 'param2']

class MegaraDarkRecipe(object):
    required_parameters = []
    master_bias = Requeriment(comment='Master bias images')
    iterations = Parameter(comment='Iterations of the recipe')

class MegaraFlatRecipe(object):
    required_parameters = []

_recipes = {'bias': MegaraBiasRecipe,
            'dark': MegaraDarkRecipe,
            'flat': MegaraFlatRecipe
}

def find_recipe(instrument, obsmode):
    return _recipes[obsmode]
    

obid = 1
workdir = 'ff04c82288946d71e881ff42d02987e8'

if not os.path.exists(workdir):
    os.makedirs(workdir)

print 'processing OB', obid

result = session.query(ObsBlock).filter_by(obsId=obid).one()

os.chdir(workdir)

for im in result.images:
    print 'copy image', im.name, 'here'
    # fake copy
    f = open(im.name, 'w')
    f.close()

print 'instrument', result.instrument
print 'observing mode', result.mode

Recipe = find_recipe(result.instrument, result.mode)

print 'recipe for instrument', result.instrument, 'and mode', result.mode, 'is', Recipe

obsblock = result

# default parameters
(params,) = session.query(RecipeParameters.parameters).filter_by(instrument=result.instrument).filter_by(mode=result.mode).one()
print params

rr = Recipe()
rr.parameters = params
