from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from ..models.spot_prices import SpotPrice
from api.awattar.client import Client

def find_missing_dates(session: Session) -> List[datetime.date]:
    """
    Find dates with missing data from last 30 days until end of today or tomorrow.
    If current time is after 14:00, include tomorrow's data.
    
    Args:
        session: SQLAlchemy session

    Returns:
        List of dates with missing data
    """
    now = datetime.now()
    start_date = (now - timedelta(days=30)).date()
    end_date = now.date()
    
    # If after 14:00, include tomorrow
    if now.hour >= 14:
        end_date = (now + timedelta(days=1)).date()

    stmt = text("""
        SELECT DISTINCT date(datetime(start_timestamp, 'unixepoch')) 
        FROM spot_prices 
        WHERE source='awattar' 
        AND start_timestamp >= :start_ts
        AND start_timestamp <= :end_ts
        ORDER BY start_timestamp
    """)
    
    start_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp())
    end_ts = int(datetime.combine(end_date, datetime.max.time()).timestamp())
    
    dates = [row[0] for row in session.execute(stmt, {'start_ts': start_ts, 'end_ts': end_ts})]
    
    date_set = set(dates)
    missing_dates = set()
    
    current = start_date
    while current <= end_date:
        if current.strftime('%Y-%m-%d') not in date_set:
            missing_dates.add(current)
        current += timedelta(days=1)
    
    return sorted(missing_dates)

def find_gaps(session: Session, start_date: datetime, end_date: datetime) -> List[Tuple[datetime, datetime]]:
    """
    Find time periods without data within the specified date range.
    
    Args:
        session: SQLAlchemy session
        start_date: Start of the period to check
        end_date: End of the period to check

    Returns:
        List of (start, end) tuples representing gaps
    """
    timestamps = session.query(SpotPrice.start_timestamp)\
        .filter(SpotPrice.source == 'awattar')\
        .filter(SpotPrice.start_timestamp.between(
            int(start_date.timestamp()),
            int(end_date.timestamp())))\
        .order_by(SpotPrice.start_timestamp).all()
    
    if not timestamps:
        return [(start_date, end_date)]
    
    gaps = []
    timestamps = [datetime.fromtimestamp(t[0]) for t in timestamps]
    
    if timestamps[0] - start_date > timedelta(hours=1):
        gaps.append((start_date, timestamps[0]))
    
    for i in range(len(timestamps)-1):
        if timestamps[i+1] - timestamps[i] > timedelta(hours=1):
            gaps.append((timestamps[i], timestamps[i+1]))
    
    if end_date - timestamps[-1] > timedelta(hours=1):
        gaps.append((timestamps[-1], end_date))
    
    return gaps

def update_db(session: Session, days_back: Optional[int] = 30) -> int:
    """
    Update database with missing price data.
    
    Args:
        session: SQLAlchemy session
        days_back: Number of days to look back for gaps (default: 30)

    Returns:
        Number of prices added
    """
    client = Client()
    total_prices = 0
    
    # First check for completely missing dates
    missing_dates = find_missing_dates(session)
    for date in missing_dates:
        prices = client.fetch_day_prices(date)
        if prices:
            for price in prices:
                spot_price = SpotPrice(
                    start_timestamp=int(price.timestamp.timestamp()),
                    end_timestamp=int(price.timestamp.timestamp()) + 3600,
                    price=price.price,
                    unit='ct/kWh',
                    source='awattar'
                )
                session.merge(spot_price)
                total_prices += 1
            print(f"Added data for {date}: {len(prices)} prices")
            session.commit()
    
    # Then check for gaps in recent data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    gaps = find_gaps(session, start_date, end_date)
    for gap_start, gap_end in gaps:
        prices = client.fetch_day_prices(gap_start.date())
        if prices:
            for price in prices:
                if gap_start <= price.timestamp <= gap_end:
                    spot_price = SpotPrice(
                        start_timestamp=int(price.timestamp.timestamp()),
                        end_timestamp=int(price.timestamp.timestamp()) + 3600,
                        price=price.price,
                        unit='ct/kWh',
                        source='awattar'
                    )
                    session.merge(spot_price)
                    total_prices += 1
            session.commit()
    
    return total_prices

if __name__ == "__main__":
    # For direct script execution
    from sqlalchemy import create_engine
    from config import CONFIG
    
    db_file = CONFIG['db_path'] / CONFIG['db_file']
    engine = create_engine(f'sqlite:///{db_file}')
    
    try:
        db_file = CONFIG['db_path'] / CONFIG['db_file']
        engine = create_engine(f'sqlite:///{db_file}')

        with Session(engine) as session:
            missing_dates = find_missing_dates(session)
            if not missing_dates:
                print("No missing data found")
            else:
                total = update_db(session)
                print(f"Total prices added: {total}")
    except Exception as e:
        print(f"An error occurred: {e}")