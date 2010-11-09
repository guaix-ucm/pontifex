from txrServer import txrServer
from instrument import Instrument, siiill

import time
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

queue1 = Queue()
queue2 = Queue()

seqserver = Server('http://localhost:8010')

cards = [pyfits.Card('EXPOSED', 0, 'Exposure time')]
cards.append(pyfits.Card('IMGTYP', 'NONE', 'Image type'))
cards.append(pyfits.Card('FILTER', '0', 'Filter'))
head = pyfits.Header(cards)

dirad = {'bias': 'BIAS', 'dark': 'DARK'}

def parser1(args):
    if args[1] == 'bias':
        return 'instrument', 'bias', 0, 0, int(args[2])
    elif args[1] == 'dark':
        return 'instrument', 'dark', float(args[3]), 0, int(args[2])
    else:
        return args

class TestInstrument(Instrument):
    def __init__(self):
        super(TestInstrument, self).__init__('test', 'cass', ['bias', 'dark'])

    def parser(self, args):
        if args[0] == 'startobsblock':
            return args
        elif args[0] == 'endobsblock':
            return args
        else:
            return parser1(args)
    
    def command(self, args):
        mandate = self.parser(args)
        queue1.put(mandate)


ti = TestInstrument()

server = txrServer(('localhost', 9010), allow_none=True, logRequests=False)
server.register_instance(ti)

def main_loop():
    
    _logger.info('Waiting for instrument events')
    while True:
        event = queue1.get()
        _logger.info('Event is %s', event)
        if event[0] == 'store':
            # tell the sequencer we want to store an image
            seqserver.return_image(event)
        elif event[0] == 'endobsblock':
            seqserver.return_image(event)
        elif event[0] == 'startobsblock':
            seqserver.return_image(event)
        elif event[0] == 'instrument':
            for i in range(event[4]):
                _logger.info('Sending readout mandate %d to reader thread', i)
                queue2.put(event[:4])
            queue2.put(('endobsblock',))
        else:
            _logger.warning('Mandate %s does not exist', event[0])
	    
def readout():
    while True:
        event = queue2.get()
        if event[0] == 'endobsblock':
            queue2.task_done()
            queue1.put(event)
        elif event[0] == 'instrument':
            _logger.info('Exposing image %s', event)
            obsmode, exposure, phfilter = event
            time.sleep(exposure)
            data = numpy.zeros((10, 10))
            _logger.info('Readout image')

            # Add headers, etc
            hdu = pyfits.PrimaryHDU(data, head)
            hdu.header['EXPOSED'] = exposure
            hdu.header['IMGTYP'] = dirad[obsmode]
            hdu.header['FILTER'] = phfilter
            hdulist = pyfits.HDUList([hdu])

            # Preparing to send binary data back to sequencer
            handle = StringIO()
            hdulist.writeto(handle)
            hdub = xmlrpclib.Binary(handle.getvalue())

            event = ('store', hdub)
            queue2.task_done()
            queue1.put(event)
        else:
            _logger.warning('Command %s not understood', event)
	
th = []
th.append(threading.Thread(target=main_loop))
th.append(threading.Thread(target=readout))
th.append(threading.Thread(target=server.serve_forever))

for i in th:
    i.start()

for i in th:
    i.join()

