
import logging
import json
import os

_logger = logging.getLogger("demo")

def processPointing(**kwds):
    _logger.info('processPointing called wth kwds %s', kwds)
    _logger.info('creating root directory')

    basedir = str(kwds['id'])
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

    return 0

def processMosaic(**kwds):
    _logger.info('processMosaic called wth kwds %s', kwds)
    _logger.info('creating root directory')

    basedir = str(kwds['id'])
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

    return 0

def processCollect(**kwds):
    _logger.info('processMosaic called wth kwds %s', kwds)
    _logger.info('creating root directory')

    basedir = str(kwds['id'])
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

    return 0
