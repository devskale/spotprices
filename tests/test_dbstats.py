# tests/test_dbstats.py
from pathlib import Path
from datetime import datetime
import sys
project_root = Path(__file__).parents[1]
sys.path.append(str(project_root))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from db.models.spot_prices import SpotPrice
from config import CONFIG

def test_db_stats():
    db_file = CONFIG['db_path'] / CONFIG['db_file']
    engine = create_engine(f'sqlite:///{db_file}')
    
    with Session(engine) as session:
        # Get price stats per source
        for source in ['awattar', 'smartenergy']:
            prices = session.query(SpotPrice).filter(SpotPrice.source == source).all()
            
            if prices:
                min_price = min(prices, key=lambda x: x.price)
                max_price = max(prices, key=lambda x: x.price)
                avg_price = sum(p.price for p in prices) / len(prices)
                
                print(f"\n{source.upper()} Stats from DB:")
                print(f"Records: {len(prices)}")
                print(f"Min price: {min_price.price:.3f} {min_price.unit} at {datetime.fromtimestamp(min_price.start_timestamp).strftime('%H:%M')}")
                print(f"Max price: {max_price.price:.3f} {max_price.unit} at {datetime.fromtimestamp(max_price.start_timestamp).strftime('%H:%M')}")
                print(f"Avg price: {avg_price:.3f} {prices[0].unit}")


def test_db_listvalues(day: datetime, source: str = 'awattar'):
    db_file = CONFIG['db_path'] / CONFIG['db_file']
    engine = create_engine(f'sqlite:///{db_file}')
    
    with Session(engine) as session:
        # Get start and end timestamps for the specified day
        start_ts = int(datetime(day.year, day.month, day.day).timestamp())
        end_ts = int(datetime(day.year, day.month, day.day, 23, 59, 59).timestamp())
        
        # Query prices for the specified source and day
        prices = (session.query(SpotPrice)
                 .filter(SpotPrice.source == source)
                 .filter(SpotPrice.start_timestamp >= start_ts)
                 .filter(SpotPrice.start_timestamp <= end_ts)
                 .order_by(SpotPrice.start_timestamp)
                 .all())
        
        if prices:
            print(f"\n{source.upper()} Prices for {day.date()}:")
            for price in prices:
                time = datetime.fromtimestamp(price.start_timestamp).strftime('%H:%M')
                print(f"{time}: {price.price:.3f} {price.unit}")
        else:
            print(f"\nNo prices found for {source.upper()} on {day.date()}")

if __name__ == "__main__":
    test_db_stats()
#    test_db_listvalues(day=datetime.now(), source='awattar')
#    test_db_listvalues(day=datetime.now(), source='smartenergy')
    # pls list all the prices for today from the db
    # for awattar and smartenergy
