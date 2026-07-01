# tests/test_endpoints.py
"""FastAPI endpoint tests for /electricity/tarifliste and
/electricity/spotprices/chart/latest using fastapi.testclient.TestClient.

Uses tmp_path + monkeypatch to point the endpoints at isolated fixture
directories so no real data/crawls or data/charts are needed.
"""
import pytest
from fastapi.testclient import TestClient

from main import app
import electricity.api.v1.endpoints.tarifliste as tarifliste_mod
import electricity.api.v1.endpoints.spotprices as spotprices_mod


client = TestClient(app)


# --- /electricity/tarifliste ----------------------------------------------

SAMPLE_REPORT = """| Stromanbieter | Tarifname | Tarifart | Preisanpassung | Strompreis (ct/kWh netto) | Link | Kurzbeschreibung |
|:---|:---|:---|:---|:---|:---|:---|
| WienEnergie | Strom Fix 24 | Bezug | Fixpreis | 24,50 ct/kWh | https://wienenergie.at | Fixpreis 24 Monate |
| Verbund | OPTIMA Entspannt | Bezug | Fixpreis | 26,90 ct/kWh | https://verbund.com | Fixpreis 12 Monate |
| OEMAG | Marktpreis | Einspeisung | Monatlich | 9,10 ct/kWh | https://oem-ag.at | Stand Jan 2026 |
"""


@pytest.fixture
def report_dir(tmp_path, monkeypatch):
    """Point the tarifliste endpoint at a tmp data/crawls dir with a report."""
    crawls = tmp_path / "data" / "crawls"
    crawls.mkdir(parents=True)
    (crawls / "report_20260101_tab.md").write_text(SAMPLE_REPORT, encoding="utf-8")
    # monkeypatch CONFIG so get_latest_report() finds our tmp dir
    from config import CONFIG
    monkeypatch.setitem(CONFIG, "db_path", tmp_path / "data")
    # clear the module-level cache so the new file is picked up
    tarifliste_mod._TARIFF_CACHE.clear()
    return crawls


def test_tarifliste_returns_tariffs(report_dir):
    resp = client.get("/electricity/tarifliste?rows=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tariffs"]) == 2
    assert data["tariffs"][0]["stromanbieter"] == "WienEnergie"
    assert data["tariffs"][1]["stromanbieter"] == "Verbund"


def test_tarifliste_rows_limit(report_dir):
    resp = client.get("/electricity/tarifliste?rows=1")
    assert resp.status_code == 200
    assert len(resp.json()["tariffs"]) == 1


def test_tarifliste_includes_metadata(report_dir):
    resp = client.get("/electricity/tarifliste?rows=10")
    data = resp.json()
    assert data["metadata"]["report_date"] == "2026-01-01"
    assert "last_modified" in data["metadata"]


def test_tarifliste_rows_validation_ge_1(report_dir):
    # rows=0 should be rejected by the ge=1 constraint
    resp = client.get("/electricity/tarifliste?rows=0")
    assert resp.status_code == 422


def test_tarifliste_rows_validation_le_100(report_dir):
    resp = client.get("/electricity/tarifliste?rows=101")
    assert resp.status_code == 422


def test_tarifliste_404_when_no_report(tmp_path, monkeypatch):
    from config import CONFIG
    monkeypatch.setitem(CONFIG, "db_path", tmp_path / "data")
    tarifliste_mod._TARIFF_CACHE.clear()
    resp = client.get("/electricity/tarifliste?rows=1")
    assert resp.status_code == 404


def test_tarifliste_caches_by_mtime(report_dir):
    """Second call should hit the cache (same mtime -> same result)."""
    r1 = client.get("/electricity/tarifliste?rows=3")
    r2 = client.get("/electricity/tarifliste?rows=3")
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json() == r2.json()


# --- /electricity/spotprices/chart/latest --------------------------------

SAMPLE_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400"><text>test</text></svg>'


@pytest.fixture
def chart_dir(tmp_path, monkeypatch):
    """Point the spotprices endpoint at a tmp data/charts dir with an SVG."""
    charts = tmp_path / "data" / "charts"
    charts.mkdir(parents=True)
    (charts / "price_chart_2026-01-01.svg").write_bytes(SAMPLE_SVG)
    (charts / "price_chart_2025-12-26_2026-01-01.svg").write_bytes(SAMPLE_SVG)
    # CHART_DIR is a module-level constant set at import time, so patch it
    # directly rather than going through CONFIG.
    monkeypatch.setattr(spotprices_mod, "CHART_DIR", charts)
    spotprices_mod._CHART_CACHE.clear()
    return charts


def test_chart_latest_singleday(chart_dir):
    resp = client.get("/electricity/spotprices/chart/latest?range=singleday")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/svg+xml"
    assert resp.content == SAMPLE_SVG


def test_chart_latest_range(chart_dir):
    resp = client.get("/electricity/spotprices/chart/latest?range=range")
    assert resp.status_code == 200
    assert resp.content == SAMPLE_SVG


def test_chart_latest_invalid_range_falls_back_to_singleday(chart_dir):
    resp = client.get("/electricity/spotprices/chart/latest?range=invalid")
    assert resp.status_code == 200
    assert resp.content == SAMPLE_SVG


def test_chart_latest_404_when_no_chart(tmp_path, monkeypatch):
    monkeypatch.setattr(spotprices_mod, "CHART_DIR", tmp_path / "nonexistent")
    spotprices_mod._CHART_CACHE.clear()
    resp = client.get("/electricity/spotprices/chart/latest?range=singleday")
    assert resp.status_code == 404


def test_chart_latest_caches_by_mtime(chart_dir):
    r1 = client.get("/electricity/spotprices/chart/latest?range=singleday")
    r2 = client.get("/electricity/spotprices/chart/latest?range=singleday")
    assert r1.content == r2.content == SAMPLE_SVG


# --- health & root -------------------------------------------------------

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "message" in resp.json()
