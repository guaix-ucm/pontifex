from txrServer import txrServer

import itertools
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

def parser2(args):

    if len(args) < 3:
        _logger.warning('Arguments too short: %s', args)
        return []

    instrument_name = args[0]
    obsmode_name = args[1]
    repeat = int(args[2])


    hed = itertools.repeat(('startobsblock', instrument_name, obsmode_name), 1)

    # No repetition
    mid = itertools.repeat(('nop',), 0)
    if obsmode_name == 'bias':
        mid = itertools.repeat(('expose', dirad[obsmode_name], 0.0, 0), repeat)
    elif obsmode_name == 'dark':
        mid = itertools.repeat(('expose', dirad[obsmode_name], float(args[3]), 0), repeat)
    else:
        _logger.warning('Obsmode %s does not exist', obsmode_name)
        return mid

    tal = itertools.repeat(('endobsblock',), 1)

    return itertools.chain(hed, mid, tal)

def command(args):
    for cmd in parser2(args):       
        queue1.put(cmd)

server = txrServer(('localhost', 9010), allow_none=True, logRequests=False)
server.register_function(command)

def main_loop():
    
    _logger.info('Waiting for instrument commands')
    while True:
        cmd = queue1.get()
        _logger.info('Command is %s', cmd)
        if cmd[0] == 'store':
            # tell the sequencer we want to store an image
            seqserver.return_image(cmd)
        elif cmd[0] == 'storeob':
            # tell the sequencer we want to finish an OB
            seqserver.return_image(cmd)
        elif cmd[0] == 'startobsblock':
            # tell the sequencer we want to start an OB
            seqserver.return_image(cmd)
        elif cmd[0] == 'expose':
            # Sending expose cmd to the detector
            _logger.info('Sending expose command to reader thread')
            queue2.put(cmd)
        elif cmd[0] == 'endobsblock':
            queue2.put(cmd)
        elif cmd[0] == 'nop':
            # do nothing
            pass
        else:
            _logger.warning('Command %s does not exist', cmd[0])
	    
def readout():
    while True:
        cmd = queue2.get()
        if cmd[0] == 'endobsblock':
            queue2.task_done()
            cmd = ('storeob', )
            queue1.put(cmd)
        elif cmd[0] == 'expose':
            _logger.info('Exposing image type=%s, exposure=%6.1f, filter ID=%d', cmd[1], cmd[2], cmd[3])
            _, obsmode, exposure, phfilter = cmd
            time.sleep(exposure)
            data = numpy.zeros((10, 10))
            _logger.info('Readout image')

            # Add headers, etc
            _logger.info('Creating FITS data')
            hdu = pyfits.PrimaryHDU(data, head)
            hdu.header['EXPOSED'] = exposure
            hdu.header['IMGTYP'] = obsmode
            hdu.header['FILTER'] = phfilter
            hdulist = pyfits.HDUList([hdu])

            # Preparing to send binary data back to sequencer
            handle = StringIO()
            hdulist.writeto(handle)
            hdub = xmlrpclib.Binary(handle.getvalue())

            cmd = ('store', hdub)
            queue2.task_done()
            queue1.put(cmd)
        elif cmd[0] == 'nop':
            # do nothing
            pass
        else:
            _logger.warning('Command %s not understood', cmd)
	
th = []
th.append(threading.Thread(target=main_loop))
th.append(threading.Thread(target=readout))
th.append(threading.Thread(target=server.serve_forever))

for i in th:
    i.start()

for i in th:
    i.join()

