# api/smartenergy/client.py
import requests
from datetime import datetime, date
from ..models import PriceClient, PriceData


'''
Smartenergy prices 
15min interval, 
EPEXSPOTAT
including 20% MWSt
for the day
ie 24*4=96 samples per day
'''

class Client(PriceClient):
    def __init__(self):
        super().__init__('smartenergy', 'ct/kWh')
        self.base_url = "https://apis.smartenergy.at/market/v1/price"
    
    def fetch_day_prices(self) -> list[PriceData]:
        response = requests.get(self.base_url)
        response.raise_for_status()
        raw_data = response.json()
        
        return [
            PriceData(
                timestamp=datetime.fromisoformat(entry['date']),
                price=entry['value']/1.2
            )
            for entry in raw_data['data']
        ]