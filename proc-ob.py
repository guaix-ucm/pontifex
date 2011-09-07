
# Processing observation number=2, recipe=bias, instrument=megara

# Process obsblock id =2

import sys
import logging
import logging.config
import importlib

from numina import recipes
from model import Session, datadir, ObsBlock, ReductionResult

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("demo")

def myprint(i):
    print i.insId
    print i.mode
    for im in i.images:
        myprint2(im)

def myprint2(im):
    print im.name

def main(rb):
    _logger.info('Creating Reduction Result')
    rr = ReductionResult()
    rr.reduction_block = rb
    rr.other = 'Other info'
    rr.picklable = {}
    try:
        recipe_name = recipes.find_recipe(rb.instrument.name, rb.mode)
        _logger.info('recipe name is %s', recipe_name)

        # Find precomputed parameters for this recipe
        _logger.info('loading precomputed parameters')
        pp = recipes.find_parameters(recipe_name)

        module = importlib.import_module(recipe_name)
        _logger.info('loading requeriments from system')
        cp = {}
        
        for name, value in module.Recipe.requires():
            cp[name] = value        

        _logger.info('creating recipe')
        recipe = module.Recipe(pp, cp)
        _logger.info('running recipe')
        result = recipe.run(rb)

    except ValueError as msg:
        _logger.error('Something has happened: %s', str(msg))
        rr.status = 'ERROR'
    else:
        _logger.info('recipe finished')
        rr.status = 'OK'

    return rr

session = Session()

rb  = session.query(ObsBlock).filter_by(id=2).first()

rr = main(rb)

_logger.info('result stored in database')
session.add(rr)
session.commit()

