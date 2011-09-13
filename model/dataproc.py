
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy import Integer, String, DateTime, Float, Binary, Boolean
from sqlalchemy import Table, Column, MetaData, ForeignKey
from sqlalchemy import PickleType, Enum
from sqlalchemy.orm import relationship, backref

from model import DeclarativeBase, metadata, Session

class DataProcessingTask(DeclarativeBase):
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
    method = Column(String(45))
    request = Column(String(45))
    result = Column(String(45))

    children = relationship("DataProcessingTask",
                backref=backref('parent', remote_side=[id]))

class DataProcessing(DeclarativeBase):
    __tablename__ = 'dp_reduction'
    id = Column(Integer, primary_key=True)

    completion_time = Column(DateTime)
    state = Column(Integer, nullable=False)
    task_id = Column(Integer, ForeignKey('dp_task.id'))

class ReductionResult(DeclarativeBase):
    __tablename__ = 'dp_reduction_result'
    id = Column(Integer, primary_key=True)
    state = Column(Integer)
    other = Column(String(45))
    obsres_id = Column(Integer, ForeignKey('observing_result.id'))
    task_id = Column(Integer, ForeignKey('dp_task.id'))
    #picklable = Column(PickleType, nullable=False)

class DataProcessingStatusEnum(DeclarativeBase):
    __tablename__ = 'dp_status_enum'
    id = Column(Integer, primary_key=True)
    status = Column(String(10), nullable=False, unique=True)

class RecipeParameters(DeclarativeBase):
    __tablename__ = 'dp_recipe_parameters'
    id = Column(Integer, primary_key=True)
    mode = Column(String(32), nullable=False)
    #insId = Column(String(10), ForeignKey('instrument.name'))
    parameters = Column(PickleType, nullable=False)


