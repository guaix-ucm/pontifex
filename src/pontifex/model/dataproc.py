#
# Copyright 2011 Universidad Complutense de Madrid
# 
# This file is part of Pontifex
# 
# Pontifex is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Pontifex is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Pontifex.  If not, see <http://www.gnu.org/licenses/>.
#

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

from datetime import datetime

from sqlalchemy import UniqueConstraint, PrimaryKeyConstraint, CheckConstraint, ForeignKeyConstraint
from sqlalchemy import Integer, String, DateTime, Boolean, TIMESTAMP
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import PickleType
from sqlalchemy.orm import relationship, backref

from . import DeclarativeBase

class DataProcessingTask(DeclarativeBase):
    __tablename__ = 'dp_task'
    id = Column(Integer, primary_key=True)
    host = Column(String(45))
    state = Column(Integer, default=0)
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    start_time = Column(DateTime)
    completion_time = Column(DateTime)
    obstree_node_id = Column(Integer, ForeignKey('observing_tree.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('dp_task.id'))
    label = Column(String(45))
    waiting = Column(Boolean)
    awaited = Column(Boolean)
    method = Column(String(45))
    request = Column(String(45))
    result = Column(String(45))

    obstree_node = relationship("ObservingTree", backref='tasks')

    children = relationship("DataProcessingTask",
                backref=backref('parent', remote_side=[id]))

# sqlite trigger to update task.state when observing_tree.state changes

#CREATE TRIGGER update_task_state UPDATE OF state ON observing_tree
#  BEGIN
#    UPDATE dp_task SET state = 1 WHERE (obstree_node_id = old.id) and (new.state = 2);
#  END;

class ReductionResult(DeclarativeBase):
    __tablename__ = 'dp_reduction_result'
    id = Column(Integer, primary_key=True)
    state = Column(Integer)
    # TODO: these two fields aren't necessary
    other = Column(String(45))
    obstree_node_id = Column(Integer, ForeignKey('observing_tree.id'))
    task_id = Column(Integer, ForeignKey('dp_task.id'))
    
    task = relationship("DataProcessingTask", backref='rresult', uselist=False)

data_product_context = Table(
    'data_product_context', DeclarativeBase.metadata,
    Column('data_product_id', Integer, ForeignKey('dp_product.id'), primary_key=True),
    Column('context_id', Integer, ForeignKey('context_value.id'), primary_key=True)
    )

class DataProduct(DeclarativeBase):
    __tablename__ = 'dp_product'
    __table_args__ = (ForeignKeyConstraint(['instrument_id', 'pset_name'], ['dp_set.instrument_id', 'dp_set.name']), )
    id = Column(Integer, primary_key=True)
    
    datatype = Column(String(45))
    reference = Column(String(45))
    result_id = Column(Integer, ForeignKey('dp_reduction_result.id'))
    instrument_id = Column(String(10), ForeignKey('instrument.name'), nullable=False)
    pset_name = Column(String(50), nullable=False)

    result = relationship("ReductionResult", backref='data_product')
    context = relationship('ContextValue', secondary='data_product_context', backref='data_product')

class ProcessingSet(DeclarativeBase):
    __tablename__ = 'dp_set'
    __table_args__ = (UniqueConstraint('instrument_id', 'name'), )
    id = Column(Integer, primary_key=True)
    instrument_id = Column(String(10), ForeignKey('instrument.name'), nullable=False)
    name = Column(String(50), nullable=False)
