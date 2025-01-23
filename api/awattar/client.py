# api/awattar/client.py
import requests
from datetime import datetime
from typing import List, Dict, Any

class Client:
    def __init__(self):
        self.base_url = "https://api.awattar.at/v1/marketdata"
    
    def fetch_current_prices(self) -> List[Dict[str, Any]]:
        """Fetch current market prices without date filtering"""
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
            data = response.json()
            return data['data']
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Awattar prices: {str(e)}")

# test_client.py
def test_client():
    client = Client()
    data = client.fetch_current_prices()
    
    assert isinstance(data, list)
    if len(data) > 0:
        first_entry = data[0]
        assert 'start_timestamp' in first_entry
        assert 'end_timestamp' in first_entry
        assert 'marketprice' in first_entry
        assert 'unit' in first_entry
        print("Test passed!")
        print(f"Sample data: {first_entry}")
    else:
        print("No data returned")