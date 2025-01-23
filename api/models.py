# api/models.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PriceData:
    timestamp: datetime
    price: float
    unit: str

