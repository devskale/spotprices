# electricity/api/v1/endpoints/tarifliste.py
from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/tarifliste", tags=["tarifliste"])

DUMMY_TARIFE = [
    {
        "Anbieter": "Wien Energie",
        "Tarife": [
            {
                "Name": "Optima Entspannt",
                "Verbrauchspreis": 25.40,
                "Tariftyp": ["Bezug"],
                "Andere_Preiskomponenten": ["Grundgebühr: 3.90 EUR/Monat"],
                "Preisanpassungszeitraum": ["12 Monate"],
                "Beschreibung": "Standardtarif mit 12-Monats-Preisgarantie"
            }
        ]
    },
    {
        "Anbieter": "Verbund",
        "Tarife": [
            {
                "Name": "Verbund-Ökostrom",
                "Verbrauchspreis": 22.90,
                "Tariftyp": ["Bezug"],
                "Andere_Preiskomponenten": ["Grundgebühr: 4.90 EUR/Monat"],
                "Preisanpassungszeitraum": ["24 Monate"],
                "Beschreibung": "100% Ökostrom mit 24-Monats-Bindung"
            }
        ]
    }
]


@router.get("")
async def get_tarifliste(rows: int = Query(default=10, ge=1, le=100)) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get list of electricity tariffs.
    """
    return {"tarife": DUMMY_TARIFE[:rows]}
