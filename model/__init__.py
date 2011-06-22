import os
import os.path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
    
from sql import Base

#engine = create_engine('sqlite:///operation.db', echo=False)
engine = create_engine('sqlite:///devdata.db', echo=True)
Base.metadata.create_all(engine) 
Session = sessionmaker(bind=engine)
session = Session()

_datadir = 'data'

if not os.path.exists(_datadir):
    os.makedirs(_datadir)

datadir = os.path.abspath(_datadir)


from sql import ObsBlock, ObsRun, ObsBlock, Images, ProcessingBlockQueue, DataProcessing
from sql import RecipeParameters
from sql import get_last_image_index, get_unprocessed_obsblock
