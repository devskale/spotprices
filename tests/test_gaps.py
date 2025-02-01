from config import CONFIG
from api.awattar.client import Client
from db.models.spot_prices import Base, SpotPrice
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from pathlib import Path
import sys
from datetime import datetime, timedelta
from sqlalchemy import text

project_root = Path(__file__).parents[1]
sys.path.append(str(project_root))


# tests/test_gaps.py
def find_missing_dates(session):
    stmt = text("SELECT DISTINCT date(datetime(start_timestamp, 'unixepoch')) FROM spot_prices WHERE source='awattar' ORDER BY start_timestamp")
    dates = [row[0] for row in session.execute(stmt)]

    today = datetime.now().date()
    if not dates:
        return [today]

    date_set = set(dates)
    missing_dates = set()

    # Get missing dates between first record and today + 1 (for potential tomorrow data)
    start = datetime.strptime(dates[0], '%Y-%m-%d').date()
    end = max(datetime.strptime(
        dates[-1], '%Y-%m-%d').date(), today + timedelta(days=1))

    current = start
    while current <= end:
        if current.strftime('%Y-%m-%d') not in date_set:
            missing_dates.add(current)
        current += timedelta(days=1)

    return sorted(missing_dates)


def update_db():
    db_file = CONFIG['db_path'] / CONFIG['db_file']
    engine = create_engine(f'sqlite:///{db_file}')
    client = Client()

    with Session(engine) as session:
        missing_dates = find_missing_dates(session)
        total_added = 0

        print(f"Found {len(missing_dates)} missing dates")
        for date in missing_dates:

            # Only try to fetch tomorrow if its past 2pm
            if date == datetime.now().date() + timedelta(days=1):
                if datetime.now().hour < 14:
                    print(f"Skipping {date}, it is not yet 2pm")
                    continue
            prices = client.fetch_day_prices(date)
            for price in prices:
                spot_price = SpotPrice(
                    start_timestamp=int(price.timestamp.timestamp()),
                    end_timestamp=int(price.timestamp.timestamp()) + 3600,
                    price=price.price,
                    unit='ct/kWh',
                    source='awattar'
                )
                session.merge(spot_price)
                total_added += 1
            session.commit()
            print(f"Added data for {date}: {len(prices)} prices")

        return total_added


if __name__ == "__main__":
    total = update_db()
    print(f"Total prices added: {total}")
