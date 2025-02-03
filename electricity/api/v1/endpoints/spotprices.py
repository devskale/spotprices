# electricity/api/v1/endpoints/spotprices.py
from fastapi import APIRouter, Response, HTTPException
from datetime import date, datetime
from typing import Dict, List, Union
import os
from pathlib import Path

router = APIRouter(prefix="/spotprices", tags=["spotprices"])

# Update with your actual chart directory
current_dir = Path(__file__).resolve().parents[4]
CHART_DIR = current_dir / "data" / "charts"


def find_latest_chart():
    """Finds the latest SVG chart file in the directory."""
    chart_files = [f for f in os.listdir(
        CHART_DIR) if f.endswith(".svg") and "price_chart_" in f]
    if not chart_files:
        raise HTTPException(status_code=404, detail="No chart files found.")

    # Sort files by date (assuming filename format price_chart_YYYY-MM-DD.svg)
    chart_files.sort(key=lambda x: datetime.strptime(
        x.split("_")[-1].split(".")[0], "%Y-%m-%d"), reverse=True)

    latest_chart = chart_files[0]
    return os.path.join(CHART_DIR, latest_chart)


@router.get("/chart/latest")
async def get_latest_chart() -> Response:
    """
    Get the latest SVG chart available.
    """
    latest_chart_path = find_latest_chart()
    with open(latest_chart_path, "rb") as f:
        svg_content = f.read()
    return Response(content=svg_content, media_type="image/svg+xml")


@router.get("/chart/{date}")
async def get_chart(date: date) -> Response:
    """
    Get SVG chart for specified date. Defaults to latest if chart not found for date.
    """
    chart_path = CHART_DIR / f"price_chart_{date.strftime('%Y-%m-%d')}.svg"
    if not chart_path.exists():
        chart_path = find_latest_chart()
    with open(chart_path, "rb") as f:
        svg_content = f.read()
    return Response(content=svg_content, media_type="image/svg+xml")


@router.get("/today")
async def get_today_prices() -> Dict[str, List[Dict[str, Union[str, float]]]]:
    """
    Get today's spot prices.  (Placeholder - replace with actual data source)
    """
    # Replace with your actual data retrieval logic
    return {"prices": [{"timestamp": "2024-10-27T12:00:00", "price": 25.2}]}


@router.get("/stats")
async def get_price_stats() -> Dict[str, Dict[str, float]]:
    """
    Get price statistics. (Placeholder - replace with actual data source)
    """
    # Replace with your actual data retrieval logic
    return {"stats": {"average": 25.2, "max": 30.0, "min": 20.0}}
