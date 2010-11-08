from txrServer import txrServer
from corre import exec_obsmode

import time
import random
from SimpleXMLRPCServer import SimpleXMLRPCServer
from time import sleep
import threading
import uuid
from Queue import Queue
import logging
import logging.config
from xmlrpclib import Server

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("dbengine")

queue1 = Queue()

class DatabaseManager(object):
    def store_image(self, args):
        _logger.info('Received command')

    def version(self):
    	return '1.0'

im = DatabaseManager()

def manager():
    global queue1
    _logger.info('Waiting for events')
    while True:
        mandate = queue1.get()
        if mandate[0] == 'store':
            _logger.info('Storing image')
        else:
            _logger.info('Other command ')

server = txrServer(('localhost', 8050), allow_none=True, logRequests=False)
server.register_instance(im)

server.register_function(server.shutdown, name='shutdown')

th = []
th.append(threading.Thread(target=manager))
th.append(threading.Thread(target=server.serve_forever))

for i in th:
    i.start()

for i in th:
    i.join()

