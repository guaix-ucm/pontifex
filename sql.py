from datetime import datetime
from time import sleep

from sqlalchemy import desc
from sqlalchemy import Table, Column, Integer, String, DateTime, MetaData, ForeignKey, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ObsBlock(Base):
    __tablename__ = 'obsblock'
    obsId = Column(Integer, primary_key=True)
    operator = Column(String(20))
    instrument = Column(String(10))
    mode = Column(String(20))
    start = Column(DateTime)
    end = Column(DateTime)

    def __init__(self, mode):
        self.mode = mode

class Images(Base):
    __tablename__ = 'images'
    imageId = Column(Integer, primary_key=True)
    name = Column(String(10), unique=True, nullable=False)
    exposure = Column(Float)
    imgtype = Column(String(10))
    obsId = Column(Integer,  ForeignKey("obsblock.obsId"))
    stamp = Column(DateTime)
  
    obsblock = relationship(ObsBlock, backref=backref('images', order_by=imageId))

    def __init__(self, name):
        self.name = name
