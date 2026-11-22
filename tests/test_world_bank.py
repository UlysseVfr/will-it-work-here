"""Tests for the World Bank ingestion, using fake API responses (no network)."""

import pytest

from ingestion import world_bank as wb

COUNTRY_RECORDS = [
    {"id": "KEN", "iso2Code": "KE", "name": "Kenya",
     "region": {"id": "SSF", "value": "Sub-Saharan Africa "},
     "incomeLevel": {"id": "LMC", "value": "Lower middle income"}},
    {"id": "WLD", "iso2Code": "1W", "name": "World",
     "region": {"id": "NA", "value": "Aggregates"},
     "incomeLevel": {"id": "NA", "value": "Aggregates"}},
]

INDICATOR_RECORDS = [
    {"countryiso3code": "KEN", "date": "2020", "value": 4700.5},
    {"countryiso3code": "KEN", "date": "2021", "value": None},  # missing -> dropped
    {"countryiso3code": "", "date": "2020", "value": 1.0},  # no ISO code -> dropped
]


def test_parse_countries_drops_aggregates_and_strips_names():
    df = wb.parse_countries(COUNTRY_RECORDS)
    assert list(df["iso3"]) == ["KEN"]
    assert df.loc[0, "region"] == "Sub-Saharan Africa"


def test_parse_indicator_keeps_only_valid_rows():
    df = wb.parse_indicator(INDICATOR_RECORDS, "gdp_per_capita_ppp")
    assert len(df) == 1
    assert df.iloc[0].to_dict() == {
        "iso3": "KEN", "indicator": "gdp_per_capita_ppp", "year": 2020, "value": 4700.5,
    }


def test_parse_indicator_empty_input_has_columns():
    df = wb.parse_indicator([], "x")
    assert list(df.columns) == ["iso3", "indicator", "year", "value"]


def test_fetch_all_pages_follows_pagination(monkeypatch):
    pages = {1: [{"pages": 2}, [{"a": 1}]], 2: [{"pages": 2}, [{"a": 2}]]}
    monkeypatch.setattr(wb, "get_json", lambda url, params: pages[params["page"]])
    assert wb.fetch_all_pages("url", {}) == [{"a": 1}, {"a": 2}]


def test_get_json_raises_on_api_error_message(monkeypatch):
    class FakeResp:
        def raise_for_status(self): pass
        def json(self): return [{"message": [{"id": "120", "value": "Invalid value"}]}]

    monkeypatch.setattr(wb.requests, "get", lambda *a, **k: FakeResp())
    with pytest.raises(wb.ApiError, match="World Bank API error"):
        wb.get_json("url", {})


def test_fallback_code_used_when_main_code_rejected(monkeypatch):
    calls = []

    def fake_fetch(name, code, source):
        calls.append(code)
        if code == "NEW.CODE":
            raise wb.ApiError("Invalid value")
        return wb.parse_indicator(INDICATOR_RECORDS, name)

    monkeypatch.setattr(wb, "fetch_indicator", fake_fetch)
    df = wb.fetch_indicator_with_fallbacks("x", {"code": "NEW.CODE", "source": 3, "fallback_codes": ["OLD.CODE"]})
    assert calls == ["NEW.CODE", "OLD.CODE"]
    assert len(df) == 1


def test_all_codes_rejected_returns_none(monkeypatch):
    def always_fail(*a):
        raise wb.ApiError("Invalid value")

    monkeypatch.setattr(wb, "fetch_indicator", always_fail)
    assert wb.fetch_indicator_with_fallbacks("x", {"code": "A", "source": 3}) is None
