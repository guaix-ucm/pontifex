import os
import os.path

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

if not os.path.exists(_datadir):
    os.makedirs(_datadir)

datadir = os.path.abspath(_datadir)

from sql import ObservingBlock, ObservingRun, Image, ProcessingBlockQueue
from sql import ObservingTask, Instrument, Users, ObservingResult
from dataproc import RecipeParameters, DataProcessingTask, DataProcessing
from dataproc import ReductionResult
from sql import get_last_image_index, get_unprocessed_obsblock
