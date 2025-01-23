# tests/test_apiawattar.py
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parents[1]
sys.path.append(str(project_root))

from api.awattar.client import Client

client = Client()
prices = client.fetch_day_prices()
print(prices[0])