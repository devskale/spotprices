import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from db.models.spot_prices import SpotPrice
from config import CONFIG

def plot_prices(days=3):
    db_file = CONFIG['db_path'] / CONFIG['db_file']
    engine = create_engine(f'sqlite:///{db_file}')
    
    today = datetime.now().date()
    end_time = datetime.combine(today + timedelta(days=1), datetime.max.time())
    start_time = datetime.combine(today - timedelta(days=days), datetime.min.time())
    
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

        # Convert timestamps to datetime
        dates = [datetime.fromtimestamp(p.start_timestamp) for p in prices]
        values = [p.price for p in prices]

        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot styling
        plt.title("Spot Tarif stündlich EPEXAT (ct/kWh)", fontsize=16, pad=20)
        
        # Grid
        ax.grid(color="gray", linestyle=(0, (10, 10)), linewidth=0.5, alpha=0.3)
        
        # Main plot
        ax.plot(dates, values, color='#268358', linewidth=2)
        
        # Fill area under curve
        ax.fill_between(dates, values, color='#268358', alpha=0.1)
        
        # Axis formatting
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")
        
        # Date formatting - Modified for 00:00 and 12:00
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %H:%M"))
        ax.xaxis.set_major_locator(mdates.HourLocator(byhour=(0, 12)))
        
        # Remove spines
        ax.spines["top"].set_visible(False)
        ax.spines["left"].set_visible(False)
        
        # Rotate x labels
        plt.xticks(rotation=0)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save and show
        plt.savefig('price_chart.png', dpi=300, bbox_inches='tight')
        plt.show()

if __name__ == "__main__":
    plot_prices()
