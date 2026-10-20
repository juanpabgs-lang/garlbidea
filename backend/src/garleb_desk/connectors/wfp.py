from __future__ import annotations

import io

import httpx
import pandas as pd

from ..catalog import WFP_DATASETS
from ..http import get_bytes, get_json
from .base import run_connector

HDX = "https://data.humdata.org/api/3/action/package_show"
KEEP = ("pasta", "spaghetti", "noodle", "semolina", "tomato")


def _resource_url(c: httpx.Client, package_id: str) -> str:
    data = get_json(c, HDX, params={"id": package_id})
    for res in data.get("result", {}).get("resources", []):
        url = res.get("url") or ""
        if url.endswith(".csv") and "food_prices" in url:
            return url
    raise RuntimeError(f"no food price csv for {package_id}")


def _kg(unit: str, commodity: str) -> float | None:
    u = (unit or "").upper().strip()
    if u in {"KG", "1 KG"}:
        return 1.0
    if "500 G" in u or u == "500G":
        return 0.5
    if "660 G" in u:
        return 0.66
    if "650 G" in u:
        return 0.65
    if "64 KG" in u:
        return 64.0
    if "PACKET" in u:
        return None
    return None


def fetch(c: httpx.Client) -> pd.DataFrame:
    frames = []
    for iso2, pkg in WFP_DATASETS.items():
        url = _resource_url(c, pkg)
        raw = get_bytes(c, url)
        df = pd.read_csv(io.BytesIO(raw))
        df = df[~df["date"].astype(str).str.startswith("#")]
        df["commodity_l"] = df["commodity"].astype(str).str.lower()
        df = df[df["commodity_l"].apply(lambda x: any(k in x for k in KEEP))]
        df["market_iso2"] = iso2
        df["kg"] = [ _kg(u, cname) for u, cname in zip(df["unit"], df["commodity"]) ]
        df["usdprice"] = pd.to_numeric(df["usdprice"], errors="coerce")
        df["usd_per_kg"] = df["usdprice"] / df["kg"]
        df["source"] = "wfp_hdx"
        df["source_url"] = url
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    keep_cols = [
        "date",
        "market_iso2",
        "admin1",
        "admin2",
        "market",
        "category",
        "commodity",
        "unit",
        "pricetype",
        "currency",
        "price",
        "usdprice",
        "usd_per_kg",
        "source",
        "source_url",
    ]
    return out[[c for c in keep_cols if c in out.columns]]


def refresh(c: httpx.Client):
    return run_connector(
        "wfp_retail",
        "wfp_prices",
        "https://data.humdata.org",
        "WFP via HDX, CC BY-IGO",
        lambda: fetch(c),
        notes="Retail pasta and tomato prices for Lebanon, Syria, Somalia, Kenya, Yemen.",
        as_of_col="date",
    )
