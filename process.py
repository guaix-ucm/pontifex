
import logging
import time
import hashlib
import json
import os

from numina import main2

_logger = logging.getLogger("demo")

def processPointing(**kwds):
    _logger.info('processPointing called wth kwds %s', kwds)
    _logger.info('creating root directory')
    m = hashlib.md5()
    m.update(str(time.time()))
    basedir = str(kwds['id']) # m.hexdigest()
    os.chdir('/home/spr/devel/pontifex-db/task')
    _logger.info('root directory is %s', basedir)
    os.mkdir(basedir)
    os.chdir(basedir)
    _logger.info('copying the images')
    for image in kwds['images']:
        _logger.info('copy %s', image)

    _logger.info('create config files, put them in root dir')

    filename = 'task-control.json'
    with open(filename, 'w+') as fp:
        config = {'observing_result': {'id': kwds['id'], 'images': kwds['images']}}
        json.dump(config, fp, indent=2)

    _logger.info('run the recipe')
    main2(['-d','--basedir', basedir, '--datadir', 'data', '--run', filename])
    _logger.info('collect results')

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

