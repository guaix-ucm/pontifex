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

from sqlalchemy import UniqueConstraint, ForeignKeyConstraint, PrimaryKeyConstraint, CheckConstraint, desc
from sqlalchemy import Integer, String, DateTime, Float, Boolean, TIMESTAMP
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import PickleType, Enum
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm import validates


from pontifex.model import DeclarativeBase

class Users(DeclarativeBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    status = Column(Integer, nullable=False)
    usertype = Column(Integer, nullable=False)

class Channel(DeclarativeBase):
    __tablename__ = 'channel'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)

class Instrument(DeclarativeBase):
    __tablename__ = 'instrument'
    name = Column(String(10), primary_key=True)

    obsruns = relationship("ObservingRun", backref='instrument')

    processing_sets = relationship("ProcessingSet", backref='instrument')

    valid_configuration = relationship("InstrumentConfiguration",
                    uselist=False,
                    primaryjoin="and_           (Instrument.name==InstrumentConfiguration.instrument_id, "
                            "InstrumentConfiguration.active==True)")

class InstrumentConfiguration(DeclarativeBase):
    __tablename__ = 'instrument_configuration'
    # The PrimaryKeyConstraint is equivalente to put primary_key=True
    # in several columns
    __table_args__ = (PrimaryKeyConstraint('instrument_id', 'create_event'),
                        UniqueConstraint('instrument_id', 'active'),
                        CheckConstraint('(active IS NULL AND revoke_event IS NOT NULL) OR (active IS NOT NULL and revoke_event IS NULL)'))                                   

    instrument_id = Column(String(10),  ForeignKey("instrument.name"), nullable=False)
    parameters = Column(PickleType, nullable=False)
    description = Column(String(255))
# versioning (borrowed from koji schema)
    create_event = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    revoke_event = Column(TIMESTAMP)
    active = Column(Boolean, nullable=True)

    instrument = relationship("Instrument", backref='configurations')

class ObservingMode(DeclarativeBase):    
    __tablename__ = 'observing_modes'
    __table_args__ = (UniqueConstraint('instrument_id', 'key'),)                    
    
    Id = Column(Integer, primary_key=True)
    name = Column(String)
    key = Column(String)
    instrument_id = Column(String(10),  ForeignKey("instrument.name"), nullable=False)
    module = Column(String(255), ForeignKey("recipe.module"), unique=True, nullable=False)

    instrument = relationship("Instrument", backref='observing_modes')

class Recipe(DeclarativeBase):
    __tablename__ = 'recipe'                                   

    module = Column(String(255), primary_key=True)
    
    configurations = relationship("RecipeConfiguration", backref='recipe')
    
class RecipeConfiguration(DeclarativeBase):
    __tablename__ = 'recipe_configuration'
    # The PrimaryKeyConstraint is equivalent to put primary_key=True
    # in several columns
    __table_args__ = (PrimaryKeyConstraint('module', 'pset_id'),)
                                                           
    module = Column(String(255), ForeignKey("recipe.module"), nullable=False)
    parameters = Column(PickleType, nullable=False)
    pset_id = Column(Integer, ForeignKey("dp_set.id"), nullable=False)
    description = Column(String(255))
    
    processing_set = relationship("ProcessingSet")

class ObservingRun(DeclarativeBase):
    __tablename__ = 'observing_run'
    id = Column(Integer, primary_key=True)
    pi_id = Column(Integer, ForeignKey('users.id'))
    start_time = Column(DateTime, default=datetime.utcnow)
    completion_time = Column(DateTime)
    state = Column(Enum('RUNNING', 'FINISHED'), default='RUNNING')
    instrument_id = Column(String(10),  ForeignKey("instrument.name"), nullable=False)

    obsblocks = relationship("ObservingBlock", backref='obsrun')

class ObservingBlock(DeclarativeBase):
    __tablename__ = 'observing_block'
    id = Column(Integer, primary_key=True)
    observing_mode = Column(String(20), nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    start_time = Column(DateTime)
    completion_time = Column(DateTime)
    object = Column(String(80), nullable=False)
    obsrun_id = Column(Integer,  ForeignKey("observing_run.id"), nullable=False)
    observer_id = Column(Integer,  ForeignKey("users.id"), nullable=False)
    observing_tree_root_id = Column(Integer,  ForeignKey("observing_tree.id"), nullable=False)

    observing_tree = relationship("ObservingTree", backref=backref('observing_block', uselist=False))
    #observer = relationship("Users", backref='observed_obs')
    observer = relationship("Users")

class ObservingTree(DeclarativeBase):
    __tablename__ = 'observing_tree'
    id = Column(Integer, primary_key=True)
    state = Column(Integer)    
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    start_time = Column(DateTime)
    completion_time = Column(DateTime)
    parent_id = Column(Integer, ForeignKey('observing_tree.id'))
    #observing_block_id = Column(Integer, ForeignKey("observing_block.id", use_alter=True, name="fk2"), nullable=False)
    mode = Column(String(45), nullable=False)
    label = Column(String(45))
    waiting = Column(Boolean)
    awaited = Column(Boolean)

    children = relationship("ObservingTree",
                backref=backref('parent', remote_side=[id]))
    
    context = relationship('ContextValue', secondary='observing_tree_context', backref='observing_tree')

    frames = relationship("Frame", backref='observing_tree')

    #observing_block = relationship("ObservingBlock")

    # approach based on ORM validation
    @validates('state')
    def update_state(self, key, value):
        if value == 2:
            for task in self.tasks:
                if task.state == 0:
                    task.state = 1
        return value

# trigger based on sqlite
# http://stackoverflow.com/questions/7888846/trigger-in-sqlachemy

#update_task_state = DDL('''\
#CREATE TRIGGER update_task_state UPDATE OF state ON observing_tree
#  BEGIN
#    UPDATE dp_task SET state = 1 WHERE (obstree_node_id = old.id) and (new.state = 2);
#  END;''')

#event.listen(ObservingTree.__table__, 'after_create', update_task_state)

class Frame(DeclarativeBase):
    __tablename__ = 'frame'
    id = Column(Integer, primary_key=True)
    name = Column(String(10), unique=True, nullable=False)
    object = Column(String(100), nullable=False)
    exposure = Column(Float, nullable=False)
    imgtype = Column(String(10), nullable=False)
    racoor = Column(Float, nullable=False)
    deccoor = Column(Float, nullable=False)
    stamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    obstree_id = Column(Integer,  ForeignKey("observing_tree.id"), nullable=False)

class ContextDescription(DeclarativeBase):
    __tablename__ = 'context_description'
    __table_args__ = (UniqueConstraint('instrument_id', 'name'), )

    id = Column(Integer, primary_key=True)
    instrument_id = Column(String(10), ForeignKey("instrument.name"), nullable=False)
    name = Column(String(250), nullable=False)
    description = Column(String(250))

    @property
    def together(self):
        return '%s.%s' % (self.instrument_id, self.name)

observing_tree_context = Table(
    'observing_tree_context', DeclarativeBase.metadata,
    Column('observing_tree_id', Integer, ForeignKey('observing_tree.id'), primary_key=True),
    Column('context_id', Integer, ForeignKey('context_value.id'), primary_key=True)
    )

class ContextValue(DeclarativeBase):
    __tablename__ = 'context_value'

    id = Column(Integer, primary_key=True)
    description_id = Column(Integer, ForeignKey("context_description.id"), nullable=False)
    value = Column(String(250), nullable=False)

    definition = relationship("ContextDescription", backref=backref("values"),  collection_class=attribute_mapped_collection('together'))

def get_last_frame_index(session):
    number = 0
    try:
        name, = session.query(Frame.name).order_by(desc(Frame.stamp)).first()
        number = int(name[1:-5]) + 1
    except TypeError:
        number = 1
    return number

