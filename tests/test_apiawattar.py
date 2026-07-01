# tests/test_apiawattar.py
from api.awattar.client import Client

client = Client()
prices = client.fetch_day_prices()
print(prices[0])