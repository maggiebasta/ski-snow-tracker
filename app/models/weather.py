from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SnowReport(Base):
    __tablename__ = "snow_reports"
    
    id = Column(Integer, primary_key=True)
    resort_name = Column(String)
    state = Column(String)
    timestamp = Column(DateTime)
    snow_depth = Column(Float)  # in inches
    new_snow_24h = Column(Float)  # in inches
    new_snow_72h = Column(Float)  # in inches
    new_snow_7d = Column(Float)   # in inches
    elevation = Column(Float)     # in feet
    temperature = Column(Float)   # in Fahrenheit
    data_source = Column(String)  # 'SNOTEL' or 'WeatherUnlocked'
