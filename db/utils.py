# db/utils.py

import calendar
from config import CONFIG
from db.models.spot_prices import SpotPrice
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class DBCheckResult:
    beginning: datetime = None
    end: datetime = None


@dataclass
class DBStatsResult:
    source: str
    start_ts: int = None
    end_ts: int = None
    min_price: tuple[float, int] = field(
        default=None)  # Tuple (price, timestamp)
    max_price: tuple[float, int] = field(
        default=None)  # Tuple (price, timestamp)
    avg_price: float = None
    records: int = 0


def db_stat_timerange(day: datetime = datetime.today(), days: int = 1) -> list[DBStatsResult]:
    """
    Calculates statistics (min, max, average price, records) for a given time range.

    Args:
        day (datetime, optional): The end date of the range. Defaults to today.
        days (int, optional): The number of days to include in the range (starting from 'day'). Defaults to 1.

    Returns:
        list[DBStatsResult]: A list containing statistics for each source.
    """
    db_file = CONFIG['db_path'] / CONFIG['db_file']
    engine = create_engine(f'sqlite:///{db_file}')
    results = []

    with Session(engine) as session:
        # Calculate start and end timestamps for the specified time range
        start_day = day - timedelta(days=days - 1)
        end_day = day
        start_ts = int(datetime(start_day.year, start_day.month,
                                start_day.day).timestamp())
        end_ts = int(datetime(end_day.year, end_day.month,
                              end_day.day + 1).timestamp())

        for source in ['awattar']:
            prices = (session.query(SpotPrice)
                      .filter(SpotPrice.source == source)
                      .filter(SpotPrice.start_timestamp >= start_ts)
                      .filter(SpotPrice.start_timestamp < end_ts)
                      .all())

            if prices:
                min_price_with_date = min(prices, key=lambda x: x.price)
                max_price_with_date = max(prices, key=lambda x: x.price)

                min_price = (min_price_with_date.price,
                             min_price_with_date.start_timestamp)
                max_price = (max_price_with_date.price,
                             max_price_with_date.start_timestamp)

                avg_price = sum(p.price for p in prices) / len(prices)

                result = DBStatsResult(
                    source=source,
                    start_ts=start_ts,
                    end_ts=end_ts,
                    min_price=min_price,
                    max_price=max_price,
                    avg_price=avg_price,
                    records=len(prices)
                )
                results.append(result)
            else:
                print(f"\nNo prices found for {
                      source.upper()} in the specified period.")

    return results


def db_check(beginning: bool = True, end: bool = True) -> DBCheckResult:
    """
    Retrieves the first and/or last timestamps from the database.

    Args:
        beginning (bool, optional): Whether to retrieve the first timestamp. Defaults to True.
        end (bool, optional): Whether to retrieve the last timestamp. Defaults to True.

    Returns:
        DBCheckResult: An object containing the first and/or last timestamps.
    """
    db_file = CONFIG['db_path'] / CONFIG['db_file']
    engine = create_engine(f'sqlite:///{db_file}')
    result = DBCheckResult()

    with Session(engine) as session:
        if beginning:
            first_price = session.query(SpotPrice).order_by(
                SpotPrice.start_timestamp).first()
            if first_price:
                result.beginning = datetime.fromtimestamp(
                    first_price.start_timestamp)
        if end:
            last_price = session.query(SpotPrice).order_by(
                SpotPrice.start_timestamp.desc()).first()
            if last_price:
                result.end = datetime.fromtimestamp(last_price.start_timestamp)
    return result


def get_ts(timespan: str, year: int = None, period: int = None) -> tuple[float, float]:
    """
    Get start and end timestamps for various time periods.

    Args:
        timespan (str): Type of timespan - 'day', 'week', or 'month'
        year (int, optional): Year for calculation. Defaults to current year.
        period (int, optional): Period number - day of month for 'day',
                              week number for 'week', month number for 'month'.
                              Defaults to current period.

    Returns:
        tuple: (start_timestamp, end_timestamp)

    Examples:
        get_ts('day', 2025, 1)     # Jan 1, 2025
        get_ts('week', 2025, 1)    # First week of 2025
        get_ts('month', 2025, 1)   # January 2025
        get_ts('day')              # Current day
    """
    today = datetime.now()
    year = year or today.year

    if timespan == 'day':
        if period:  # Specific day of current month
            date = datetime(year, today.month, period)
        else:
            date = today
        start = datetime(date.year, date.month, date.day)
        end = start + timedelta(days=1) - timedelta(microseconds=1)

    elif timespan == 'week':
        # Current week if not specified
        period = period or today.isocalendar()[1]
        start = datetime.strptime(f'{year}-W{period:02d}-1', '%Y-W%W-%w')
        end = start + timedelta(days=7) - timedelta(microseconds=1)

    elif timespan == 'month':
        period = period or today.month  # Current month if not specified
        start = datetime(year, period, 1)
        last_day = calendar.monthrange(year, period)[1]
        end = datetime(year, period, last_day, 23, 59, 59, 999999)

    else:
        raise ValueError("timespan must be 'day', 'week', or 'month'")

    return start.timestamp(), end.timestamp()
