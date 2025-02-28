# /electricity/api/v1/endpoints/tarifliste.py

from fastapi import APIRouter, HTTPException, Query
from typing import List
from pathlib import Path
import re
from datetime import datetime

from ..models import TarifInfo

router = APIRouter(prefix="/tarifliste", tags=["tarifliste"])


def parse_markdown_table(content: str) -> List[TarifInfo]:
    """Parse markdown table content into TarifInfo objects."""
    tarife = []

    # Split content into lines and remove empty lines
    lines = [line.strip() for line in content.split('\n') if line.strip()]

    # Find the actual table start (after any think blocks)
    table_start = 0
    for i, line in enumerate(lines):
        if re.match(r'\s*\|\s*Stromanbieter\s*\|', line):
            table_start = i
            break

    # Skip header and separator lines from the table start
    data_lines = [line for line in lines[table_start + 2:]
                  if line and '|' in line]

    for line in data_lines:
        # Split line by | and remove empty strings
        columns = [col.strip() for col in line.split('|') if col.strip()]

        if len(columns) >= 6:  # Ensure we have all required columns
            tarif = TarifInfo(
                stromanbieter=columns[0],
                tarifname=columns[1],
                tarifart=columns[2],
                preisanpassung=columns[3],
                strompreis=columns[4],
                kurzbeschreibung=columns[5]
            )
            tarife.append(tarif)

    return tarife


def get_latest_report() -> tuple[Path, datetime]:
    """Get the path and timestamp of the latest report file."""
    report_pattern = re.compile(r'report_\d{8}_tab\.md$')

    # Get the spotprices directory path
    # Go up 4 levels to reach spotprices
    current_dir = Path(__file__).resolve().parents[4]
    report_dir = current_dir / "data" / "crawls"

    if not report_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Report directory not found: {report_dir}"
        )

    report_files = [f for f in report_dir.glob(
        "*") if report_pattern.match(f.name)]

    if not report_files:
        raise HTTPException(
            status_code=404,
            detail="No report files found"
        )

    latest_report = max(report_files, key=lambda x: x.stat().st_mtime)
    modified_time = datetime.fromtimestamp(latest_report.stat().st_mtime)

    return latest_report, modified_time


@router.get("")
async def get_tarifliste(
    rows: int = Query(default=10, ge=1, le=100),
    # Added to match WordPress expectations
    contentformat: str = Query(default="json")
) -> dict:
    """
    Get list of electricity tariffs.

    Args:
        rows: Number of tariffs to return (1-100)
        contentformat: Format of the response (always json)

    Returns:
        Dictionary with tariffs list and metadata
    """
    try:
        # Get latest report file
        report_file, modified_time = get_latest_report()

        # Extract date from filename (format: report_YYYYMMDD_tab.md)
        date_match = re.search(r'report_(\d{4})(\d{2})(\d{2})_tab\.md$', report_file.name)
        report_date = None
        if date_match:
            year, month, day = date_match.groups()
            report_date = f"{year}-{month}-{day}"
        
        # Read and parse report content
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse markdown table into tariff objects
        tarife = parse_markdown_table(content)

        # Return requested number of tariffs with metadata
        return {
            "tariffs": tarife[:rows],
            "metadata": {
                "report_date": report_date,
                "last_modified": modified_time.isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing tariff data: {str(e)}"
        )
