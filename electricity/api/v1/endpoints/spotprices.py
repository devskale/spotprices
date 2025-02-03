# electricity/api/v1/endpoints/spotprices.py
from fastapi import APIRouter, Response
from datetime import date, datetime
from typing import Dict, List, Union

router = APIRouter(prefix="/spotprices", tags=["spotprices"])

DUMMY_CHART_SVG = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="800" height="400" xmlns="http://www.w3.org/2000/svg">
    <rect width="800" height="400" fill="#f0f0f0"/>
    <text x="400" y="200" text-anchor="middle" font-family="Arial">
        Dummy Chart for {date}
    </text>
</svg>"""

DUMMY_PRICES = [
    {"timestamp": "2024-02-02T00:00:00", "price": 22.5},
    {"timestamp": "2024-02-02T01:00:00", "price": 21.8},
    {"timestamp": "2024-02-02T02:00:00", "price": 20.9},
    {"timestamp": "2024-02-02T03:00:00", "price": 19.7},
]


@router.get("/chart/{date}")
async def get_chart(date: date) -> Response:
    """
    Get SVG chart for specified date.
    """
    svg_content = DUMMY_CHART_SVG.format(date=date)
    return Response(content=svg_content, media_type="image/svg+xml")


@router.get("/today")
async def get_today_prices() -> Dict[str, List[Dict[str, Union[str, float]]]]:
    """
    Get today's spot prices.
    """
    return {"prices": DUMMY_PRICES}


@router.get("/stats")
async def get_price_stats() -> Dict[str, Dict[str, float]]:
    """
    Get price statistics.
    """
    return {
        "stats": {
            "min": 19.7,
            "max": 22.5,
            "avg": 21.2,
            "current": 20.9
        }
    }
