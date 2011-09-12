
#    def process(instrument, mode, rb):
#        _logger.info('Creating Reduction Result')
#        rr = ReductionResult()
#        rr.other = 'Other info'
#        rr.picklable = {}
#        try:
#            recipe_name = recipes.find_recipe(instrument, mode)
#            _logger.info('recipe name is %s', recipe_name)
#    
#            # Find precomputed parameters for this recipe
#            _logger.info('loading precomputed parameters')
#            pp = recipes.find_parameters(recipe_name)
#    
#            module = importlib.import_module(recipe_name)
#            _logger.info('loading requeriments from system')
#            cp = {}
#            
#            for name, value in module.Recipe.requires():
#                cp[name] = value        
#    
#            _logger.info('creating recipe')
#            recipe = module.Recipe(pp, cp)
#            _logger.info('running recipe')
#            result = recipe.run(rb)
#    
#        except ValueError as msg:
#            _logger.error('Something has happened: %s', str(msg))
#            rr.state = 1
#        else:
#            _logger.info('recipe finished')
#            rr.state = 0

#        return rr

import logging
import time
_logger = logging.getLogger("demo")

def processPointing(**kwds):
    _logger.info('processPointing called wth kwds %s', kwds)
    _logger.info('creating root directory')
    _logger.info('copying the images')
    _logger.info('create the recipe')
    _logger.info('configure the recipe')
    _logger.info('run the recipe')
    time.sleep(5)
    _logger.info('done')
    return 0

def processMosaic(**kwds):
    return 0

def processCollect(**kwds):
    return 0
