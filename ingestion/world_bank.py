"""Download country metadata and indicators from the World Bank API.

Writes two raw CSV files that dbt will read later:
  data/raw/countries.csv   one row per country (aggregates like "World" removed)
  data/raw/indicators.csv  long format: one row per country, indicator and year

Run from the project root:
    python -m ingestion.world_bank
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import pandas as pd
import requests

from ingestion.config import API_BASE, END_YEAR, INDICATORS, START_YEAR

log = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")
PER_PAGE = 20_000  # large pages keep the number of requests small
MAX_RETRIES = 4


class ApiError(RuntimeError):
    """The API answered, but rejected the request (e.g. unknown indicator code)."""


def get_json(url: str, params: dict) -> list:
    """GET a World Bank API URL with retries. Returns the parsed JSON body."""
    params = {"format": "json", "per_page": PER_PAGE, **params}
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=60)
            resp.raise_for_status()
            body = resp.json()
            # The API returns errors as a 200 with a "message" object.
            if isinstance(body, list) and body and isinstance(body[0], dict) and "message" in body[0]:
                raise ApiError(f"World Bank API error: {body[0]['message']}")
            return body
        except (requests.RequestException, ValueError) as exc:
            if attempt == MAX_RETRIES:
                raise
            wait = 2**attempt
            log.warning("Attempt %d failed (%s), retrying in %ds", attempt, exc, wait)
            time.sleep(wait)
    raise AssertionError("unreachable")


def fetch_all_pages(url: str, params: dict) -> list[dict]:
    """Follow the API's pagination and return every record."""
    meta, records = get_json(url, {**params, "page": 1})
    records = records or []
    for page in range(2, int(meta.get("pages", 1)) + 1):
        _, more = get_json(url, {**params, "page": page})
        records.extend(more or [])
    return records


def parse_countries(records: list[dict]) -> pd.DataFrame:
    """Keep real countries only (aggregates have region id 'NA')."""
    rows = [
        {
            "iso3": r["id"],
            "iso2": r["iso2Code"],
            "name": r["name"],
            "region": r["region"]["value"].strip(),
            "income_level": r["incomeLevel"]["value"].strip(),
        }
        for r in records
        if r["region"]["id"] != "NA"
    ]
    return pd.DataFrame(rows).sort_values("iso3").reset_index(drop=True)


def parse_indicator(records: list[dict], name: str) -> pd.DataFrame:
    """Turn raw indicator records into tidy rows, dropping empty values."""
    rows = [
        {
            "iso3": r["countryiso3code"],
            "indicator": name,
            "year": int(r["date"]),
            "value": float(r["value"]),
        }
        for r in records
        if r.get("value") is not None and r.get("countryiso3code")
    ]
    return pd.DataFrame(rows, columns=["iso3", "indicator", "year", "value"])


def fetch_countries() -> pd.DataFrame:
    return parse_countries(fetch_all_pages(f"{API_BASE}/country", {}))


def fetch_indicator(name: str, code: str, source: int) -> pd.DataFrame:
    url = f"{API_BASE}/country/all/indicator/{code}"
    records = fetch_all_pages(url, {"source": source, "date": f"{START_YEAR}:{END_YEAR}"})
    return parse_indicator(records, name)


def fetch_indicator_with_fallbacks(name: str, spec: dict) -> pd.DataFrame | None:
    """Try the main code, then each fallback. Returns None if every code is rejected."""
    for code in [spec["code"], *spec.get("fallback_codes", [])]:
        try:
            df = fetch_indicator(name, code, spec["source"])
            if code != spec["code"]:
                log.warning("%s: used fallback code %s", name, code)
            return df
        except ApiError as exc:
            log.warning("%s: code %s rejected (%s)", name, code, exc)
    return None


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    countries = fetch_countries()
    countries.to_csv(RAW_DIR / "countries.csv", index=False)
    log.info("Saved %d countries", len(countries))

    frames, failed = [], []
    for name, spec in INDICATORS.items():
        df = fetch_indicator_with_fallbacks(name, spec)
        if df is None:
            failed.append(name)
            continue
        df = df[df["iso3"].isin(countries["iso3"])]  # drop regional aggregates
        log.info("%-24s %6d rows, %3d countries", name, len(df), df["iso3"].nunique())
        frames.append(df)

    indicators = pd.concat(frames, ignore_index=True)
    indicators.to_csv(RAW_DIR / "indicators.csv", index=False)
    log.info("Saved %d indicator rows to %s", len(indicators), RAW_DIR / "indicators.csv")
    if failed:
        log.error("Could not download: %s (check their codes in ingestion/config.py)", ", ".join(failed))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
