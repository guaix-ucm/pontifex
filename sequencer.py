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
_logger = logging.getLogger("sequencer")

queue = Queue()
queue2 = Queue()
queue3 = Queue()

instruments = {}

class SequenceManager(object):
    def __init__(self):
        self._instruments = instruments

    def run_command(self, args):
        _logger.info('Received command %s', args)
        argslist = args.split()	
        if argslist[0] in self._instruments:
    	    queue2.put(argslist)
    	    
            _logger.info('Enqueued')
            return "Enqued"
        else:
            _logger.info('No such instrument')
            return "No such instrument"

    def version(self):
    	return '1.0'

    def unregister(self, name):
        _logger.info('Instrument unregistered %s', name)
    	del self._instruments[name]

    def register(self, name, host, port, focus, obsmodes):
        if name not in self._instruments:
            self._instruments[name]= (Server('http://%s:%d' % (host, int(port))), 
                                              focus, obsmodes)
            _logger.info('Instrument registered %s %s %s %s %s', name, host, port, focus, obsmodes)
#            vacio.release()

    def return_image(self, ievent):
        _logger.info('Received ievent')
        queue2.put(ievent)
        return True

    def instruments(self):
    	return self._instruments.keys()

im = SequenceManager()

def sequencer():
    global queue2
    _logger.info('Waiting for events')
    while True:
        mandate = queue2.get()
        _logger.info('Event %s', mandate[0])
        if mandate[0] == 'store':
            _logger.info('Sending image to storage engine')
        elif mandate[0] in instruments:
            _logger.info('Observation instrument=%s mode=%s started', mandate[0], mandate[1])
            server = instruments[mandate[0]][0]
            try:
                server.command(mandate[1:])
            except Exception, ex:
                _logger.error('Error %s', ex)
        else:
            _logger.info('Instrument %s not registred', mandate[0])

server = txrServer(('localhost', 8010), allow_none=True, logRequests=False)
server.register_instance(im)

server.register_function(server.shutdown, name='shutdown')
#server.serve_forever()

th = []
th.append(threading.Thread(target=sequencer))
th.append(threading.Thread(target=server.serve_forever))

for i in th:
    i.start()

for i in th:
    i.join()

