# api/smartenergy/client.py
import requests
from datetime import datetime
from ..models import PriceData

class Client:
    def __init__(self):
        self.base_url = "https://apis.smartenergy.at/market/v1/price"
    
    def fetch_current_prices(self) -> list[PriceData]:
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
            raw_data = response.json()
            
            return [
                PriceData(
                    timestamp=datetime.fromisoformat(entry['date']),
                    price=entry['value'],
                    unit='ct/kWh'
                )
                for entry in raw_data['data']
            ]
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch SmartEnergy prices: {str(e)}")