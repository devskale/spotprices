# tests/test_database.py
from pathlib import Path
from datetime import datetime
project_root = Path(__file__).parents[1]
import sys
sys.path.append(str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from db.models.spot_prices import Base, SpotPrice
from db.operations.spot_prices import save_prices, get_day_prices
from api.awattar.client import Client as AwattarClient
from api.smartenergy.client import Client as SmartEnergyClient
from config import CONFIG

def test_db():
    CONFIG['db_path'].mkdir(exist_ok=True)
    db_file = CONFIG['db_path'] / CONFIG['db_file']
    
    engine = create_engine(f'sqlite:///{db_file}', echo=True)
    Base.metadata.create_all(engine)
    
    awattar = AwattarClient()
    smart = SmartEnergyClient()
    
    prices_a = awattar.fetch_day_prices()
    prices_s = smart.fetch_day_prices()
    
    with Session(engine) as session:
        save_prices(session, prices_a, awattar.source, awattar.unit)
        save_prices(session, prices_s, smart.source, smart.unit)
        
        today = datetime.now()
        db_prices_a = get_day_prices(session, today, 'awattar')
        db_prices_s = get_day_prices(session, today, 'smartenergy')
        
        print(f"\nStored Awattar prices: {len(db_prices_a)}")
        print(f"Stored SmartEnergy prices: {len(db_prices_s)}")

if __name__ == "__main__":
    test_db()