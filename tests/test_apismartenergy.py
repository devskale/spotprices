# tests/test_apismartenergy.py
from api.smartenergy.client import Client

client = Client()
prices = client.fetch_day_prices()
print(prices[0])