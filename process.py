
import logging
import json
import os
import os.path
import shutil

from model import taskdir, datadir

_logger = logging.getLogger("pontifex.proc")

def processPointing(**kwds):
    _logger.info('processPointing called wth kwds %s', kwds)
    _logger.info('creating root directory')

    basedir = str(kwds['id'])
    os.chdir(taskdir)
    _logger.info('root directory is %s', basedir)

    os.mkdir(basedir)
    os.chdir(basedir)

    _logger.info('copying the images')
    for image in kwds['images']:
        _logger.info('copy %s', image.name)
        shutil.copy(os.path.join(datadir, image.name), '.')

    _logger.info('create config files, put them in root dir')

    filename = 'task-control.json'
    with open(filename, 'w+') as fp:
        config = {'observing_result': {'id': kwds['id'], 'images': [image.name for image in kwds['images']]}}
        json.dump(config, fp, indent=2)

    return 0

def processMosaic(**kwds):
    _logger.info('processMosaic called wth kwds %s', kwds)
    _logger.info('creating root directory')

    basedir = str(kwds['id'])
    os.chdir(taskdir)
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
    os.chdir(taskdir)
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
