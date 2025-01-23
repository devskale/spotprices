# api/smartenergy/client.py
import requests
from datetime import datetime, date, time, timezone
from zoneinfo import ZoneInfo
from ..models import PriceData


'''
Smartenergy prices 
15min interval, 
EPEXSPOTAT
inculding 20% MWSt
for the day
ie 24*4=96 samples per day
'''
class Client:
    def __init__(self):
        self.base_url = "https://apis.smartenergy.at/market/v1/price"
    
    def fetch_day_prices(self, day: date = None) -> list[PriceData]:
        if day is None:
            day = date.today()
            
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
            raw_data = response.json()
            
            all_prices = [
                PriceData(
                    timestamp=datetime.fromisoformat(entry['date']),
                    price=entry['value']/1.2,   # net price
                    unit='ct/kWh'
                )
                for entry in raw_data['data']
            ]
            
            # Filter for requested day
            return [p for p in all_prices if p.timestamp.date() == day]
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch SmartEnergy prices: {str(e)}")