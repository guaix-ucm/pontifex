from txrServer import txrServer
from user import session
from sql import ObsBlock, Images

import StringIO
import pyfits
import time
import random
from SimpleXMLRPCServer import SimpleXMLRPCServer
from time import sleep
import threading
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
        _logger.info('Received storage command')
        queue1.put(args)

    def version(self):
    	return '1.0'

im = DatabaseManager()

FORMAT = 's%05d.fits'

index = 0

def store_image(bindata):
    global index
    # Convert to HDUList
    handle = StringIO.StringIO(bindata)
    hdulist = pyfits.open(handle)
    # Write to disk
    filename = FORMAT % index
    hdulist.writeto('data/' + filename, clobber=True)
    index += 1
    # Update database
    img = Images(filename)
    img.exposure = 0#exposure
    img.imgtype = 0#obsmode
    img.stamp = 0 #datetime.utcnow()
    #ob.images.append(img)
    session.commit()

def manager():
    global queue1
    _logger.info('Waiting for events')
    while True:
        mandate = queue1.get()
        if mandate[0] == 'store':
            _logger.info('Storing image')
            store_image(mandate[1])
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

