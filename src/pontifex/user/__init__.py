#
# Copyright 2011 Universidad Complutense de Madrid
# 
# This file is part of Pontifex
# 
# Pontifex is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Pontifex is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Pontifex.  If not, see <http://www.gnu.org/licenses/>.
#

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4


import threading
import logging
from xmlrpclib import ServerProxy
import signal
import sys
import ConfigParser

from sqlalchemy import create_engine

from pontifex.txrServer import txrServer
import pontifex.model
from pontifex.host import PontifexHost


# create logger for host
_logger = logging.getLogger("pontifex.host")

def main_host():

    if len(sys.argv) != 2:
        sys.exit(1)

    cfgfile = sys.argv[1]

    config = ConfigParser.ConfigParser()
    config.read(cfgfile)

    masterurl = config.get('master', 'url')
    host = config.get('slave', 'host')
    port = config.getint('slave', 'port')

    im = PontifexHost(masterurl, host, port)

    tserver = txrServer((host, port), allow_none=True, logRequests=False)
    tserver.register_function(im.pass_info)

    # signal handler
    def handler(signum, frame):
        im.quit()
        tserver.shutdown()
        im.doned = True
        sys.exit(0)

    # Set the signal handler on SIGTERM and SIGINT
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    xmls = threading.Thread(target=tserver.serve_forever)
    xmls.start()

    worker = threading.Thread(target=im.worker)
    worker.start()

    while not im.doned:
        signal.pause()

