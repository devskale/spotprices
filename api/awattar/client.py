# api/awattar/client.py
import requests
from datetime import datetime, date
from ..models import PriceClient, PriceData

'''
Awattar prices 
60min interval, 
EPEXSPOTAT
Net price
for the day
ie 24*1=24 samples per day
'''
class Client(PriceClient):
    def __init__(self):
        super().__init__('awattar', 'ct/kWh')
        self.base_url = "https://api.awattar.at/v1/marketdata"
    
    def fetch_day_prices(self, day: date = None) -> list[PriceData]:
        if day is None:
            day = date.today()
            
        start = int(datetime.combine(day, datetime.min.time()).timestamp() * 1000)
        end = int(datetime.combine(day, datetime.max.time()).timestamp() * 1000)
        
        response = requests.get(self.base_url, params={'start': start, 'end': end})
        response.raise_for_status()
        raw_data = response.json()['data']
        
        return [
            PriceData(
                timestamp=datetime.fromtimestamp(entry['start_timestamp'] / 1000),
                price=entry['marketprice'] / 10
            )
            for entry in raw_data
        ]