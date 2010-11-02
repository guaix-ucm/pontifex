from datetime import datetime
from time import sleep

from sqlalchemy import create_engine, desc
from sqlalchemy import Table, Column, Integer, String, DateTime, MetaData, ForeignKey
from sqlalchemy.orm import mapper
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

#engine = create_engine('sqlite:///db', echo=True)
engine = create_engine('sqlite:///db')

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
    stamp = Column(DateTime)
    obsId = Column(Integer,  ForeignKey("obsblock.obsId"))
  
    obsblock = relationship(ObsBlock, backref=backref('images', order_by=imageId))

    def __init__(self, name):
        self.name = name

Base.metadata.create_all(engine) 


Session = sessionmaker(bind=engine)
session = Session()

ob = ObsBlock('test')
ob.instrument = 'emir'
ob.operator = 'Sergio'
ob.start = datetime.utcnow()
session.add(ob)
session.commit()

# query, last image
try:
    name, = session.query(Images.name).order_by(desc(Images.stamp)).first()
except TypeError:
    name = 'r00000.fits'
number = int(name[1:-5]) + 1
# create n = 3 images
n = 3
import time
for i in range(number, number + n):
    img = Images('r%05d.fits' % i)
    time.sleep(1)
    img.stamp = datetime.utcnow()
    ob.images.append(img)

session.commit()

ob.end = datetime.utcnow()
session.commit()
