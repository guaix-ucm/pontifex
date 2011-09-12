
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy import Integer, String, DateTime, Float, Binary, Boolean
from sqlalchemy import Table, Column, MetaData, ForeignKey
from sqlalchemy import PickleType, Enum
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

from model import DeclarativeBase as Base, metadata, Session

class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    status = Column(Integer, nullable=False)
    usertype = Column(Integer, nullable=False)

class Instrument(Base):
    __tablename__ = 'instrument'
    name = Column(String(10), primary_key=True)
    parameters = Column(PickleType, nullable=False)

    obsruns = relationship("ObservingRun", backref='instrument')
    #recipes = relationship("RecipeParameters", backref="instrument")

class ObservingRun(Base):
    __tablename__ = 'observing_run'
    id = Column(Integer, primary_key=True)
    pi_id = Column(Integer, ForeignKey('users.id'))
    start_time = Column(DateTime, default=datetime.utcnow)
    completion_time = Column(DateTime)
    state = Column(Enum('RUNNING', 'FINISHED'), default='RUNNING')
    instrument_id = Column(Integer,  ForeignKey("instrument.name"), nullable=False)

    obsblocks = relationship("ObservingBlock", backref='obsrun')

class ObservingBlock(Base):
    __tablename__ = 'observing_block'
    id = Column(Integer, primary_key=True)
    observing_mode = Column(String(20), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    completion_time = Column(DateTime)
    obsrun_id = Column(Integer,  ForeignKey("observing_run.id"), nullable=False)
    observer_id = Column(Integer,  ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer,  ForeignKey("observing_task.id"), nullable=False)

    images = relationship("Image", backref='observing_block')

class ObservingResult(Base):
    __tablename__ = 'observing_result'
    id = Column(Integer, primary_key=True)
    observing_mode = Column(String(20), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    completion_time = Column(DateTime)
    obsblock_id = Column(Integer,  ForeignKey("observing_block.id"), nullable=False)
    task_id = Column(Integer,  ForeignKey("observing_task.id"), nullable=False)

    images = relationship("Image", backref='observing_result')


class Image(Base):
    __tablename__ = 'image'
    id = Column(Integer, primary_key=True)
    name = Column(String(10), unique=True, nullable=False)
    exposure = Column(Float, nullable=False)
    imgtype = Column(String(10), nullable=False)
    obsblock_id = Column(Integer,  ForeignKey("observing_result.id"), nullable=False)
    stamp = Column(DateTime, default=datetime.utcnow)

class ProcessingBlockQueue(Base):
    __tablename__ = 'procqueue'
    id = Column(Integer, primary_key=True)
    obsId = Column(Integer, ForeignKey('observing_block.id'))
    status = Column(String(10), default='NEW', nullable=False)

    obsblock = relationship("ObservingBlock", backref=backref("procqueue", uselist=False))

class ObservingTask(Base):
    __tablename__ = 'observing_task'
    id = Column(Integer, primary_key=True)
    state = Column(Integer)
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    start_time = Column(DateTime)
    completion_time = Column(DateTime)
    parent_id = Column(Integer, ForeignKey('observing_task.id'))
    label = Column(String(45))
    waiting = Column(Boolean)
    awaited = Column(Boolean)

    children = relationship("ObservingTask",
                backref=backref('parent', remote_side=[id]))

def get_unprocessed_obsblock(session):
    return session.query(ProcessingBlockQueue)

def get_last_image_index(session):
    try:
        name, = session.query(Image.name).order_by(desc(Image.stamp)).first()
        number = int(name[1:-5]) + 1
    except TypeError:
        number = 0
    return number

