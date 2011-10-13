#
# Copyright 2011 Sergio Pascual
# 
# This file is part of Pontifex
# 
# Pontifex is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# PyEmir is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with PyEmir.  If not, see <http://www.gnu.org/licenses/>.
#

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy import Integer, String, DateTime, Float, Binary, Boolean
from sqlalchemy import Table, Column, MetaData, ForeignKey
from sqlalchemy import PickleType, Enum
from sqlalchemy.orm import relationship, backref

from pontifex.model import DeclarativeBase, metadata, Session

class DataProcessingTask(DeclarativeBase):
    __tablename__ = 'dp_task'
    id = Column(Integer, primary_key=True)
    host = Column(String(45))
    state = Column(Integer)
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    start_time = Column(DateTime)
    completion_time = Column(DateTime)
    or_id = Column(Integer, ForeignKey('observing_result.id'))
    parent_id = Column(Integer, ForeignKey('dp_task.id'))
    label = Column(String(45))
    waiting = Column(Boolean)
    awaited = Column(Boolean)
    method = Column(String(45))
    request = Column(String(45))
    result = Column(String(45))

    observing_result = relationship("ObservingResult",
                backref=backref('tasks'))

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

class RecipeParameters(DeclarativeBase):
    __tablename__ = 'dp_recipe_parameters'
    id = Column(Integer, primary_key=True)
    mode = Column(String(32), nullable=False)
    #insId = Column(String(10), ForeignKey('instrument.name'))
    parameters = Column(PickleType, nullable=False)

data_product_context = Table(
    'data_product_context', DeclarativeBase.metadata,
    Column('data_product_id', Integer, ForeignKey('dp_product.id'), primary_key=True),
    Column('context_id', Integer, ForeignKey('context_value.id'), primary_key=True)
    )

class DataProduct(DeclarativeBase):
    __tablename__ = 'dp_product'
    id = Column(Integer, primary_key=True)
    instrument_id = Column(String(10), ForeignKey("instrument.name"), nullable=False)
    datatype = Column(String(45))
    reference = Column(String(45))
    task_id = Column(Integer, ForeignKey('dp_task.id'))

    task = relationship("DataProcessingTask", backref=backref('product'))
    context = relationship('ContextValue', secondary='data_product_context', backref='data_product')
