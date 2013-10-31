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

import os
import os.path
import math

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

maker = sessionmaker(autoflush=True, autocommit=False)
Session = scoped_session(maker)

DeclarativeBase = declarative_base()

metadata = DeclarativeBase.metadata

def init_model(engine):
    Session.configure(bind=engine)

_datadir = 'data'
_taskdir = 'task'
_productsdir = 'products'

if not os.path.exists(_datadir):
    os.makedirs(_datadir)

if not os.path.exists(_taskdir):
    os.makedirs(_taskdir)

if not os.path.exists(_productsdir):
    os.makedirs(_productsdir)

datadir = os.path.abspath(_datadir)
taskdir = os.path.abspath(_taskdir)
productsdir = os.path.abspath(_productsdir)

from .sql import ObservingBlock, ObservingRun, Frame, InstrumentConfiguration
from .sql import Instrument, Users, ObservationResult, Channel, ContextDescription, ContextValue
from .dataproc import DataProcessingTask
from .dataproc import ReductionResult, DataProduct, ProcessingSet
from .sql import FITSKeyword, BoolFITSKeyword, StringFITSKeyword
from .sql import IntegerFITSKeyword, FloatFITSKeyword
from .sql import create_fits_keyword
from .sql import Recipe, RecipeConfiguration, ObservingMode, Pipeline
from .sql import PipelineMap
from .sql import get_last_frame_index
