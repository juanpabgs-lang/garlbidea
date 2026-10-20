from __future__ import annotations

from typing import Any

import httpx
import pandas as pd

from ..catalog import COUNTRIES, MARKETS, iso2
from ..http import get_json
from .base import run_connector

URL = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/DS-045409"
PRODUCTS = ["1902", "190219", "110311", "200290", "210320"]
PARTNERS = list(MARKETS) + ["US", "IQ", "YE", "LY", "EG"]
TIMES = [f"{y}-{m:02d}" for y in (2024, 2025, 2026) for m in range(1, 13) if not (y == 2026 and m > 9)]


def _decode(payload: dict[str, Any]) -> pd.DataFrame:
    dims = payload["id"]
    sizes = payload["size"]
    cats = {k: list(payload["dimension"][k]["category"]["index"].keys()) for k in dims}
    labels = {
        k: payload["dimension"][k]["category"].get("label", {}) for k in dims
    }
    strides = [1] * len(sizes)
    for i in range(len(sizes) - 2, -1, -1):
        strides[i] = strides[i + 1] * sizes[i + 1]
    rows = []
    for key, val in payload.get("value", {}).items():
        k = int(key)
        coords = [(k // s) % sz for s, sz in zip(strides, sizes)]
        rec = {dims[i]: cats[dims[i]][c] for i, c in enumerate(coords)}
        rec["value"] = val
        rec["partner_label"] = labels["partner"].get(rec.get("partner"), rec.get("partner"))
        rec["product_label"] = labels["product"].get(rec.get("product"), rec.get("product"))
        rows.append(rec)
    return pd.DataFrame(rows)


def parse_payload(payload: dict[str, Any]) -> pd.DataFrame:
    raw = _decode(payload)
    if raw.empty:
        return raw
    qty = raw[raw["indicators"] == "QUANTITY_IN_100KG"].copy()
    val = raw[raw["indicators"] == "VALUE_IN_EUROS"].copy()
    keys = ["reporter", "partner", "product", "flow", "time"]
    qty = qty[keys + ["value"]].rename(columns={"value": "qty_100kg"})
    val = val[keys + ["value", "partner_label", "product_label"]].rename(columns={"value": "value_eur"})
    df = val.merge(qty, on=keys, how="outer")
    df["tonnes"] = pd.to_numeric(df["qty_100kg"], errors="coerce") / 10.0
    df["value_eur"] = pd.to_numeric(df["value_eur"], errors="coerce")
    df["unit_eur_t"] = df["value_eur"] / df["tonnes"].replace(0, pd.NA)
    df["origin"] = df["reporter"].map(lambda x: iso2(x) or x)
    df["market"] = df["partner"].map(lambda x: iso2(x) or x)
    df["flow"] = df["flow"].map({"2": "export", "1": "import"}).fillna(df["flow"])
    df["source"] = "comext"
    df["period"] = df["time"]
    return df


def fetch(c: httpx.Client) -> pd.DataFrame:
    params = {
        "format": "JSON",
        "freq": "M",
        "reporter": "IT",
        "flow": "2",
    }
    # Eurostat accepts repeated keys
    items: list[tuple[str, str]] = [(k, v) for k, v in params.items()]
    for p in PARTNERS:
        items.append(("partner", p))
    for p in PRODUCTS:
        items.append(("product", p))
    items.append(("indicators", "VALUE_IN_EUROS"))
    items.append(("indicators", "QUANTITY_IN_100KG"))
    for t in TIMES:
        items.append(("time", t))
    r = c.get(URL, params=items)
    r.raise_for_status()
    return parse_payload(r.json())


def refresh(c: httpx.Client):
    return run_connector(
        "eurostat_comext",
        "comext_flows",
        URL,
        "Eurostat Comext, reuse with attribution",
        lambda: fetch(c),
        notes="Italy monthly extra-EU exports of pasta, semolina and tomato products.",
        as_of_col="period",
    )


# silence unused import warning for catalog COUNTRIES if linters complain
_ = COUNTRIES
