from txrServer import txrServer
from instrument import Instrument
import threading

import logging
import logging.config
from xmlrpclib import Server

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("instrument.test")


class TestInstrument(Instrument):
    def __init__(self):
        super(TestInstrument, self).__init__('test', 'cass', ['bias', 'dark'])

    def parser(self, args):
        if args[0] == 'bias':
            return 'test', 'bias', 0, None, int(args[0])
        if args[0] == 'dark':
            return 'test', 'dark', float(args[0]), None, int(args[1])

o = TestInstrument()

server = txrServer(('localhost', 9010), allow_none=True, logRequests=False)
server.register_instance(o)

def main_loop():
    queue = o.queue1
    _logger.info('Waiting for events')
    while True:
        event = queue.get()
        _logger.info('Event is %s', event)
	

th = []
th.append(threading.Thread(target=main_loop))
th.append(threading.Thread(target=server.serve_forever))

for i in th:
    i.start()

for i in th:
    i.join()
