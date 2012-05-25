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

import time
import threading
import logging
from Queue import Queue
from xmlrpclib import ServerProxy
import os.path
from datetime import datetime
import signal
import sys
import uuid
import ConfigParser
import shutil

import yaml
from sqlalchemy import create_engine
from numina.user import run_recipe_from_file
from numina.pipeline import init_pipeline_system
from numina.serialize import lookup as lookup_serializer

import pontifex.process as process
from pontifex.txrServer import txrServer
import pontifex.model
from pontifex.model import Session, productsdir
from pontifex.model import ObservingBlock, Instrument, ProcessingSet
from pontifex.model import ContextDescription, ContextValue
from pontifex.model import DataProcessingTask, ReductionResult, DataProduct
from pontifex.server import PontifexServer
from pontifex.host import PontifexHost

# create logger
_logger_s = logging.getLogger("pontifex.server")

# Processing tasks STATES
CREATED, COMPLETED, ENQUEUED, PROCESSING, FINISHED, ERROR = range(6)

# create logger for host
_logger = logging.getLogger("pontifex.host")

# FIXME: global variables
sdum = None
sload = None

def main_cli():

    masterurl = 'http://127.0.0.1:7081'

    rserver = ServerProxy(masterurl)

    def run(args):
        oid = args.id, 
        pset = args.pset
        for id in oid:
            print id, pset
            rserver.run(id, pset)

    def pset_create(args):
        print 'Create pset with name %s for instrument %s' % (args.name, args.instrument)
        rserver.pset_create(args.name, args.instrument)

    def usage(args, parser):
        parser.print_help()

    import argparse

    parser = argparse.ArgumentParser(description='Pontifex command line utility',
                                     prog='pontifex',
                                     epilog="For detailed help pass " \
                                               "--help to a target")

    # Verbosity
    parser.add_argument('-v', action='store_true',
                        help='Run with verbose debug output')
    parser.add_argument('-q', action='store_true',
                        help='Run quietly only displaying errors')

    # Add a subparsers object to use for the actions
    subparsers = parser.add_subparsers(title='Targets',
                                       description='These are valid commands you can ask pontifex to do.')

    # Set up the various actions
    # Add help to -h and --help
    parser_help = subparsers.add_parser('help', help='Show usage')
    parser_help.set_defaults(command=lambda args: usage(args, parser=parser))

    # Add a common parser to be used as a parent
    parser_build_common = subparsers.add_parser('common',
                                                add_help=False)
    # run target
    parser_run = subparsers.add_parser('run',
                                         help='Request reduction',
                                         parents=[parser_build_common],
                                         description='This command \
                                         requests a reduction of a particular \
                                         observing block to be performed.')

    parser_run.add_argument('id', action='store', type=int,
                              help='Id of the observing block')

    parser_run.add_argument('-s', dest='pset', default='default',
                              help='Name of the processing set')

    parser_run.set_defaults(command=run)
    
    # pset target
    parser_pset = subparsers.add_parser('pset',
                                         help='Handle processing sets',
                                         parents=[parser_build_common],
                                         description='This command \
                                         helps to handle \
                                         processing sets.')




    # Add a subparsers object to use for the actions
    subparsers_pset = parser_pset.add_subparsers(title='Processing Set Targets',
                                       description='These are valid commands you can ask pontifex pset to do.')

    # pset create target
    parser_pset_create = subparsers_pset.add_parser('create',
                                         help='Create processing set',
                                         parents=[parser_build_common],
                                         description='This command \
                                         creates a \
                                         processing set.')

    parser_pset_create.add_argument('name', action='store', type=str,
                              help='Name of the processing set')
    parser_pset_create.add_argument('instrument', action='store', type=str,
                              help='Instrument of the processing set')
    parser_pset_create.set_defaults(command=pset_create)

    val = parser.parse_args()

    #val.command(val.id, val.pset)
    val.command(val)

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

def main_server():

    logging.config.fileConfig("logging.ini")

    df_server = ServerProxy('http://127.0.0.1:7080')

    engine = create_engine('sqlite:///devdata.db', echo=False)
    #engine = create_engine('sqlite:///devdata.db', echo=True)
    engine.execute('pragma foreign_keys=on')

    pontifex.model.init_model(engine)
    pontifex.model.metadata.create_all(engine)

    im = PontifexServer()

    tserver = txrServer(('localhost', 7081), allow_none=True, logRequests=False)
    tserver.register_function(im.register)
    tserver.register_function(im.unregister)
    tserver.register_function(im.receiver)
    tserver.register_function(im.version)
    tserver.register_function(im.run)
    tserver.register_function(im.pset_create)

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

    POLL = 5
    _logger_s.info('polling database for new ProcessingTasks every %d seconds', POLL)
    timer = threading.Thread(target=im.watchdog, args=(POLL, ), name='timer')
    timer.start()

    inserter = threading.Thread(target=im.inserter, name='inserter')
    inserter.start()

    consumer = threading.Thread(target=im.consumer, name='consumer')
    consumer.start()

    while not im.doned:
        signal.pause()
