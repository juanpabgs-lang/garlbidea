from __future__ import annotations

import re
from datetime import date, timedelta
from html import unescape

import httpx
import pandas as pd

from ..http import get_bytes
from .base import run_connector

KEYWORDS = (
    "makarna",
    "buğday",
    "bugday",
    "irmik",
    "dahilde işleme",
    "ithalat rejimi",
    "ihracat",
    "gümrük tarife",
    "hububat",
    "un ve unlu",
    "tarım ürünleri",
    "malvarlığının dondurulması",
)


def _decode(raw: bytes) -> str:
    for enc in ("windows-1254", "utf-8", "iso-8859-9"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def fetch(c: httpx.Client) -> pd.DataFrame:
    recs = []
    today = date.today()
    for i in range(0, 18):
        d = today - timedelta(days=i)
        url = f"https://www.resmigazete.gov.tr/eskiler/{d:%Y}/{d:%m}/{d:%Y%m%d}.htm"
        try:
            r = c.get(url, timeout=12.0)
            if r.status_code != 200:
                continue
            raw = r.content
        except Exception:
            continue
        text = unescape(re.sub(r"<[^>]+>", "\n", _decode(raw)))
        lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines() if len(ln.strip()) > 20]
        hits = [ln for ln in lines if any(k.lower() in ln.lower() for k in KEYWORDS)]
        recs.append(
            {
                "date": d.isoformat(),
                "url": url,
                "hit_count": len(hits),
                "headlines": " | ".join(hits[:8]),
                "relevant": bool(hits),
                "source": "resmi_gazete",
            }
        )
    return pd.DataFrame(recs)


def refresh(c: httpx.Client):
    return run_connector(
        "resmi_gazete",
        "gazette",
        "https://www.resmigazete.gov.tr",
        "Republic of Türkiye Official Gazette, public",
        lambda: fetch(c),
        notes="Last 18 daily indexes, keyword-filtered for wheat, pasta, inward processing, export regime, asset freezes.",
        as_of_col="date",
    )
