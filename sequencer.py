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

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("sequencer")

queue = Queue()
queue2 = Queue()

class TestObsModParser:
    def bias(self, args):
        return 'test', 'bias', 0, None, int(args[0])
    def dark(self, args):
        return 'test', 'dark', float(args[0]), None, int(args[1])

ot = TestObsModParser()

class Test(object):
    def __init__(self, queue):
        self.queue = queue
    
    def observations_waiting(self):
        return self.queue.qsize()

    def run_command(self, args):
        repeat = 0
        argslist = args.split()
        fun = getattr(ot, argslist[1])
        pars = fun(argslist[2:])
        return queue2.put(pars)

    def gimme_observation(self):
        return self.queue.get()

def sequencer():
    global queue2
    _logger.info('Waiting for events')
    while True:
        mandate = queue2.get()
        _logger.info('Observing')
        exec_obsmode(*mandate)
        queue.put(mandate)
        _logger.info('Finished observation instrument=%s mode=%s', mandate[0],
        mandate[1])

server = txrServer(('localhost', 8010), allow_none=True, logRequests=False)
server.register_instance(Test(queue))

server.register_function(server.shutdown, name='shutdown')
#server.serve_forever()

th = []
th.append(threading.Thread(target=sequencer))
th.append(threading.Thread(target=server.serve_forever))

for i in th:
    i.start()

for i in th:
    i.join()

