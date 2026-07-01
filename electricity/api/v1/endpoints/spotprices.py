from pathlib import Path
import re
from fastapi import HTTPException, Query, Response
from fastapi import APIRouter

from config import CONFIG

router = APIRouter(prefix="/spotprices", tags=["spotprices"])

CHART_DIR = CONFIG['db_path'] / "charts"

# In-memory cache for the latest chart SVG bytes, keyed by range and
# invalidated on file mtime change. Polled heavily; file changes ~daily.
_CHART_CACHE: dict[str, dict] = {}


def find_latest_chart(chart_range: str = "singleday") -> Path:
    """
    Find the latest chart file based on the chart_range.
    - 'singleday': filenames matching price_chart_YYYY-MM-DD.svg
    - 'range': filenames matching price_chart_YYYY-MM-DD_YYYY-MM-DD.svg
    """
    chart_dir = CHART_DIR
    if chart_range == "singleday":
        pattern = re.compile(r"^price_chart_\d{4}-\d{2}-\d{2}\.svg$")
    else:  # chart_range == "range"
        pattern = re.compile(
            r"^price_chart_\d{4}-\d{2}-\d{2}_\d{4}-\d{2}-\d{2}\.svg$")

    svg_files = [f for f in chart_dir.glob("*.svg") if pattern.match(f.name)]
    if not svg_files:
        raise HTTPException(
            status_code=404, detail="No chart found matching the criteria")

    latest_chart = max(svg_files, key=lambda f: f.stat().st_mtime)
    return latest_chart


@router.get("/chart/latest")
async def get_latest_daychart(chart_range: str = Query("singleday", alias="range")) -> Response:
    """
    Get the latest chart available.
    - When range is 'singleday', returns a chart with a single date (price_chart_YYYY-MM-DD.svg).
    - When range is 'range', returns a chart with a date range (price_chart_YYYY-MM-DD_YYYY-MM-DD.svg).
    """
    if chart_range not in ("singleday", "range"):
        chart_range = "singleday"

    latest_chart_path = find_latest_chart(chart_range=chart_range)
    # Cache the SVG bytes keyed on (path, mtime) — this endpoint is polled
    # heavily and the file only changes once daily.
    cache_key = (str(latest_chart_path), latest_chart_path.stat().st_mtime)
    cached = _CHART_CACHE.get(chart_range)
    if cached and cached["key"] == cache_key:
        svg_content = cached["content"]
    else:
        with open(latest_chart_path, "rb") as f:
            svg_content = f.read()
        _CHART_CACHE[chart_range] = {"key": cache_key, "content": svg_content}
    return Response(content=svg_content, media_type="image/svg+xml")
