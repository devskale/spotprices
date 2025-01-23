# db/models/spot_prices.py
from sqlalchemy import create_engine, Table, Column, Integer, Float, String, MetaData, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class SpotPrice(Base):
    __tablename__ = 'spot_prices'
    
    start_timestamp = Column(Integer, primary_key=True)
    source = Column(String, primary_key=True)
    end_timestamp = Column(Integer)
    price = Column(Float)
    unit = Column(String)