# tests/check_today.py
from pathlib import Path
import sys
from datetime import datetime, timedelta
from sqlalchemy import text

project_root = Path(__file__).parents[1]
sys.path.append(str(project_root))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from db.models.spot_prices import SpotPrice
from config import CONFIG

def check_today():
    db_file = CONFIG['db_path'] / CONFIG['db_file']
    engine = create_engine(f'sqlite:///{db_file}')
    
    with Session(engine) as session:
        today = datetime.now().date()
        start = int(datetime.combine(today, datetime.min.time()).timestamp())
        end = int(datetime.combine(today, datetime.max.time()).timestamp())
        
        stmt = select(SpotPrice).where(
            SpotPrice.source == 'awattar',
            SpotPrice.start_timestamp >= start,
            SpotPrice.start_timestamp <= end
        ).order_by(SpotPrice.start_timestamp)
        
        prices = session.execute(stmt).scalars().all()
        
        print(f"Today's data ({today}):")
        print(f"Number of prices: {len(prices)}")
        if prices:
            last_time = datetime.fromtimestamp(prices[-1].start_timestamp)
            print(f"Last timestamp: {last_time}")
            
            if len(prices) < 24:
                print("Missing some hourly data!")
                first_time = datetime.fromtimestamp(prices[0].start_timestamp)
                print(f"Time range: {first_time} to {last_time}")

if __name__ == "__main__":
    check_today()