
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy import Integer, String, DateTime, Float, Binary
from sqlalchemy import Table, Column, MetaData, ForeignKey
from sqlalchemy import PickleType
from sqlalchemy.orm import relation, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ObsRun(Base):
    __tablename__ = 'obsrun'
    runId = Column(Integer, primary_key=True)
    piData = Column(String(20))
    start = Column(DateTime, default=datetime.utcnow)
    status = Column(String(10), default='running')
    end = Column(DateTime)

class ObsBlock(Base):
    __tablename__ = 'obsblock'
    obsId = Column(Integer, primary_key=True)
    instrument = Column(String(10), nullable=False)
    mode = Column(String(20), nullable=False)
    start = Column(DateTime, default=datetime.utcnow)
    end = Column(DateTime)
    runId = Column(Integer,  ForeignKey("obsrun.runId"))

    obsrun = relation(ObsRun, backref=backref('obsblock', order_by=obsId))

class Images(Base):
    __tablename__ = 'images'
    imageId = Column(Integer, primary_key=True)
    name = Column(String(10), unique=True, nullable=False)
    exposure = Column(Float, nullable=False)
    imgtype = Column(String(10), nullable=False)
    obsId = Column(Integer,  ForeignKey("obsblock.obsId"))
    stamp = Column(DateTime, default=datetime.utcnow)
  
    obsblock = relation(ObsBlock, backref=backref('images', order_by=imageId))

class ProcessingBlockQueue(Base):
    __tablename__ = 'procqueue'
    pblockId = Column(Integer, primary_key=True)
    obsId = Column(Integer, ForeignKey('obsblock.obsId'))
    obsblock = relation("ObsBlock", backref=backref("procqueue", uselist=False))
    status = Column(String(10), default='NEW')

class DataProcessing(Base):
    __tablename__ = 'dataprocessing'
    processingId = Column(Integer, primary_key=True)
    obsId = Column(Integer, ForeignKey('obsblock.obsId'))
    obsblock = relation("ObsBlock", backref=backref("dataprocessing", uselist=False))
    status = Column(Integer, ForeignKey('dp_status_enum.dpenumId'), default=1)
    st_enum = relation("DataProcessingStatusEnum")
    stamp = Column(DateTime)
    hashdir = Column(String(32))
    host = Column(String(128))

class DataProcessingStatusEnum(Base):
    __tablename__ = 'dp_status_enum'
    dpenumId = Column(Integer, primary_key=True)
    status = Column(String(10), nullable=False, unique=True)

class RecipeParameters(Base):
    __tablename__ = 'dp_recipe_parameters'
    instrument = Column(String(32), primary_key=True)
    mode = Column(String(32), primary_key=True)
    parameters = Column(PickleType, nullable=False)

def get_unprocessed_obsblock(session):
    return session.query(ProcessingBlockQueue)

def get_last_image_index(session):
    try:
        name, = session.query(Images.name).order_by(desc(Images.stamp)).first()
        number = int(name[1:-5]) + 1
    except TypeError:
        number = 0
    return number

