# api/awattar/client.py
import requests
from datetime import datetime, date, time
from ..models import PriceData

'''
Awattar prices 
60min interval, 
EPEXSPOTAT
Net price
for the day
ie 24*1=24 samples per day
'''
class Client:
    def __init__(self):
        self.base_url = "https://api.awattar.at/v1/marketdata"
    
    def fetch_day_prices(self, day: date = None) -> list[PriceData]:
        if day is None:
            day = date.today()
            
        start = int(datetime.combine(day, time.min).timestamp() * 1000)
        end = int(datetime.combine(day, time.max).timestamp() * 1000)
        
        params = {'start': start, 'end': end}
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            raw_data = response.json()['data']
            
            return [
                PriceData(
                    timestamp=datetime.fromtimestamp(entry['start_timestamp'] / 1000),
                    price=entry['marketprice'] / 10,
                    unit='ct/kWh'
                )
                for entry in raw_data
            ]
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Awattar prices: {str(e)}")