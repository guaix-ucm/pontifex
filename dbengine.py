from txrServer import txrServer
from dbins import session
from sql import ObsBlock, Images, lastindex

import datetime
import StringIO
import pyfits
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
    def startobsblock(self, args):
        _logger.info('Received start observing block command')
        queue1.put(('startobsblock',) + tuple(args))

    def store_image(self, args):
        _logger.info('Received store image command')
        queue1.put(args)

    def endobsblock(self):
        _logger.info('Received end observing block command')
        queue1.put(('endobsblock',))

    def version(self):
    	return '1.0'

im = DatabaseManager()

FORMAT = 's%05d.fits'

ob = None

def store_image(bindata, index):
    # Convert binary data back to HDUList
    handle = StringIO.StringIO(bindata)
    hdulist = pyfits.open(handle)
    # Write to disk
    filename = FORMAT % index
    hdulist.writeto('data/' + filename, clobber=True)
    # Update database
    img = Images(filename)
    img.exposure = hdulist[0].header['EXPOSED']
    img.imgtype = hdulist[0].header['IMGTYP']
    img.stamp = datetime.datetime.utcnow()
    ob.images.append(img)
    session.commit()

def manager():
    global queue1
    global ob
    index = lastindex(session)
    _logger.info('Last stored image is number %d', index)
    _logger.info('Waiting for commands')
    while True:
        cmd = queue1.get()
        if cmd[0] == 'store':
            _logger.info('Storing image %d', index)
            store_image(cmd[1], index)
            index += 1
        elif cmd[0] == 'startobsblock':
            # Add ObsBlock to database
            _logger.info('Add ObsBlock to database')
            ob = ObsBlock(cmd[2])
            ob.instrument = cmd[1]
            ob.operator = 'Sergio'
            ob.start = datetime.datetime.utcnow()
            session.add(ob)
            session.commit()
        elif cmd[0] == 'endobsblock':
            _logger.info('Update endtime of ObsBlock in database')
            ob.end = datetime.datetime.utcnow()
            session.commit()    
            ob = None
        else:
            _logger.warning('Command %s does not exist', cmd[0])


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

