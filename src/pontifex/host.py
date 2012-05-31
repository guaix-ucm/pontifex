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
from xmlrpclib import ServerProxy
import os.path
import uuid

from numina.user import run_recipe_from_file
from numina.serialize import lookup as lookup_serializer

# Processing tasks STATES
CREATED, COMPLETED, ENQUEUED, PROCESSING, FINISHED, ERROR = range(6)

# create logger for host
_logger = logging.getLogger("pontifex.host")

class PontifexHost(object):
    def __init__(self, master, host, port):
        super(PontifexHost, self).__init__()
        uid = uuid.uuid5(uuid.NAMESPACE_URL, 'http://%s:%d' % (host, port))
        self.cid = uid.hex
        self.host = host
        self.port = port
        self.rserver = ServerProxy(master)
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

    def pass_info(self, taskid, config):
        _logger.info('received taskid=%d', taskid)
        self.queue.put((taskid, config))

    def worker(self):
        taskdir = os.path.abspath('task')
        while True:
            token = self.queue.get()            
            if token is not None:
                taskid, config = token
                _logger.info('processing taskid %d', taskid)
                basedir = os.path.join(taskdir, str(taskid))
                workdir = os.path.join(basedir, 'work')
                resultsdir = os.path.join(basedir, 'results')
                filename = os.path.join(resultsdir, 'task-control.json')
                _logger.debug('Basedir: %s', basedir)
                _logger.debug('Workdir: %s', workdir)
                _logger.debug('Resultsdir: %s', resultsdir)                

                #result = run_recipe_from_file(filename, sload, sdump, workdir=workdir, 
                #                    resultsdir=resultsdir, cleanup=False)
                
                result = {'products': {}}

                _logger.info('finished')
                
                self.queue.task_done()
                _logger.info('sending back to server')
                self.rserver.receiver(self.cid, result, taskid)
                os.chdir(taskdir)
            else:
                _logger.info('ending worker thread')
                return
