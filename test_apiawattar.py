from api.awattar.client import Client

client = Client()
prices = client.fetch_current_prices()
print(prices[0])
