# tests/test_chart.py
from pathlib import Path
import sys
from datetime import datetime, timedelta
project_root = Path(__file__).parents[1]
sys.path.append(str(project_root))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from db.models.spot_prices import SpotPrice
from config import CONFIG

# tests/test_chart.py
def print_chart(prices, width=80, height=15):
    prices_sorted = sorted(prices, key=lambda x: x.start_timestamp)
    min_price = 0
    max_price = max(p.price for p in prices)
    price_range = max_price - min_price
    
    chart = []
    for i in range(height):
        row = []
        price_level = max_price - (i * price_range / (height - 1))
        for p in prices_sorted:
            if abs(p.price - price_level) < price_range / (2 * height):
                row.append('*')
            else:
                row.append(' ')
        chart.append(row)
    
    print("\nPrice Chart (ct/kWh):")
    for i, row in enumerate(chart):
        price_label = f"{max_price - (i * price_range / (height - 1)):5.2f}"
        print(f"{price_label} |{''.join(row)}")
    
    # Print time axis with ticks
    time_axis = '      +'
    for i in range(len(prices_sorted)):
        dt = datetime.fromtimestamp(prices_sorted[i].start_timestamp)
        if dt.hour == 0 and dt.minute == 0:
            time_axis += '|'
        else:
            time_axis += '-'
    print(time_axis)
    
    # Print day names aligned with vertical bars
    day_line = '       '
    for i, p in enumerate(prices_sorted):
        dt = datetime.fromtimestamp(p.start_timestamp)
        if dt.hour == 0 and dt.minute == 0:
            day_line += dt.strftime('%a')
        else:
            day_line += ' ' * (i - len(day_line) + 7)
    print(day_line)


# tests/test_chart.py
def show_last_days(days=2):
    db_file = CONFIG['db_path'] / CONFIG['db_file']
    engine = create_engine(f'sqlite:///{db_file}')
    
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    end_time = datetime.combine(tomorrow, datetime.max.time())
    start_time = datetime.combine(today - timedelta(days=days), datetime.min.time())
    
    with Session(engine) as session:
        stmt = select(SpotPrice).where(
            SpotPrice.start_timestamp >= int(start_time.timestamp()),
            SpotPrice.start_timestamp <= int(end_time.timestamp()),
            SpotPrice.source == 'awattar'
        ).order_by(SpotPrice.start_timestamp)
        
        prices = session.execute(stmt).scalars().all()
        
        if prices:
            print(f"\nShowing Awattar prices from {start_time.date()} to {end_time.date()}")
            print_chart(prices)
        else:
            print("No data found for the specified period")


if __name__ == "__main__":
    show_last_days()