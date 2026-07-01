# tests/test_api_clients.py
"""Mocked-API tests for the Awattar and SmartEnergy clients.

Uses the `responses` library to stub HTTP calls so no network is needed.
Verifies the unit conversions (Awattar marketprice/10, SmartEnergy /1.2 MWSt)
and the timestamp parsing.
"""
from datetime import date, datetime
import responses

from api.awattar.client import Client as AwattarClient
from api.smartenergy.client import Client as SmartEnergyClient


# --- Awattar ---------------------------------------------------------------

AWATTAR_URL = "https://api.awattar.at/v1/marketdata"


@responses.activate
def test_awattar_fetches_and_divides_by_10():
    """Awattar returns marketprice in EUR/MWh; client converts to ct/kWh
    by dividing by 10. (1 EUR/MWh = 0.1 ct/kWh)"""
    responses.add(
        responses.GET, AWATTAR_URL,
        json={"data": [
            {"start_timestamp": 1700000000000, "end_timestamp": 1700003600000, "marketprice": 250.0},
            {"start_timestamp": 1700003600000, "end_timestamp": 1700007200000, "marketprice": 300.0},
        ]},
        status=200,
    )

    prices = AwattarClient().fetch_day_prices(date(2023, 11, 14))
    assert len(prices) == 2
    assert prices[0].price == 25.0   # 250 / 10
    assert prices[1].price == 30.0   # 300 / 10


@responses.activate
def test_awattar_parses_timestamps():
    responses.add(
        responses.GET, AWATTAR_URL,
        json={"data": [
            {"start_timestamp": 1700000000000, "end_timestamp": 1700003600000, "marketprice": 100.0},
        ]},
        status=200,
    )
    prices = AwattarClient().fetch_day_prices(date(2023, 11, 14))
    # 1700000000000 ms -> 2023-11-14T22:13:20Z
    assert prices[0].timestamp == datetime.fromtimestamp(1700000000)


@responses.activate
def test_awattar_uses_start_end_params():
    """The client should pass start/end query params for the requested day."""
    responses.add(
        responses.GET, AWATTAR_URL,
        json={"data": []},
        status=200,
    )
    AwattarClient().fetch_day_prices(date(2023, 11, 14))
    assert len(responses.calls) == 1
    # Verify the start/end params were sent
    request = responses.calls[0].request
    assert "start=" in request.url
    assert "end=" in request.url


@responses.activate
def test_awattar_empty_response():
    responses.add(
        responses.GET, AWATTAR_URL,
        json={"data": []},
        status=200,
    )
    prices = AwattarClient().fetch_day_prices(date(2023, 11, 14))
    assert prices == []


@responses.activate
def test_awattar_raises_on_http_error():
    responses.add(
        responses.GET, AWATTAR_URL,
        json={"error": "server error"},
        status=500,
    )
    import pytest
    with pytest.raises(Exception):
        AwattarClient().fetch_day_prices(date(2023, 11, 14))


# --- SmartEnergy ----------------------------------------------------------

SMARTENERGY_URL = "https://apis.smartenergy.at/market/v1/price"


@responses.activate
def test_smartenergy_divides_by_1_2_for_mwst():
    """SmartEnergy returns brutto (incl. 20% MWSt); client divides by 1.2
    to get netto."""
    responses.add(
        responses.GET, SMARTENERGY_URL,
        json={"data": [
            {"date": "2026-01-01T00:00:00", "value": 24.0},
            {"date": "2026-01-01T00:15:00", "value": 30.0},
        ]},
        status=200,
    )
    prices = SmartEnergyClient().fetch_day_prices()
    assert len(prices) == 2
    assert prices[0].price == 20.0   # 24 / 1.2
    assert prices[1].price == 25.0   # 30 / 1.2


@responses.activate
def test_smartenergy_parses_iso_timestamps():
    responses.add(
        responses.GET, SMARTENERGY_URL,
        json={"data": [
            {"date": "2026-01-01T12:30:00", "value": 12.0},
        ]},
        status=200,
    )
    prices = SmartEnergyClient().fetch_day_prices()
    assert prices[0].timestamp == datetime.fromisoformat("2026-01-01T12:30:00")


@responses.activate
def test_smartenergy_accepts_day_arg_for_signature_compatibility():
    """SmartEnergy ignores the day arg (API doesn't support it) but accepts
    it to match the Awattar client signature."""
    responses.add(
        responses.GET, SMARTENERGY_URL,
        json={"data": [{"date": "2026-01-01T00:00:00", "value": 12.0}]},
        status=200,
    )
    # Should not raise even though day is passed
    prices = SmartEnergyClient().fetch_day_prices(date(2026, 1, 1))
    assert len(prices) == 1


@responses.activate
def test_smartenergy_empty_response():
    responses.add(
        responses.GET, SMARTENERGY_URL,
        json={"data": []},
        status=200,
    )
    prices = SmartEnergyClient().fetch_day_prices()
    assert prices == []
