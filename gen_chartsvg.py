from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from db.models.spot_prices import SpotPrice
from config import CONFIG
import math

def gen_chart_svg(startday, endday, output_file='price_chart.svg'):
    db_file = CONFIG['db_path'] / CONFIG['db_file']
    engine = create_engine(f'sqlite:///{db_file}')
    
    start_time = datetime.combine(startday, datetime.min.time())
    end_time = datetime.combine(endday, datetime.max.time())
    
    with Session(engine) as session:
        stmt = select(SpotPrice).where(
            SpotPrice.start_timestamp >= int(start_time.timestamp()),
            SpotPrice.start_timestamp <= int(end_time.timestamp()),
            SpotPrice.source == 'awattar'
        ).order_by(SpotPrice.start_timestamp)
        
        prices = session.execute(stmt).scalars().all()
        
        if not prices:
            print("No data found for the specified period")
            return

        timestamps = [datetime.fromtimestamp(p.start_timestamp) for p in prices]
        values = [p.price for p in prices]
        
        width = 800
        height = 400
        padding = 50
        plot_width = width - 2 * padding
        plot_height = height - 2 * padding
        
        min_price = min(0, min(values))
        max_price = max(values)
        
        # Round min/max to nearest 10 cents
        min_price = math.floor(min_price / 10) * 10
        max_price = math.ceil(max_price / 10) * 10
        price_range = max_price - min_price
        
        svg_content = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        .grid {{ stroke: gray; stroke-width: 0.5; opacity: 0.3; stroke-dasharray: 4,4; }}
        .grid-midnight {{ stroke: gray; stroke-width: 1; opacity: 0.5; }}
        .axis {{ stroke: black; stroke-width: 1; }}
        .price-line {{ stroke: #268358; stroke-width: 2; fill: none; }}
        .price-area {{ fill: #268358; opacity: 0.1; }}
        .axis-text {{ font-family: Arial; font-size: 12px; }}
        .title {{ font-family: Arial; font-size: 16px; font-weight: bold; }}
    </style>
    
    <!-- Title -->
    <text x="{width/2}" y="25" text-anchor="middle" class="title">
        Spot Tarif stündlich EPEXAT (ct/kWh)
    </text>
'''
        
        # Generate grid lines for even numbers
        step = 10  # 10 cents steps
        for price in range(math.floor(min_price/step)*step, math.ceil(max_price/step)*step + step, step):
            y = padding + plot_height * (1 - (price - min_price) / price_range)
            svg_content += f'''    <line class="grid" x1="{padding}" y1="{y}" x2="{width-padding}" y2="{y}" />
    <text class="axis-text" x="{width-padding+5}" y="{y+5}" text-anchor="start">{price:.0f}</text>
'''

        # Time axis labels
        time_interval = timedelta(hours=12)
        current_time = timestamps[0]
        while current_time <= timestamps[-1]:
            x = padding + plot_width * (current_time - timestamps[0]).total_seconds() / (timestamps[-1] - timestamps[0]).total_seconds()
            if current_time.hour == 0:
                svg_content += f'''    <line class="grid-midnight" x1="{x}" y1="{padding}" x2="{x}" y2="{height-padding}" />'''
            elif current_time.hour == 12:
                svg_content += f'''    <line class="grid" x1="{x}" y1="{padding}" x2="{x}" y2="{height-padding}" />'''
            
            # Add day name in the middle of each day
            if current_time.hour == 12:
                svg_content += f'''    <text class="axis-text" x="{x}" y="{height-padding+20}" text-anchor="middle">
        {current_time.strftime('%A')}
    </text>
'''
            current_time += time_interval

        # Generate price line
        line_points = []
        area_points = []
        for i, (ts, val) in enumerate(zip(timestamps, values)):
            x = padding + plot_width * (ts - timestamps[0]).total_seconds() / (timestamps[-1] - timestamps[0]).total_seconds()
            y = padding + plot_height * (1 - (val - min_price) / price_range)
            line_points.append(f"{x},{y}")
            area_points.append(f"{x},{y}")
            
        base_y = padding + plot_height * (1 - (0 - min_price) / price_range)
        area_points.append(f"{padding + plot_width},{base_y}")
        area_points.append(f"{padding},{base_y}")
        
        svg_content += f'''    <path class="price-area" d="M {' L '.join(area_points)} Z" />
    <path class="price-line" d="M {' L '.join(line_points)}" />
</svg>'''

        with open(output_file, 'w') as f:
            f.write(svg_content)
        
        print(f"Chart saved to {output_file}")

if __name__ == "__main__":
    today = datetime.now().date()
    gen_chart_svg(today - timedelta(days=1), today + timedelta(days=1))