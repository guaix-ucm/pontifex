#
# Copyright 2011 Sergio Pascual
# 
# This file is part of Pontifex
# 
# Pontifex is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# PyEmir is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with PyEmir.  If not, see <http://www.gnu.org/licenses/>.
#

import importlib

def find_recipe(instrument, mode):
    base = 'numina.recipes.%s' % instrument
    try:
        mod = importlib.import_module(base)
    except ImportError:
        msg = 'No instrument %s' % instrument
        raise ValueError(msg)

    try:
        repmod = mod.find_recipe(mode)
    except KeyError:
        msg = 'No recipe for mode %s' % mode
        raise ValueError(msg)
        
    return '%s.%s' % (base, repmod)

def find_parameters(recipe_name):
    # query somewhere for the precomputed parameters
    return {}
