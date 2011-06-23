
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy import Integer, String, DateTime, Float, Binary
from sqlalchemy import Table, Column, MetaData, ForeignKey
from sqlalchemy import PickleType, Enum
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Instruments(Base):
    __tablename__ = 'instruments'
    name = Column(String(10), primary_key=True)
    parameters = Column(PickleType, nullable=False)
    obsblocks = relationship("ObsBlock", backref='instrument')
    recipes = relationship("RecipeParameters", backref="instrument")

class ObsRun(Base):
    __tablename__ = 'obsrun'
    id = Column(Integer, primary_key=True)
    piData = Column(String(20))
    start = Column(DateTime, default=datetime.utcnow)
#    status = Column(String(10), default='RUNNING')
    status = Column(Enum('RUNNING', 'FINISHED'), default='RUNNING')
    end = Column(DateTime)
    obsblocks = relationship("ObsBlock", backref='obsrun')

class ObsBlock(Base):
    __tablename__ = 'obsblock'
    id = Column(Integer, primary_key=True)
    insId = Column(Integer,  ForeignKey("instruments.name"), nullable=False)
    mode = Column(String(20), nullable=False)
    start = Column(DateTime, default=datetime.utcnow, nullable=False)
    end = Column(DateTime)
    runId = Column(Integer,  ForeignKey("obsrun.id"), nullable=False)

    images = relationship("Images", backref='obsblock')

class Images(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True)
    name = Column(String(10), unique=True, nullable=False)
    exposure = Column(Float, nullable=False)
    imgtype = Column(String(10), nullable=False)
    obsId = Column(Integer,  ForeignKey("obsblock.id"), nullable=False)
    stamp = Column(DateTime, default=datetime.utcnow)

class ProcessingBlockQueue(Base):
    __tablename__ = 'procqueue'
    id = Column(Integer, primary_key=True)
    obsId = Column(Integer, ForeignKey('obsblock.id'))
    status = Column(String(10), default='NEW', nullable=False)

    obsblock = relationship("ObsBlock", backref=backref("procqueue", uselist=False))

class DataProcessing(Base):
    __tablename__ = 'dataprocessing'
    processingId = Column(Integer, primary_key=True)
    obsId = Column(Integer, ForeignKey('obsblock.id'))
    obsblock = relationship("ObsBlock", backref=backref("dataprocessing", uselist=False))
    status = Column(Integer, ForeignKey('dp_status_enum.id'), default=1)
    st_enum = relationship("DataProcessingStatusEnum")
    stamp = Column(DateTime)
    hashdir = Column(String(32))
    host = Column(String(128))

class DataProcessingStatusEnum(Base):
    __tablename__ = 'dp_status_enum'
    id = Column(Integer, primary_key=True)
    status = Column(String(10), nullable=False, unique=True)

class RecipeParameters(Base):
    __tablename__ = 'dp_recipe_parameters'
    id = Column(Integer, primary_key=True)
    mode = Column(String(32), nullable=False)
    insId = Column(String(10), ForeignKey('instruments.name'))
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

