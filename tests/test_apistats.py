# tests/test_stats.py
import sys
from pathlib import Path
project_root = Path(__file__).parents[1]
sys.path.append(str(project_root))

from api.awattar.client import Client as AwattarClient
from api.smartenergy.client import Client as SmartEnergyClient

def print_stats(prices, source, unit):
    min_price = min(prices, key=lambda x: x.price)
    max_price = max(prices, key=lambda x: x.price)
    avg_price = sum(p.price for p in prices) / len(prices)
    
    print(f"\n{source} Stats:")
    print(f"Number of prices: {len(prices)}")
    print(f"Min price: {min_price.price:.3f} {unit} at {min_price.timestamp.strftime('%Y-%m-%d %H:%M')}")
    print(f"Max price: {max_price.price:.3f} {unit} at {max_price.timestamp.strftime('%Y-%m-%d %H:%M')}")
    print(f"Avg price: {avg_price:.3f} {unit}")

awattar = AwattarClient()
smart = SmartEnergyClient()

today_a = awattar.fetch_day_prices()
today_s = smart.fetch_day_prices()

print_stats(today_a, "Awattar", "ct/kWh")
print_stats(today_s, "SmartEnergy", "ct/kWh")


