from txrServer import txrServer
from instrument import Instrument, siiill

import xmlrpclib
import threading
import logging
import logging.config
from xmlrpclib import Server
from Queue import Queue
import pyfits
import numpy
from StringIO import StringIO

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("instrument.test")


class TestInstrument(Instrument):
    def __init__(self):
        super(TestInstrument, self).__init__('test', 'cass', ['bias', 'dark'])

    def parser(self, args):
        if args[0] == 'bias':
            return 'bias', 0, None, int(args[1])
        if args[0] == 'dark':
            return 'dark', float(args[2]), None, int(args[1])

o = TestInstrument()

siiill(o)

server = txrServer(('localhost', 9010), allow_none=True, logRequests=False)
server.register_instance(o)

queue1 = o.queue1
queue2 = Queue()
queue3 = Queue()

def main_loop():
    
    _logger.info('Waiting for instrument events')
    while True:
        event = queue1.get()
        _logger.info('Event is %s', event)
        if event[0] == 'store':
		    o.seq.return_image(event)
        else:
            for i in range(event[3]):
                _logger.info('Sending image %d to reader', i)
                queue2.put(event)
	    
def readout():
    while True:
        event = queue2.get()
        _logger.info('Readout image %s', event)
        data = numpy.zeros((10, 10))
        data[3, 3] = 200
        hdu = pyfits.PrimaryHDU(data)
        handle = StringIO()
        hdu.writeto(handle)
        hdub = xmlrpclib.Binary(handle.getvalue())

        event = ('store', hdub)
        queue2.task_done()
        queue1.put(event)
	
# Connect on startup

o.register()

th = []
th.append(threading.Thread(target=main_loop))
th.append(threading.Thread(target=readout))
th.append(threading.Thread(target=server.serve_forever))

for i in th:
    i.start()

for i in th:
    i.join()

o.unregister()
