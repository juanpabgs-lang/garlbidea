from __future__ import annotations

import time
from typing import Any

import httpx
import pandas as pd

from ..catalog import COMPETITOR_ORIGINS, MARKETS, iso2, m49
from ..http import get_json
from .base import run_connector

BASE = "https://comtradeapi.un.org/public/v1/preview"

REPORTERS_EXPORT = {
    "IT": [2024, 2025],
    "TR": [2024, 2025],
    "EG": [2024, 2025],
    "ES": [2025],
    "FR": [2025],
    "SA": [2024, 2025],
}
REPORTERS_IMPORT = {
    "KE": [2025],
    "LB": [2024],
    "SA": [2024],
    "QA": [2024],
    "OM": [2025],
    "KW": [2025],
    "TZ": [2025],
    "UG": [2025],
    "RW": [2025],
    "IQ": [2024],
    "JO": [2024],
}
MIRROR_PARTNERS = [m for m in MARKETS if m not in REPORTERS_IMPORT]
PRODUCTS = ["1902", "190219", "110311", "200290"]
MONTHLY = [
    ("TR", "M", [f"2025{m:02d}" for m in range(1, 13)] + [f"2024{m:02d}" for m in range(1, 13)], "190219", "X"),
    ("EG", "M", [f"2026{m:02d}" for m in range(1, 7)] + [f"2025{m:02d}" for m in (10, 11, 12)], "1902", "X"),
    ("IT", "M", [f"2025{m:02d}" for m in range(1, 13)], "190219", "X"),
]


def _rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return list(payload.get("data") or [])


def _norm(rows: list[dict[str, Any]], freq: str, source_tag: str) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    recs = []
    for r in rows:
        reporter = iso2(str(r.get("reporterCode") or ""))
        partner = iso2(str(r.get("partnerCode") or ""))
        if r.get("partnerCode") in (0, "0"):
            partner = "WLD"
        recs.append(
            {
                "period": str(r.get("period")),
                "freq": freq,
                "reporter": reporter,
                "partner": partner,
                "product": str(r.get("cmdCode")),
                "flow": "export" if r.get("flowCode") == "X" else "import",
                "value_usd": r.get("primaryValue"),
                "net_kg": r.get("netWgt"),
                "qty": r.get("qty"),
                "source": source_tag,
            }
        )
    df = pd.DataFrame(recs)
    if df.empty:
        return df
    df["tonnes"] = pd.to_numeric(df["net_kg"], errors="coerce") / 1000.0
    df["value_usd"] = pd.to_numeric(df["value_usd"], errors="coerce")
    df["unit_usd_t"] = df["value_usd"] / df["tonnes"].replace(0, pd.NA)
    return df


def _get(c: httpx.Client, freq: str, **params: Any) -> list[dict[str, Any]]:
    url = f"{BASE}/C/{freq}/HS"
    data = get_json(c, url, params=params, retries=2)
    time.sleep(1.35)
    return _rows(data)


def fetch(c: httpx.Client) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    quota_hit = False

    def grab(freq: str, tag: str, **params: Any) -> None:
        nonlocal quota_hit
        if quota_hit:
            return
        try:
            rows = _get(c, freq, **params)
            frames.append(_norm(rows, freq, tag))
        except Exception as exc:  # noqa: BLE001
            if "403" in str(exc) or "Quota" in str(exc):
                quota_hit = True
                return
            # skip a single failed call

    for iso, years in REPORTERS_EXPORT.items():
        code = m49(iso)
        if not code:
            continue
        for year in years:
            grab("A", "comtrade_export", reporterCode=code, period=year, cmdCode="1902", flowCode="X")
            grab("A", "comtrade_export", reporterCode=code, period=year, cmdCode="190219", flowCode="X")
    for iso, years in REPORTERS_IMPORT.items():
        code = m49(iso)
        if not code:
            continue
        for year in years:
            grab("A", "comtrade_import", reporterCode=code, period=year, cmdCode="1902", flowCode="M")
    for partner in MIRROR_PARTNERS:
        pcode = m49(partner)
        if not pcode:
            continue
        grab("A", "comtrade_mirror", period=2025, partnerCode=pcode, cmdCode="190219", flowCode="X")
    # a few recent monthly prints only — preview quota is tight
    for reporter, period, prod in (("TR", "202512", "190219"), ("EG", "202603", "1902"), ("IT", "202512", "190219")):
        code = m49(reporter)
        if code:
            grab("M", "comtrade_monthly", reporterCode=code, period=period, cmdCode=prod, flowCode="X")
    grab("A", "comtrade_tr_durum", reporterCode=792, period=2025, cmdCode="100119", flowCode="M")
    if not frames:
        return pd.DataFrame()
    nonempty = [f for f in frames if f is not None and not f.empty]
    if not nonempty:
        return pd.DataFrame()
    df = pd.concat(nonempty, ignore_index=True)
    df = df.drop_duplicates(subset=["period", "freq", "reporter", "partner", "product", "flow", "source"])
    return df


def refresh(c: httpx.Client):
    return run_connector(
        "un_comtrade",
        "comtrade_flows",
        BASE,
        "UN Comtrade public preview, attribution required",
        lambda: fetch(c),
        notes="Annual exporter/importer/mirror flows plus monthly Turkey/Egypt/Italy pasta.",
        as_of_col="period",
    )


_ = COMPETITOR_ORIGINS
