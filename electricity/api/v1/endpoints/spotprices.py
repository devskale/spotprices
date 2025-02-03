from pathlib import Path
import re
from fastapi import HTTPException, Query, Response
from fastapi import APIRouter

router = APIRouter(prefix="/spotprices", tags=["spotprices"])

# Update with your actual chart directory
CHART_DIR = Path(__file__).resolve().parents[4] / "data" / "charts"


def find_latest_chart(chart_range: str = "singleday") -> Path:
    """
    Find the latest chart file based on the chart_range.
    - 'singleday': filenames matching price_chart_YYYY-MM-DD.svg
    - 'range': filenames matching price_chart_YYYY-MM-DD_YYYY-MM-DD.svg
    """
    chart_dir = CHART_DIR
    print(chart_dir)
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
    with open(latest_chart_path, "rb") as f:
        svg_content = f.read()
    return Response(content=svg_content, media_type="image/svg+xml")
