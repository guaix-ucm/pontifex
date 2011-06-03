#!/usr/bin/python

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import datetime
import StringIO
import logging
import logging.config
import os.path
import os

import pyfits
import gobject
import dbus
from dbus import SessionBus
from dbus.service import Object, BusName, signal, method
from dbus.mainloop.glib import DBusGMainLoop

from dbins import session, datadir
from sql import ObsRun, ObsBlock, Images, ProcessingBlockQueue, get_last_image_index

logging.config.fileConfig("logging.conf")

# create logger
_logger = logging.getLogger("dbengine")

dbus_loop = DBusGMainLoop()
dsession = SessionBus(mainloop=dbus_loop)

FORMAT = 's%05d.fits'

class DatabaseManager(Object):
    def __init__(self, bus, loop):
        name = BusName('es.ucm.Pontifex.DBengine', bus)
        path = '/es/ucm/Pontifex/DBengine'

        self.loop = loop

        self.index = get_last_image_index(session)
        _logger.info('Last stored image is number %d', self.index)
        _logger.info('Waiting for commands')

        self.obsrun = None
        self.ob = None
        self.props = {}

        super(DatabaseManager, self).__init__(name, path)

    @method(dbus_interface='es.ucm.Pontifex.DBengine')
    def quit(self):
        _logger.info('Ending')
        self.loop.quit()

    @signal(dbus_interface='es.ucm.Pontifex.DBengine', signature='ss')
    def signal_start_obsblock(self, instrument, mode):
        _logger.info('ObsBlock started')

    @signal(dbus_interface='es.ucm.Pontifex.DBengine', signature='su')
    def signal_start_obsrun(self, pidata, runid):
        _logger.info('OsbRun started (runID is %d)', runid)

    @signal(dbus_interface='es.ucm.Pontifex.DBengine', signature='u')
    def signal_end_obsblock(self, runid):
        _logger.info('ObsBlock %d ended', runid)

    @signal(dbus_interface='es.ucm.Pontifex.DBengine', signature='u')
    def signal_end_obsrun(self, runid):
        _logger.info('ObsRun %d ended', runid)


    @method(dbus_interface='es.ucm.Pontifex.DBengine',
            in_signature='s', out_signature='i')
    def start_obsrun(self, pidata):
        ''' Add ObsRun to database
           
            startobsrun pidata
        '''
        if self.obsrun is None:
            _logger.info('Add ObsRun to database')
            self.obsrun = ObsRun(pidata)
            self.obsrun.start = datetime.datetime.utcnow()
            session.add(self.obsrun)
            session.commit()
            runId = self.obsrun.runId
            self.signal_start_obsrun(pidata, runId)
            return runId
        else:
            _logger.info('ObsRun already started')
        return 0

    @method(dbus_interface='es.ucm.Pontifex.DBengine',
            in_signature='ss', out_signature='b')
    def start_obsblock(self, instrument, mode):
        '''Add ObsBlock to database'''
        if self.obsrun is not None:
            if self.ob is None:
                _logger.info('Add ObsBlock to database')
                self.ob = ObsBlock(instrument, mode)
                self.ob.start = datetime.datetime.utcnow()
                self.obsrun.obsblock.append(self.ob)
                session.commit()
                self.signal_start_obsblock(instrument, mode)
                return True
            else:
                _logger.warning('Observing Block already open')
        else:
            _logger.warning('Observing Run not iniatialized')
        return False

    @method(dbus_interface='es.ucm.Pontifex.DBengine',
            in_signature='s', out_signature='')
    def store_file(self, tmpfile):
        _logger.info('Receiving image')
        # Convert binary data back to HDUList
        hdulist = pyfits.open(tmpfile)
        if self.ob is None:
            _logger.warning('Observing block not initialized')
            _logger.info('Saving scratch image')
            # Write to disk
            filename = 'scratch.fits'
            hdulist.writeto(os.path.join(datadir, filename), clobber=True)
        else:
            _logger.info('Storing image %d', self.index)
            # Write to disk
            filename = FORMAT % self.index
            hdulist.writeto(os.path.join(datadir, filename), clobber=True)
            for hdu in hdulist:
                hdu.header['RUN'] = self.index
                hdu.header.update('FILENAME', filename)
            # Update database
            img = Images(filename)
            img.exposure = hdulist[0].header['EXPOSED']
            img.imgtype = hdulist[0].header['IMGTYP']
            img.stamp = datetime.datetime.utcnow()
            self.ob.images.append(img)
            session.commit()
            self.index += 1
        
        del hdulist

        try:
            os.remove(tmpfile)
        except OSError, e:
            _logger.warning(str(e)) 


    @method(dbus_interface='es.ucm.Pontifex.DBengine',
            in_signature='ay', out_signature='', byte_arrays=True)
    def store_image(self, bindata):
        _logger.info('Receiving image')
        # Convert binary data back to HDUList
        handle = StringIO.StringIO(bindata)
        hdulist = pyfits.open(handle)
        if self.ob is None:
            _logger.warning('Observing block not initialized')
            _logger.info('Saving scratch image')
            # Write to disk
            filename = 'scratch.fits'
            hdulist.writeto(os.path.join(datadir, filename), clobber=True)
        else:
            _logger.info('Storing image %d', self.index)
            # Write to disk
            filename = FORMAT % self.index
            hdulist.writeto(os.path.join(datadir, filename), clobber=True)
            # Update database
            img = Images(filename)
            img.exposure = hdulist[0].header['EXPOSED']
            img.imgtype = hdulist[0].header['IMGTYP']
            img.stamp = datetime.datetime.utcnow()
            self.ob.images.append(img)
            session.commit()
            self.index += 1

    @method(dbus_interface='es.ucm.Pontifex.DBengine',
            in_signature='', out_signature='b')
    def end_obsblock(self):
        _logger.info('Received end observing block command')
        if self.ob is not None:
            _logger.info('Update endtime of ObsBlock in database')
            self.ob.end = datetime.datetime.utcnow()
            pbq = ProcessingBlockQueue()
            pbq.obsblock = self.ob
            session.add(pbq) 
            session.commit()
            self.signal_end_obsblock(self.ob.obsId)
            self.ob = None
            return True
        else:
            _logger.warning('Observing Block not iniatialized')
        return False

    @method(dbus_interface='es.ucm.Pontifex.DBengine',
            in_signature='', out_signature='b')
    def end_obsrun(self):
        if self.obsrun is not None:
            _logger.info('Update endtime of ObsRun in database')
            # endobssrun
            self.obsrun.end = datetime.datetime.utcnow()
            self.obsrun.status = 'FINISHED'
            session.commit()
            self.signal_end_obsrun(self.obsrun.runId)
            self.obsrun = None
            return True
        else:
            _logger.info('ObsRun not started')
        return False

    def version(self):
    	return '1.0'

loop = gobject.MainLoop()
gobject.threads_init()

im = DatabaseManager(dsession, loop)
loop.run()

