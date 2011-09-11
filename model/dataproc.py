
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy import Integer, String, DateTime, Float, Binary, Boolean
from sqlalchemy import Table, Column, MetaData, ForeignKey
from sqlalchemy import PickleType, Enum
from sqlalchemy.orm import relationship, backref

from model import DeclarativeBase as Base, metadata, Session

class DataProcessingTask(Base):
    __tablename__ = 'dp_task'
    id = Column(Integer, primary_key=True)
    host = Column(String(45), nullable=False)
    state = Column(Integer)
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    start_time = Column(DateTime)
    completion_time = Column(DateTime)
    parent_id = Column(Integer, ForeignKey('dp_task.id'))
    label = Column(String(45))
    waiting = Column(Boolean)
    awaited = Column(Boolean)

    children = relationship("DataProcessingTask",
                backref=backref('parent', remote_side=[id]))

class DataProcessing(Base):
    __tablename__ = 'dp_reduction'
    id = Column(Integer, primary_key=True)
    #mrb_id = Column(Integer, ForeignKey('observing_task.id'))
    completion_time = Column(DateTime)
    state = Column(Integer, nullable=False)
    task_id = Column(Integer, ForeignKey('dp_task.id'))

class DataProcessingStatusEnum(Base):
    __tablename__ = 'dp_status_enum'
    id = Column(Integer, primary_key=True)
    status = Column(String(10), nullable=False, unique=True)

class RecipeParameters(Base):
    __tablename__ = 'dp_recipe_parameters'
    id = Column(Integer, primary_key=True)
    mode = Column(String(32), nullable=False)
    #insId = Column(String(10), ForeignKey('instrument.name'))
    parameters = Column(PickleType, nullable=False)

