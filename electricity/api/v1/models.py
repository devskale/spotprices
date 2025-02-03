# /electricity/api/v1/models.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class TarifInfo(BaseModel):
    stromanbieter: str
    tarifname: str
    tarifart: str
    preisanpassung: str
    strompreis: str
    kurzbeschreibung: str


class TarifListeResponse(BaseModel):
    tarife: List[TarifInfo]
    updated_at: Optional[datetime] = None
