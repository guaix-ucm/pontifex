#
# Copyright 2011-2012 Universidad Complutense de Madrid
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

import argparse
import logging
from xmlrpclib import ServerProxy

# create logger for CLI
_logger = logging.getLogger("pontifex.cli")

def main():

    masterurl = 'http://127.0.0.1:7081'

    rserver = ServerProxy(masterurl)

    def run(args):
        oid = args.id, 
        pset = args.pset
        for id_ in oid:
            print id_, pset
            rserver.run(id_, pset)

    def pset_create(args):
        print 'Create pset with name %s for instrument %s' % (args.name, args.instrument)
        rserver.pset_create(args.name, args.instrument)

    def usage(args, parser):
        parser.print_help()



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

if __name__ == '__main__':
    main()

