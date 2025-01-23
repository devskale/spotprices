# tests/test_normalized_apis.py
import sys
from pathlib import Path
project_root = Path(__file__).parents[1]
sys.path.append(str(project_root))

from api.awattar.client import Client as AwattarClient
from api.smartenergy.client import Client as SmartEnergyClient

def test_normalized_outputs():
    awattar = AwattarClient()
    smart = SmartEnergyClient()
    
    a_prices = awattar.fetch_current_prices()
    s_prices = smart.fetch_current_prices()
    
    print("\nAwattar sample:")
    print(f"Timestamp: {a_prices[0].timestamp}")
    print(f"Price: {a_prices[0].price} {a_prices[0].unit}")
    
    print("\nSmartEnergy sample:")
    print(f"Timestamp: {s_prices[0].timestamp}")
    print(f"Price: {s_prices[0].price} {s_prices[0].unit}")

if __name__ == "__main__":
    test_normalized_outputs()