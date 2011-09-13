
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
import hashlib

_logger = logging.getLogger("demo")

def processPointing(**kwds):
    _logger.info('processPointing called wth kwds %s', kwds)
    _logger.info('creating root directory')
    m = hashlib.md5()
    m.update(str(time.time()))
    basedir = m.hexdigest()
    _logger.info('root directory is %s', basedir)
    _logger.info('copying the images')
    for image in kwds['images']:
        _logger.info('copy %s', image)
    _logger.info('create the recipe')
    _logger.info('configure the recipe')
    _logger.info('run the recipe')
    time.sleep(5)
    _logger.info('done')
    return {'base': 'ReductionResult', 'rootdir': basedir, 
        'fits': ['result1.fits', 'result2.fits'], 
        'logs': ['log1.txt', 'log2.txt', 'log3.xml']
    }

def processMosaic(**kwds):
    _logger.info('processMosaic called wth kwds %s', kwds)
    _logger.info('creating root directory')
    m = hashlib.md5()
    m.update(str(time.time()))
    basedir = m.hexdigest()
    _logger.info('root directory is %s', basedir)
    _logger.info('copying the results of children nodes')
    for nodeid in kwds['children']:
        _logger.info('nodeid is %d', nodeid)
    _logger.info('create the recipe')
    _logger.info('configure the recipe')
    _logger.info('run the recipe')
    time.sleep(5)
    _logger.info('done')
    return {'base': 'ReductionResult', 'rootdir': basedir, 
        'fits': ['result1.fits', 'result2.fits'], 
        'logs': ['log1.txt', 'log2.txt', 'log3.xml']
    }

def processCollect(**kwds):
    _logger.info('processCollect called wth kwds %s', kwds)
    _logger.info('creating root directory')
    m = hashlib.md5()
    m.update(str(time.time()))
    basedir = m.hexdigest()
    _logger.info('root directory is %s', basedir)
    _logger.info('copying the results of children nodes')

    _logger.info('create the recipe')
    _logger.info('configure the recipe')
    _logger.info('run the recipe')
    time.sleep(5)
    _logger.info('done')
    return {'base': 'ReductionResult', 'rootdir': basedir, 
        'fits': ['result1.fits', 'result2.fits'], 
        'logs': ['log1.txt', 'log2.txt', 'log3.xml']
    }

