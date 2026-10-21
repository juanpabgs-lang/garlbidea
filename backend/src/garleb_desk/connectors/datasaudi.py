from __future__ import annotations

import httpx
import pandas as pd

from ..catalog import iso2
from ..http import get_json
from .base import run_connector

API = "https://api.datasaudi.sa/tesseract/data.jsonrecords"


def _query(c: httpx.Client, flow: int) -> pd.DataFrame:
    payload = get_json(
        c,
        API,
        params={
            "cube": "foreign_trade",
            "drilldowns": "Month,Country",
            "measures": "Million SAR,Weight TONS",
            "HS2": "19",
            "Trade Flow": str(flow),
        },
    )
    rows = payload.get("data") or []
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["flow"] = "import" if flow == 1 else "export"
    df["period"] = df.get("Month")
    df["country"] = df.get("Country")
    df["country_id"] = df.get("Country ID")
    df["iso2"] = df["country_id"].map(lambda x: iso2(str(x).upper()) if isinstance(x, str) else None)
    df["sar_m"] = pd.to_numeric(df.get("Million SAR"), errors="coerce")
    df["tonnes"] = pd.to_numeric(df.get("Weight TONS"), errors="coerce")
    df["value_usd"] = df["sar_m"] * 1_000_000 / 3.75
    df["unit_usd_t"] = df["value_usd"] / df["tonnes"].replace(0, pd.NA)
    df["source"] = "gastat_datasaudi"
    df["product"] = "19"
    return df


def fetch(c: httpx.Client) -> pd.DataFrame:
    imp = _query(c, 1)
    exp = _query(c, 2)
    frames = [f for f in (imp, exp) if f is not None and not f.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def refresh(c: httpx.Client):
    return run_connector(
        "saudi_gastat",
        "saudi_trade",
        API,
        "GASTAT via DataSaudi open API",
        lambda: fetch(c),
        notes="Monthly Saudi chapter-19 (cereals preparations) trade by partner, SAR and tonnes.",
        as_of_col="period",
    )
