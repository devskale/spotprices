# api/models.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PriceData:
    timestamp: datetime
    price: float
    unit: str

# api/awattar/client.py
import requests
from datetime import datetime
from ..models import PriceData

class Client:
    def __init__(self):
        self.base_url = "https://api.awattar.at/v1/marketdata"
    
    def fetch_current_prices(self) -> list[PriceData]:
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
            raw_data = response.json()['data']
            
            return [
                PriceData(
                    timestamp=datetime.fromtimestamp(entry['start_timestamp'] / 1000),
                    price=entry['marketprice'] / 10,  # Convert EUR/MWh to ct/kWh
                    unit='ct/kWh'
                )
                for entry in raw_data
            ]
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Awattar prices: {str(e)}")