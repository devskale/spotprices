from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.models.spot_prices import SpotPrice
from api.awattar.client import Client
from db.utils import get_engine

# How many days back to check for missing data (including tomorrow for preview)
CATCHUP_DAYS = 3


def get_existing_dates(session):
    """Get set of dates that already have data."""
    stmt = text("SELECT DISTINCT date(datetime(start_timestamp, 'unixepoch')) FROM spot_prices WHERE source='awattar'")
    return set(row[0] for row in session.execute(stmt))


def update_db():
    """Update database with missing spot prices.
    
    Only fills the last CATCHUP_DAYS from today backwards.
    Does NOT attempt to fill historical gaps - live with holes in the data.
    """
    engine = get_engine()
    client = Client()

    with Session(engine) as session:
        existing_dates = get_existing_dates(session)
        today = datetime.now().date()
        total_added = 0

        # Build list of dates to check: today + CATCHUP_DAYS back + tomorrow (if after 2pm)
        dates_to_check = []
        for i in range(CATCHUP_DAYS):
            dates_to_check.append(today - timedelta(days=i))
        
        # Add tomorrow if it's after 2pm (Awattar publishes next day prices after ~1pm)
        if datetime.now().hour >= 14:
            dates_to_check.append(today + timedelta(days=1))

        # Filter to only missing dates
        missing_dates = [
            d for d in dates_to_check 
            if d.strftime('%Y-%m-%d') not in existing_dates
        ]

        if not missing_dates:
            print("No missing dates in the catch-up window")
            return 0

        print(f"Catch-up: checking {len(dates_to_check)} days, found {len(missing_dates)} missing")

        for date in sorted(missing_dates):
            try:
                prices = client.fetch_day_prices(date)
                if not prices:
                    print(f"No data available for {date}")
                    continue
                    
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
            except Exception as e:
                print(f"Error fetching {date}: {e}")
                continue

        return total_added
