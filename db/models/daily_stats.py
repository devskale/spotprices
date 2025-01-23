class DailyStats(Base):
    __tablename__ = 'daily_stats'
    
    date = Column(String, primary_key=True)
    source = Column(String, primary_key=True)
    min_price = Column(Float)
    min_time = Column(String)
    max_price = Column(Float)
    max_time = Column(String)
    avg_price = Column(Float)
    data_points = Column(Integer)