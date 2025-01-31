from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from db.models.spot_prices import SpotPrice
from config import CONFIG
import math


def gen_chart_svg(startday, endday, output_file='price_chart.svg', minmaxdot=False):
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

        timestamps = [datetime.fromtimestamp(
            p.start_timestamp) for p in prices]
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
        .axis-text {{ font-family: Arial; font-size: 12px; }}
        .title {{ font-family: Arial; font-size: 16px; font-weight: bold; }}
        .min-dot {{ fill: #0066cc; }}
        .max-dot {{ fill: #cc0000; }}
        .dot-label {{ font-family: Arial; font-size: 11px; }}
        .brand-card {{ fill: white; stroke: #ddd; stroke-width: 1; rx: 4; }}
        .brand-text {{ font-family: Arial; font-size: 10px; fill: #666; }}
    </style>
    <!-- Gradient definition -->
    <linearGradient id="priceGradient" gradientUnits="userSpaceOnUse" x1="0" y1="50" x2="0" y2="350">
      <stop offset="0%" stop-color="#C2E4C9" stop-opacity="1"/>  <!-- Lighter Green -->
      <stop offset="60%" stop-color="#C2E4C9" stop-opacity="0.2"/> <!-- Softer transition -->
      <stop offset="100%" stop-color="#C2E4C9" stop-opacity="0.0"/> <!-- Transparent -->
    </linearGradient>
    <!-- Title -->
    <text x="{width/2}" y="25" text-anchor="middle" class="title">
        Spot Tarif stündlich EPEXAT
    </text>

    <!-- Y-axis label -->
    <text x="{width-padding+25}" y="{padding-20}" text-anchor="middle" class="axis-text">
        ct/kWh
    </text>'''

        # Generate grid lines for even numbers
        step = 10  # 10 cents steps
        for price in range(math.floor(min_price/step)*step, math.ceil(max_price/step)*step + step, step):
            y = padding + plot_height * (1 - (price - min_price) / price_range)
            svg_content += f'''
    <line class="grid" x1="{padding}" y1="{y}" x2="{width-padding}" y2="{y}" />
    <text class="axis-text" x="{width-padding+5}" y="{y+5}" text-anchor="start">{price:.0f}</text>'''

        # Time axis labels
        time_interval = timedelta(hours=12)
        current_time = timestamps[0]
        while current_time <= timestamps[-1]:
            x = padding + plot_width * (current_time - timestamps[0]).total_seconds() / (
                timestamps[-1] - timestamps[0]).total_seconds()
            if current_time.hour == 0:
                svg_content += f'''
    <line class="grid-midnight" x1="{x}" y1="{padding}" x2="{x}" y2="{height-padding}" />'''
            elif current_time.hour == 12:
                svg_content += f'''
    <line class="grid" x1="{x}" y1="{padding}" x2="{x}" y2="{height-padding}" />'''

            # Add day name and date in the middle of each day
            if current_time.hour == 12:
                date_str = current_time.strftime('%d.%m.')
                weekday = current_time.strftime('%A')
                weekday_de = {
                    'Monday': 'Montag',
                    'Tuesday': 'Dienstag',
                    'Wednesday': 'Mittwoch',
                    'Thursday': 'Donnerstag',
                    'Friday': 'Freitag',
                    'Saturday': 'Samstag',
                    'Sunday': 'Sonntag'
                }[weekday]

                svg_content += f'''
    <text class="axis-text" x="{x}" y="{height-padding+15}" text-anchor="middle">{weekday_de}</text>
    <text class="axis-text" x="{x}" y="{height-padding+30}" text-anchor="middle">{date_str}</text>'''

            current_time += time_interval

        # Generate price line
        line_points = []
        area_points = []
        for i, (ts, val) in enumerate(zip(timestamps, values)):
            x = padding + plot_width * \
                (ts - timestamps[0]).total_seconds() / \
                (timestamps[-1] - timestamps[0]).total_seconds()
            y = padding + plot_height * (1 - (val - min_price) / price_range)
            line_points.append(f"{x},{y}")
            area_points.append(f"{x},{y}")

        # Complete area points for fill
        base_y = padding + plot_height * (1 - (0 - min_price) / price_range)
        area_points.append(f"{padding + plot_width},{base_y}")
        area_points.append(f"{padding},{base_y}")

        svg_content += f'''
    <path class="price-area" fill="url(#priceGradient)" d="M {' L '.join(area_points)} Z" />
    <path class="price-line" d="M {' L '.join(line_points)}" />'''

        # Add min/max dots if enabled
        if minmaxdot:
            min_val = min(values)
            max_val = max(values)
            min_idx = values.index(min_val)
            max_idx = values.index(max_val)

            # Min dot and label
            min_x = padding + plot_width * (timestamps[min_idx] - timestamps[0]).total_seconds(
            ) / (timestamps[-1] - timestamps[0]).total_seconds()
            min_y = padding + plot_height * \
                (1 - (min_val - min_price) / price_range)
            svg_content += f'''
    <circle class="min-dot" cx="{min_x}" cy="{min_y}" r="4" />
    <text class="dot-label" x="{min_x}" y="{min_y-10}" text-anchor="middle">{min_val:.1f}</text>'''

            # Max dot and label
            max_x = padding + plot_width * (timestamps[max_idx] - timestamps[0]).total_seconds(
            ) / (timestamps[-1] - timestamps[0]).total_seconds()
            max_y = padding + plot_height * \
                (1 - (max_val - min_price) / price_range)
            svg_content += f'''
    <circle class="max-dot" cx="{max_x}" cy="{max_y}" r="4" />
    <text class="dot-label" x="{max_x}" y="{max_y-10}" text-anchor="middle">{max_val:.1f}</text>'''

        # Add brand card
        svg_content += f'''
    <!-- Brand card -->
    <rect class="brand-card" x="{width-padding-65}" y="{height-padding-40}" width="60" height="20"/>
    <text class="brand-text" x="{width-padding-35}" y="{height-padding-26}" text-anchor="middle">by skale.dev</text>
</svg>'''

        with open('./data/charts/'+output_file, 'w') as f:
            f.write(svg_content)

        print(f"Chart saved to {output_file}")


if __name__ == "__main__":
    today = datetime.now().date()
    startdate = today - timedelta(days=4)
    enddate = today + timedelta(days=1)
    outputfilename = f"price_chart_{startdate.strftime(
        '%Y-%m-%d')}_{enddate.strftime('%Y-%m-%d')}.svg"
    gen_chart_svg(startday=startdate, endday=enddate,
                  output_file=outputfilename, minmaxdot=True)
