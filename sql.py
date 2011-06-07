
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

from sqlalchemy import desc
from sqlalchemy import Table, Column, Integer, String, DateTime, MetaData, ForeignKey, Float, Binary
from sqlalchemy.orm import relation, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ObsRun(Base):
    __tablename__ = 'obsrun'
    runId = Column(Integer, primary_key=True)
    piData = Column(String(20))
    start = Column(DateTime)
    status = Column(String(10))
    end = Column(DateTime)

    def __init__(self, pi_data):
        self.piData = pi_data
        self.status = 'IDLE'

class ObsBlock(Base):
    __tablename__ = 'obsblock'
    obsId = Column(Integer, primary_key=True)
    instrument = Column(String(10))
    mode = Column(String(20))
    start = Column(DateTime)
    end = Column(DateTime)
    runId = Column(Integer,  ForeignKey("obsrun.runId"))

    obsrun = relation(ObsRun, backref=backref('obsblock', order_by=obsId))

    def __init__(self, instrument, mode):
        self.instrument = instrument
        self.mode = mode

class Images(Base):
    __tablename__ = 'images'
    imageId = Column(Integer, primary_key=True)
    name = Column(String(10), unique=True, nullable=False)
    exposure = Column(Float)
    imgtype = Column(String(10))
    obsId = Column(Integer,  ForeignKey("obsblock.obsId"))
    stamp = Column(DateTime)
  
    obsblock = relation(ObsBlock, backref=backref('images', order_by=imageId))

    def __init__(self, name):
        self.name = name

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
    status = Column(String(10))
    stamp = Column(DateTime)
    hashdir = Column(String(32))


def get_unprocessed_obsblock(session):
    return session.query(ProcessingBlockQueue)


def get_last_image_index(session):
    try:
        name, = session.query(Images.name).order_by(desc(Images.stamp)).first()
        number = int(name[1:-5]) + 1
    except TypeError:
        number = 0
    return number

