from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
    
from sql import Base

engine = create_engine('sqlite:///operation.db', echo=False)
Base.metadata.create_all(engine) 
Session = sessionmaker(bind=engine)
session = Session()
