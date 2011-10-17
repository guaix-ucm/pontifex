#
# Copyright 2008-2011 Sergio Pascual
# 
# This file is part of Numina
# 
# Numina is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Numina is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Numina.  If not, see <http://www.gnu.org/licenses/>.
# 

'''User command line interface of Numina.'''

import datetime
import logging.config
import os
from optparse import OptionParser
from ConfigParser import SafeConfigParser
from ConfigParser import Error as CPError
from logging import captureWarnings
from pkgutil import get_data
import StringIO
import xdg.BaseDirectory as xdgbd
import json
import importlib

from numina import __version__, ObservingResult, FitsEncoder
from numina.recipes import list_recipes, init_recipe_system, find_recipe

_logger = logging.getLogger("numina")

def parse_cmdline(args=None):
    '''Parse the command line.'''
    usage = "usage: %prog [options] recipe [recipe-options]"

    version_line = '%prog ' + __version__ 

    parser = OptionParser(usage=usage, version=version_line, 
                          description=__doc__)
    # Command line options
    parser.set_defaults(mode="none")
    parser.add_option('-d', '--debug', action="store_true", 
                      dest="debug", default=False, 
                      help="make lots of noise [default]")
    parser.add_option('-l', action="store", dest="logging", metavar="FILE", 
                      help="FILE with logging configuration")
    parser.add_option('--module', action="store", dest="module", 
                      metavar="FILE", help="FILE")
    parser.add_option('--list', action="store_const", const='list', 
                      dest="mode")
    parser.add_option('--run', action="store_const", const='run', 
                      dest="mode")
    parser.add_option('--basedir', action="store", dest="basedir", 
                      default=os.getcwd())
    parser.add_option('--resultsdir', action="store", dest="resultsdir")
    parser.add_option('--workdir', action="store", dest="workdir")
    
    parser.add_option('--cleanup', action="store_true", dest="cleanup", 
                      default=False)
    # Stop when you find the first argument
    parser.disable_interspersed_args()
    (options, args) = parser.parse_args(args)
    return (options, args)

def mode_list():
    '''Run the list mode of Numina'''
    _logger.debug('list mode')
    for recipeclass in list_recipes():
        print recipeclass
    
def mode_none():
    '''Do nothing in Numina.'''
    pass

# FIXME: this code or part of this code is repeated in
# numina/__init__.py and pontifex/process.py
# it should be unified
def mode_run(args, options):
    # json decode

    with open(args[0], 'r') as fd:
        task_control = json.load(fd)
    
    ins_pars = {}

    if 'instrument' in task_control:
        _logger.info('file contains instrument config')
        ins_pars = task_control['instrument']
    if 'observing_result' in task_control:
        _logger.info('file contains observing result')
        obsres = ObservingResult()
        obsres.__dict__ = task_control['observing_result']

    if 'reduction' in task_control:
        params = task_control['reduction']['parameters']
        
    _logger.info('our instrument is %(instrument)s and our observing mode is %(mode)s', 
                obsres.__dict__)
    try:
        entry_point = find_recipe(obsres.instrument, obsres.mode)
        _logger.info('entry point is %s', entry_point)
    except ValueError:
        _logger.warning('cannot find entry point for %(instrument)s and %(mode)s', obsres.__dict__)
        raise

    mod, klass = entry_point.split(':')

    module = importlib.import_module(mod)
    RecipeClass = getattr(module, klass)

    parameters = {}
    for req in RecipeClass.__requires__:
        _logger.info('recipe requires %s', req.tag)
        if req.tag in params:
            _logger.debug('parameter %s has value %s', req.tag, params[req.tag])
            parameters[req.tag] = params[req.tag]
        elif req.default is not None:
            _logger.debug('parameter %s has defaulr value %s', req.tag, req.defaulr)
            parameters[req.tag] = req.default
        else:
            _logger.error('parameter %s must be defined', req.tag)
            raise ValueError

    for req in RecipeClass.__provides__:
        _logger.info('recipe provides %s', req.tag)
    
    # Creating base directory for storing results
    
    workdir = options.workdir
    resultsdir = options.resultsdir
               
    _logger.debug('Creating the recipe')
            
    runinfo = {}
    runinfo['workdir'] = workdir
    runinfo['resultsdir'] = resultsdir
    runinfo['entrypoint'] = entry_point
            
    recipe = RecipeClass()

    recipe.configure(parameters=parameters, runinfo=runinfo, instrument=ins_pars)
            
    base = os.getcwd()

    _recipe_logger = logging.getLogger('%(instrument)s.recipes' % obsres.__dict__)

    _recipe_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Set custom logger
    fh = logging.FileHandler('%s/processing.log' % resultsdir)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(_recipe_formatter)

    _recipe_logger.addHandler(fh)

    try:
        # Running the recipe
        _logger.debug('Running recipe')
        os.chdir(base)
        os.chdir(workdir)

        result = recipe(obsres)
             
        result['recipe_runner'] = info()
        result['runinfo'] = runinfo
    
        os.chdir(base)
        os.chdir(resultsdir)

        with open('result.json', 'w+') as fd:
            json.dump(result, fd, indent=1, cls=FitsEncoder)
    
        with open('result.json', 'r') as fd:
            result = json.load(fd)

        import shutil
        if options.cleanup:
            _logger.debug('Cleaning up the workdir')
            os.chdir(base)
            shutil.rmtree(workdir)
    finally:
        _recipe_logger.removeHandler(fh)
    return 0

def info():
    '''Information about this version of numina.
    
    This information will be stored in the result object of the recipe
    '''
    return dict(name='numina', version=__version__)

def main(args=None):
    '''Entry point for the Numina CLI.'''        
    # Configuration options from a text file    
    config = SafeConfigParser()
    # Default values, it must exist
   
    #config.readfp(StringIO.StringIO(get_data('numina','defaults.cfg')))

    # Custom values, site wide and local
    config.read(['.numina/numina.cfg', 
                 os.path.join(xdgbd.xdg_config_home, 'numina/numina.cfg')])
    
    # The cmd line is parsed
    options, args = parse_cmdline(args)

    # After processing both the command line and the files
    # we get the values of everything

    # logger file
    if options.logging is None:
        # This should be a default path in defaults.cfg
        try:
            options.logging = config.get('numina', 'logging')
        except CPError:
            options.logging = StringIO.StringIO(get_data('numina','logging.ini'))

    logging.config.fileConfig(options.logging)
    
    logger = logging.getLogger("numina")
    
    _logger.info('Numina simple recipe runner version %s', __version__)
    
#    if options.module is None:
#        options.module = config.get('numina', 'module')
    
#    init_recipe_system([options.module])
    import sys
    sys.path.append('/home/spr/devel/pontifex')
    init_recipe_system(['clodia', 'emir', 'megara', 'frida'])
    captureWarnings(True)
    
    if options.basedir is None:
        options.basedir = os.getcwd()
    else:
        options.basedir = os.path.abspath(options.basedir)    
    
    if options.workdir is None:
        options.workdir = os.path.abspath(os.path.join(options.basedir, 'work'))
    else:
        options.workdir = os.path.abspath(options.workdir)
                
    if options.resultsdir is None:
        options.resultsdir = os.path.abspath(os.path.join(options.basedir, 'results'))
    else:
        options.resultsdir = os.path.abspath(options.resultsdir)
    
    if options.mode == 'list':
        mode_list() 
        return 0
    elif options.mode == 'none':
        mode_none()
        return 0
    elif options.mode == 'run':

        # Check basedir exists
        if not os.path.exists(options.basedir):
            os.mkdir(options.basedir)

        
        # Check workdir exists
        if not os.path.exists(options.workdir):
            os.mkdir(options.workdir)
        # Check resultdir exists
        if not os.path.exists(options.resultsdir):
            os.mkdir(options.resultsdir)
        
        return mode_run(args, options)
    
if __name__ == '__main__':
    main()
