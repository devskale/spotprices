# tests/test_gentle_fetch.py
from pathlib import Path
from datetime import datetime, date, timedelta
import sys
import time
project_root = Path(__file__).parents[1]
sys.path.append(str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from db.models.spot_prices import Base, SpotPrice
from db.operations.spot_prices import save_prices
from api.awattar.client import Client
from config import CONFIG

def fetch_day_data(start: int = 0, end: int = 0):
    client = Client()
    db_file = CONFIG['db_path'] / CONFIG['db_file']
    engine = create_engine(f'sqlite:///{db_file}')
    
    today = date.today()
    start_date = today - timedelta(days=start)
    end_date = today - timedelta(days=end)
    
    with Session(engine) as session:
        current_date = start_date
        while current_date <= end_date:
            try:
                prices = client.fetch_day_prices(current_date)
                if prices:
                    save_prices(session, prices, client.source, client.unit)
                    print(f"Stored {len(prices)} prices for {current_date}")
                else:
                    print(f"No data available for {current_date}")
                time.sleep(1)  # Be gentle with the API
            except Exception as e:
                print(f"Error fetching data for {current_date}: {e}")
                break
            current_date = current_date + timedelta(days=1)

if __name__ == "__main__":
    fetch_day_data(start=5, end=2)
