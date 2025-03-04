import pandas as pd
from sqlalchemy import text
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta

from db.database import get_db_engine


def get_spot_price_data(start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> pd.DataFrame:
    """
    Retrieve spot price data from the database within the specified date range.

    Args:
        start_date: Optional start date for filtering data
        end_date: Optional end date for filtering data

    Returns:
        DataFrame containing timestamp and price data
    """
    engine = get_db_engine()

    # Build query based on date filters
    query = """
    SELECT timestamp, price 
    FROM spot_prices
    """

    conditions = []
    params = {}

    if start_date:
        conditions.append("timestamp >= :start_date")
        params['start_date'] = start_date

    if end_date:
        conditions.append("timestamp <= :end_date")
        params['end_date'] = end_date

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY timestamp"

    # Execute query and return as DataFrame
    with engine.connect() as connection:
        result = connection.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())

    return df


def get_latest_spot_price_data(days: int = 365) -> pd.DataFrame:
    """
    Retrieve the most recent spot price data for the specified number of days.

    Args:
        days: Number of days of data to retrieve

    Returns:
        DataFrame containing timestamp and price data
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    return get_spot_price_data(start_date, end_date)
