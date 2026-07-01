from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from db.models.spot_prices import SpotPrice
import math
from db.maintenance import update_db
from db.utils import get_engine


def gen_chart_svg(startday, endday, output_file='price_chart.svg', minmaxdot=False):
    engine = get_engine()

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

        # Dimensions
        width = 800
        height = 400
        padding_left = 55
        padding_right = 15
        padding_top = 45
        padding_bottom = 50
        plot_width = width - padding_left - padding_right
        plot_height = height - padding_top - padding_bottom

        # Price range (handle negatives)
        min_price = min(0, min(values))
        max_price = max(values)
        
        # Round min/max to nearest 5 cents for tighter scale
        min_price = math.floor(min_price / 5) * 5
        max_price = math.ceil(max_price / 5) * 5
        price_range = max_price - min_price

        # Calculate zero line position
        zero_y = padding_top + plot_height * (1 - (0 - min_price) / price_range)

        # Format date range for title
        if startday == endday - timedelta(days=1):
            date_range_str = startday.strftime('%d.%m.%Y')
        else:
            date_range_str = f"{startday.strftime('%d.%m.')} – {(endday - timedelta(days=1)).strftime('%d.%m.%Y')}"

        # German weekday names
        weekday_de = {
            'Monday': 'Mo', 'Tuesday': 'Di', 'Wednesday': 'Mi',
            'Thursday': 'Do', 'Friday': 'Fr', 'Saturday': 'Sa', 'Sunday': 'So'
        }

        svg_content = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;">
    <defs>
        <linearGradient id="priceGradient" gradientUnits="userSpaceOnUse" x1="0" y1="{padding_top}" x2="0" y2="{padding_top + plot_height}">
            <stop offset="0%" stop-color="#22c55e" stop-opacity="0.6"/>
            <stop offset="50%" stop-color="#22c55e" stop-opacity="0.15"/>
            <stop offset="100%" stop-color="#22c55e" stop-opacity="0"/>
        </linearGradient>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.15"/>
        </filter>
    </defs>

    <!-- Title -->
    <text x="{width/2}" y="22" text-anchor="middle" font-size="15" font-weight="600" fill="#1f2937">
        Strom-Spotpreis EPEX AT
    </text>
    <text x="{width/2}" y="40" text-anchor="middle" font-size="11" fill="#6b7280">
        {date_range_str}
    </text>

    <!-- Y-axis label (rotated, left side) -->
    <text x="15" y="{height/2}" text-anchor="middle" font-size="11" fill="#6b7280" transform="rotate(-90, 15, {height/2})">
        €/MWh
    </text>
'''

        # Generate horizontal grid lines and labels
        step = 10 if price_range > 50 else 5
        for price in range(int(min_price), int(max_price) + 1, step):
            y = padding_top + plot_height * (1 - (price - min_price) / price_range)
            is_zero = price == 0
            svg_content += f'''
    <line x1="{padding_left}" y1="{y:.1f}" x2="{padding_left + plot_width}" y2="{y:.1f}" 
          stroke="{"#9ca3af" if is_zero else "#e5e7eb"}" stroke-width="{"1" if is_zero else "0.5"}" 
          stroke-dasharray="{"none" if is_zero else "4,4"}"/>
    <text x="{padding_left - 6}" y="{y + 4}" text-anchor="end" font-size="10" fill="#6b7280">{price}</text>'''

        # Generate vertical grid lines and day labels (at midnight for each day)
        current_day = startday
        day_positions = []
        
        while current_day < endday:
            midnight = datetime.combine(current_day, datetime.min.time())
            if midnight >= timestamps[0] and midnight <= timestamps[-1]:
                x = padding_left + plot_width * (midnight - timestamps[0]).total_seconds() / (timestamps[-1] - timestamps[0]).total_seconds()
                day_positions.append((x, current_day))
                
                svg_content += f'''
    <line x1="{x:.1f}" y1="{padding_top}" x2="{x:.1f}" y2="{padding_top + plot_height}" 
          stroke="#d1d5db" stroke-width="1"/>'''
            
            current_day += timedelta(days=1)

        # Add day labels below chart
        for x, day in day_positions:
            weekday = day.strftime('%A')
            date_str = day.strftime('%d.%m')
            svg_content += f'''
    <text x="{x:.1f}" y="{padding_top + plot_height + 15}" text-anchor="start" font-size="10" font-weight="500" fill="#374151">{weekday_de.get(weekday, weekday[:2])}</text>
    <text x="{x:.1f}" y="{padding_top + plot_height + 28}" text-anchor="start" font-size="9" fill="#9ca3af">{date_str}</text>'''

        # Add noon markers (lighter vertical lines)
        current_day = startday
        while current_day < endday:
            noon = datetime.combine(current_day, datetime.min.time()).replace(hour=12)
            if noon >= timestamps[0] and noon <= timestamps[-1]:
                x = padding_left + plot_width * (noon - timestamps[0]).total_seconds() / (timestamps[-1] - timestamps[0]).total_seconds()
                svg_content += f'''
    <line x1="{x:.1f}" y1="{padding_top}" x2="{x:.1f}" y2="{padding_top + plot_height}" 
          stroke="#e5e7eb" stroke-width="0.5" stroke-dasharray="2,2"/>'''
            current_day += timedelta(days=1)

        # Generate price line and area
        line_points = []
        area_points = []
        
        for ts, val in zip(timestamps, values):
            x = padding_left + plot_width * (ts - timestamps[0]).total_seconds() / (timestamps[-1] - timestamps[0]).total_seconds()
            y = padding_top + plot_height * (1 - (val - min_price) / price_range)
            line_points.append(f"{x:.1f},{y:.1f}")
            area_points.append((x, y))

        # Build area path (fill to zero line)
        area_path = f"M {area_points[0][0]:.1f},{zero_y:.1f}"
        for x, y in area_points:
            area_path += f" L {x:.1f},{y:.1f}"
        area_path += f" L {area_points[-1][0]:.1f},{zero_y:.1f} Z"

        svg_content += f'''
    <!-- Price area fill -->
    <path d="{area_path}" fill="url(#priceGradient)"/>
    
    <!-- Price line -->
    <path d="M {' L '.join(line_points)}" stroke="#16a34a" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'''

        # Add min/max dots if enabled
        if minmaxdot and values:
            min_val = min(values)
            max_val = max(values)
            min_indices = [i for i, v in enumerate(values) if v == min_val]
            max_indices = [i for i, v in enumerate(values) if v == max_val]
            
            # Use first occurrence for positioning
            min_idx = min_indices[0]
            max_idx = max_indices[0]

            # Min dot
            min_x = padding_left + plot_width * (timestamps[min_idx] - timestamps[0]).total_seconds() / (timestamps[-1] - timestamps[0]).total_seconds()
            min_y = padding_top + plot_height * (1 - (min_val - min_price) / price_range)
            svg_content += f'''
    <!-- Min indicator -->
    <circle cx="{min_x:.1f}" cy="{min_y:.1f}" r="5" fill="#3b82f6" filter="url(#shadow)"/>
    <circle cx="{min_x:.1f}" cy="{min_y:.1f}" r="3" fill="white"/>
    <text x="{min_x:.1f}" y="{min_y - 10:.1f}" text-anchor="middle" font-size="10" font-weight="600" fill="#3b82f6">{min_val:.1f}</text>'''

            # Max dot
            max_x = padding_left + plot_width * (timestamps[max_idx] - timestamps[0]).total_seconds() / (timestamps[-1] - timestamps[0]).total_seconds()
            max_y = padding_top + plot_height * (1 - (max_val - min_price) / price_range)
            svg_content += f'''
    <!-- Max indicator -->
    <circle cx="{max_x:.1f}" cy="{max_y:.1f}" r="5" fill="#ef4444" filter="url(#shadow)"/>
    <circle cx="{max_x:.1f}" cy="{max_y:.1f}" r="3" fill="white"/>
    <text x="{max_x:.1f}" y="{max_y - 10:.1f}" text-anchor="middle" font-size="10" font-weight="600" fill="#ef4444">{max_val:.1f}</text>'''

        # Legend
        legend_y = padding_top + plot_height + 42
        svg_content += f'''
    <!-- Legend -->
    <g transform="translate({padding_left}, {legend_y})">
        <circle cx="0" cy="0" r="4" fill="#3b82f6"/>
        <text x="8" y="4" font-size="9" fill="#6b7280">Tiefstpreis</text>
        <circle cx="85" cy="0" r="4" fill="#ef4444"/>
        <text x="93" y="4" font-size="9" fill="#6b7280">Höchstpreis</text>
    </g>'''

        # Brand attribution (bottom right, subtle)
        svg_content += f'''
    <!-- Brand -->
    <text x="{width - 10}" y="{height - 8}" text-anchor="end" font-size="8" fill="#d1d5db">skale.dev</text>
</svg>'''

        output_path = Path('./data/charts') / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)

        print(f"Chart saved to {output_file} ({len(prices)} data points)")


if __name__ == "__main__":
    # Update the database first
    print("Updating database...")
    total_added = update_db()
    print(f"Database update complete. Added {total_added} new prices.")

    # Delete old charts
    chart_dir = Path(__file__).resolve().parents[0] / "data" / "charts"
    for file in chart_dir.glob("*.svg"):
        file.unlink()
    for file in chart_dir.glob("*.png"):
        file.unlink()

    today = datetime.now().date()

    # Generate today's chart
    startdate = today
    enddate = today + timedelta(days=1)
    outputfilename = f"price_chart_{startdate.strftime('%Y-%m-%d')}.svg"
    gen_chart_svg(startday=startdate, endday=enddate, output_file=outputfilename, minmaxdot=True)

    # Generate week chart
    startdate = today - timedelta(days=5)
    enddate = today + timedelta(days=1)
    outputfilename = f"price_chart_{startdate.strftime('%Y-%m-%d')}_{enddate.strftime('%Y-%m-%d')}.svg"
    gen_chart_svg(startday=startdate, endday=enddate, output_file=outputfilename, minmaxdot=True)
