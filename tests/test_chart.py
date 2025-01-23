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

def print_chart(prices, width=80, height=15):
    if not prices:
        return
    
    prices_sorted = sorted(prices, key=lambda x: x.start_timestamp)
    min_price = 0  # Start at 0 ct/kWh
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
    
    # Print time axis
    time_axis = '      +'+ '-' * len(prices_sorted)
    print(time_axis)
    
    # Get days and their positions
    days = []
    for i, p in enumerate(prices_sorted):
        dt = datetime.fromtimestamp(p.start_timestamp)
        if dt.hour == 0 and dt.minute == 0:
            days.append((i, dt.strftime('%a')))
    
    # Print day markers
    day_line = ' ' * 7
    for pos, day in days:
        day_line = day_line[:pos+7] + day + day_line[pos+10:]
    print(day_line)

if __name__ == "__main__":
    show_last_days()