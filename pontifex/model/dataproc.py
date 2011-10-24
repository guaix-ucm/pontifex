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
    state = Column(Integer)
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

class ReductionResult(DeclarativeBase):
    __tablename__ = 'dp_reduction_result'
    id = Column(Integer, primary_key=True)
    state = Column(Integer)
    # TODO: these two fields aren't necessary
    other = Column(String(45))
    obstree_node_id = Column(Integer, ForeignKey('observing_tree.id'))
    task_id = Column(Integer, ForeignKey('dp_task.id'))
    
    task = relationship("DataProcessingTask", backref='rresult', uselist=False)

class Recipe(DeclarativeBase):
    __tablename__ = 'dp_recipe'
    # The PrimaryKeyConstraint is equivalente to put primary_key=True
    # in several columns
    __table_args__ = (PrimaryKeyConstraint('instrument_id', 'module', 'create_event'),
                        UniqueConstraint('instrument_id', 'mode', 'module', 'active'),
                        CheckConstraint('(active IS NULL AND revoke_event IS NOT NULL) OR (active IS NOT NULL and revoke_event IS NULL)'))                                   

    instrument_id = Column(String(10),  ForeignKey("instrument.name"), nullable=False)
    mode = Column(String(45), nullable=False)
    module = Column(String(255), nullable=False)
# versioning (borrowed from koji schema)
    create_event = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    revoke_event = Column(TIMESTAMP)
    active = Column(Boolean, nullable=True)

    instrument = relationship("Instrument", backref='recipes')

class RecipeConfiguration(DeclarativeBase):
    __tablename__ = 'dp_recipe_configuration'
    # The PrimaryKeyConstraint is equivalente to put primary_key=True
    # in several columns
    __table_args__ = (PrimaryKeyConstraint('instrument_id', 'module', 'create_event'),
                        UniqueConstraint('instrument_id', 'module', 'active'),
                        ForeignKeyConstraint(['instrument_id', 'module'], ['dp_recipe.instrument_id', 'dp_recipe.module']),
                        CheckConstraint('(active IS NULL AND revoke_event IS NOT NULL) OR (active IS NOT NULL and revoke_event IS NULL)'))                                   

    instrument_id = Column(String(10),  ForeignKey("instrument.name"), nullable=False)

    module = Column(String(255), nullable=False)
    parameters = Column(PickleType, nullable=False)
    description = Column(String(255))
# versioning (borrowed from koji schema)
    create_event = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    revoke_event = Column(TIMESTAMP)
    active = Column(Boolean, nullable=True)

    instrument = relationship("Instrument", backref='recipe_configurations')


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
    instrument_id = Column(String(10), ForeignKey('instrument.name'), primary_key=True, nullable=False)
    name = Column(String(50), primary_key=True, nullable=False)







