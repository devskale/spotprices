# db/operations/spot_prices.py
from sqlalchemy.orm import Session
from datetime import datetime
from ..models.spot_prices import SpotPrice
from api.models import PriceData

def save_prices(session: Session, prices: list[PriceData], source: str, unit: str):
    for price in prices:
        spot_price = SpotPrice(
            start_timestamp=int(price.timestamp.timestamp()),
            end_timestamp=int(price.timestamp.timestamp()) + 3600,
            price=price.price,
            unit=unit,
            source=source
        )
        session.merge(spot_price)
    session.commit()

def get_day_prices(session: Session, day: datetime, source: str = None):
    start = int(day.replace(hour=0, minute=0, second=0).timestamp())
    end = int(day.replace(hour=23, minute=59, second=59).timestamp())
    
    query = session.query(SpotPrice).filter(
        SpotPrice.start_timestamp >= start,
        SpotPrice.start_timestamp <= end
    )
    
    if source:
        query = query.filter(SpotPrice.source == source)
        
    return query.all()