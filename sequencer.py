from txrServer import txrServer

import threading
from Queue import Queue
import logging
import logging.config
from xmlrpclib import Server

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("sequencer")

queue = Queue()

instruments = ['test']

dbserver = Server('http://localhost:8050')
insserver = Server('http://localhost:9010')

class SequenceManager(object):
    def __init__(self):
        self._instruments = instruments

    # Console
    def run_command(self, args):
        _logger.info('Received console command %s', args)
        argslist = args.split()
        if argslist[0] in instruments:
    	    queue.put(('instrument',) + tuple(argslist))
            return True
        else:
            _logger.warning('No such instrument')
            return False

    def version(self):
    	return True

    # Instrument
    def return_image(self, event):
        _logger.info('Received instrument event % s', event)
        queue.put(event)
        return True

sm = SequenceManager()

def sequencer():
    global queue
    _logger.info('Waiting for events')
    while True:
        mandate = queue.get()
        if mandate[0] == 'instrument':
            _logger.info('Observation instrument=%s mode=%s started', mandate[1], mandate[2])
            # Create obsblock
            try:
                dbserver.startobsblock(mandate[1:3])
                insserver.command(mandate[1:])
            except Exception, ex:
                _logger.error('Error %s', ex)
        elif mandate[0] == 'endobsblock':
            dbserver.endobsblock()
        elif mandate[0] == 'store':
            _logger.info('Sending event to storage engine')
            dbserver.store_image(mandate)
        else:
            _logger.warning('Mandate %s does not exist', mandate[0])

server = txrServer(('localhost', 8010), allow_none=True, logRequests=False)
server.register_instance(sm)

server.register_function(server.shutdown, name='shutdown')

th = []
th.append(threading.Thread(target=sequencer))
th.append(threading.Thread(target=server.serve_forever))

for i in th:
    i.start()

for i in th:
    i.join()

