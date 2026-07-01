# /electricity/api/v1/endpoints/tarifliste.py

from fastapi import APIRouter, HTTPException, Query
from typing import List
from pathlib import Path
import re
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

from ..models import TarifInfo

router = APIRouter(prefix="/tarifliste", tags=["tarifliste"])

_BRUTTO_CTKWH_RE = re.compile(r"(?P<num>\d+(?:[.,]\d+)?)\s*ct/kWh\s*\(brutto\)", flags=re.IGNORECASE)


def normalize_strompreis_to_netto_exkl_mwst(value: str) -> str:
    def replace_match(match: re.Match) -> str:
        raw_num = match.group("num")
        try:
            brutto = Decimal(raw_num.replace(",", "."))
            netto = (brutto / Decimal("1.2")).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            netto_str = str(netto).replace(".", ",")
            return f"{netto_str} ct/kWh"
        except Exception:
            return match.group(0)

    return _BRUTTO_CTKWH_RE.sub(replace_match, value)


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

        if len(columns) >= 7:
            strompreis = normalize_strompreis_to_netto_exkl_mwst(columns[4])
            tarif = TarifInfo(
                stromanbieter=columns[0],
                tarifname=columns[1],
                tarifart=columns[2],
                preisanpassung=columns[3],
                strompreis=strompreis,
                link=columns[5],
                kurzbeschreibung=columns[6],
            )
            tarife.append(tarif)
        elif len(columns) >= 6:
            strompreis = normalize_strompreis_to_netto_exkl_mwst(columns[4])
            tarif = TarifInfo(
                stromanbieter=columns[0],
                tarifname=columns[1],
                tarifart=columns[2],
                preisanpassung=columns[3],
                strompreis=strompreis,
                kurzbeschreibung=columns[5],
            )
            tarife.append(tarif)

    return tarife


def get_latest_report() -> tuple[Path, datetime]:
    """Get the path and timestamp of the latest report file."""
    report_pattern = re.compile(r'report_\d{8}_tab\.md$')

    # Get the spotprices directory path from CONFIG (not magic path depth)
    from config import CONFIG
    current_dir = CONFIG['db_path'].parent
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


# --- mtime-based cache for parsed tariffs ---------------------------------
# The report file is regenerated ~once daily, but this endpoint is polled
# heavily (thousands of hits). Cache the glob + read + parse and only
# recompute when the underlying file's mtime changes.
_TARIFF_CACHE: dict[str, object] = {}


def get_cached_tariffs() -> tuple[list, Path, datetime]:
    """Return (tariffs, report_path, modified_time), recomputing only when
    the latest report file changes (by path + mtime)."""
    report_file, modified_time = get_latest_report()
    cache_key = f"{report_file}:{report_file.stat().st_mtime}"
    cached = _TARIFF_CACHE.get("key")
    if cached and cached["key"] == cache_key:
        return cached["tariffs"], report_file, modified_time

    with open(report_file, "r", encoding="utf-8") as f:
        content = f.read()
    tariffs = parse_markdown_table(content)
    _TARIFF_CACHE["key"] = {
        "key": cache_key,
        "tariffs": tariffs,
    }
    return tariffs, report_file, modified_time


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
        # Get latest report file (cached by mtime; polled heavily)
        tarife, report_file, modified_time = get_cached_tariffs()

        # Extract date from filename (format: report_YYYYMMDD_tab.md)
        date_match = re.search(r'report_(\d{4})(\d{2})(\d{2})_tab\.md$', report_file.name)
        report_date = None
        if date_match:
            year, month, day = date_match.groups()
            report_date = f"{year}-{month}-{day}"

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
