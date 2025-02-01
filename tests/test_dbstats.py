# tests/test_dbstats.py

from db.models.spot_prices import SpotPrice
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from config import CONFIG
from db.utils import db_stat_timerange, db_check, get_ts
from pathlib import Path
from datetime import datetime
import sys

project_root = Path(__file__).parents[1]
sys.path.append(str(project_root))


def test_db_listvalues(day: datetime, source: str = 'awattar'):
    db_file = CONFIG['db_path'] / CONFIG['db_file']
    engine = create_engine(f'sqlite:///{db_file}')

    with Session(engine) as session:
        # Get start and end timestamps for the specified day
        start_ts = int(datetime(day.year, day.month, day.day).timestamp())
        end_ts = int(datetime(day.year, day.month,
                     day.day, 23, 59, 59).timestamp())

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
                time = datetime.fromtimestamp(
                    price.start_timestamp).strftime('%H:%M')
                print(f"{time}: {price.price:.3f} {price.unit}")
        else:
            print(f"\nNo prices found for {source.upper()} on {day.date()}")


if __name__ == "__main__":
    stats = db_stat_timerange(day=datetime.now(), days=14)
    for stat in stats:
        print(stat)
    check = db_check()

    print(f"DB first day: {check.beginning}")
    print(f"DB last day: {check.end}")

    # If you want all the information:
    year, week, weekday = datetime.now().isocalendar()

    # e.g., "Full info: Year 2025, Week 5, Weekday 6"
    print(f"Full info: Year {year}, Week {week}, Weekday {weekday}")

    start, end = get_ts('week', 2025, week-1)
