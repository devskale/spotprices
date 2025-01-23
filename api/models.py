from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class PriceData:
    timestamp: datetime
    price: float

class PriceClient:
    def __init__(self, source: str, unit: str):
        self.source = source
        self.unit = unit
        
    def get_prices(self) -> List[PriceData]:
        raise NotImplementedError