#
# Copyright 2011 Universidad Complutense de Madrid
# 
# This file is part of Pontifex
# 
# Pontifex is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Pontifex is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Pontifex.  If not, see <http://www.gnu.org/licenses/>.
#

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4


import logging
from Queue import Queue
import xmlrpclib
import os.path
import uuid

import yaml

from numina.pipeline import import_object

from numina.recipes.oblock import obsres_from_dict  

# Processing tasks STATES
CREATED, COMPLETED, ENQUEUED, PROCESSING, FINISHED, ERROR = range(6)

# create logger for host
_logger = logging.getLogger("pontifex.host")

def run_recipe_from_file(taskid, taskdir, config):
    basedir = os.path.join(taskdir, str(taskid))
    workdir = os.path.join(basedir, 'work')
    resultsdir = os.path.join(basedir, 'results')

    task_control = config
    
    if 'instrument' in task_control:
        _logger.info('config contains instrument')
        ins_pars = task_control['instrument']
    if 'observing_result' in task_control:
        _logger.info('config contains observing result')
        obsres_dict = task_control['observing_result']       
        obsres = obsres_from_dict(obsres_dict)

    if 'reduction' in task_control:
        params = task_control['reduction']['parameters']

    try:
        # RecipeClass = get_recipe(ins_pars['pipeline'], obsres.mode)
        RecipeClass = import_object(task_control['reduction']['recipe'])
        _logger.info('entry point is %s', RecipeClass)
    except ValueError:
        #_logger.warning('cannot find entry point for %(instrument)s and %(mode)s', obsres.__dict__)
        raise
                   
    _logger.debug('creating runinfo')
            
    runinfo = {}
    runinfo['workdir'] = workdir
    runinfo['resultsdir'] = resultsdir
    runinfo['entrypoint'] = RecipeClass

    # Set custom logger
    _recipe_logger = RecipeClass.logger
    _recipe_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    processing_log = 'processing.log'

    _logger.debug('creating custom logger "%s"', processing_log)
    os.chdir(resultsdir)
    fh = logging.FileHandler(processing_log)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(_recipe_formatter)
    _recipe_logger.addHandler(fh)

    result = {'products': {}}
    _recipe_logger.removeHandler(fh)

    return result

class PontifexHost(object):
    def __init__(self, master, host, port):
        super(PontifexHost, self).__init__()
        uid = uuid.uuid5(uuid.NAMESPACE_URL, 'http://%s:%d' % (host, port))
        self.cid = uid.hex
        self.host = host
        self.port = port
        self.rserver = xmlrpclib.ServerProxy(master)
        self.rserver.register(self.cid, host, port, ['EMIR', 'MEGARA'])

        self.doned = False
        self.queue = Queue()

        _logger.info('ready')

    def quit(self):
        _logger.info('ending')
        self.rserver.unregister(self.cid)
        self.queue.put(None)

    def version(self):
        return '1.0'

    def pass_info(self, taskid, config, ob):
        _logger.info('received taskid=%d', taskid)
        self.queue.put((taskid, config, ob))

    def worker(self):
        taskdir = os.path.abspath('task')
        while True:
            token = self.queue.get()            
            if token is not None:
                taskid, config, ob = token
                _logger.info('processing taskid=%d', taskid)
                basedir = os.path.join(taskdir, str(taskid))
                workdir = os.path.join(basedir, 'work')
                resultsdir = os.path.join(basedir, 'results')                
                _logger.debug('Basedir: %s', basedir)
                _logger.debug('Workdir: %s', workdir)
                _logger.debug('Resultsdir: %s', resultsdir)                

                run_recipe_from_file(taskid, taskdir, config)
                
                result = {'products': {}}

                _logger.info('finished')
                
                self.queue.task_done()
                _logger.info('sending back to server')
                self.rserver.receiver(self.cid, result, taskid)
                os.chdir(taskdir)
            else:
                _logger.info('ending worker thread')
                return
