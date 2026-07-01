from datetime import datetime, timedelta
from typing import List, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..models.spot_prices import SpotPrice

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
    if not dates:
        return [now.date()]
    
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


if __name__ == "__main__":
    # For direct script execution
    from sqlalchemy import create_engine
    from config import CONFIG

    db_file = CONFIG['db_path'] / CONFIG['db_file']
    engine = create_engine(f'sqlite:///{db_file}')

    try:
        with Session(engine) as session:
            missing_dates = find_missing_dates(session)
            if not missing_dates:
                print("No missing data found")
            else:
                print(f"Missing dates: {missing_dates}")
    except Exception as e:
        print(f"An error occurred: {e}")
