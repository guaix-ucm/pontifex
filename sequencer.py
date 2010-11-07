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


class InstrumentManager(object):
    def __init__(self):
        self.instruments = {}

    def run_command(self, args):
        repeat = 0
        argslist = args.split()
        return queue2.put(argslist)
    def version(self):
	return '1.0'	
    def unregister(self, name):
        _logger.info('Instrument unregistered %s', name)
	del self.instruments[name]

    def register(self, name, host, port, focus, obsmodes):
        if name not in self.instruments:
            self.instruments[name]= (Server('http://%s:%d' % (host, int(port))), 
                                              focus, obsmodes)
            _logger.info('Instrument registered %s %s %s %s %s', name, host, port, focus, obsmodes)
#            vacio.release()

    def instruments(self):
	return self.instruments.keys()

    def finish_notify(self, name):
        if name in self.instruments:
#       a,b,c = self.slaves[id]
#       self.slaves[id] = (a, b, True)
            _logger.info('Instrument %s finished operation', name)
#            vacio.release()

im = InstrumentManager()

def sequencer():
    global queue2
    _logger.info('Waiting for events')
    while True:
        mandate = queue2.get()
        _logger.info('Observing')
        if mandate[0] in im.instruments:
            _logger.info('Observation instrument=%s mode=%s started', mandate[0], mandate[1])
            im.instruments.command(mandate[1:])
        #queue.put(mandate)

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

