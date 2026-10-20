from __future__ import annotations

import re
from html import unescape

import httpx
import pandas as pd

from ..http import get_text
from .base import run_connector

LIST = "https://www.ppa.gov.lb/ar/tenders"
FOOD = (
    "غذا",
    "طعام",
    "تموين",
    "معكرون",
    "طحين",
    "قمح",
    "بندور",
    "صلصة",
    "food",
    "flour",
    "wheat",
    "pasta",
    "tomato",
    "ration",
    "catering",
    "kitchen",
    "مستشفى",
    "مدرست",
    "تغذية",
    "تموينات",
)


def fetch(c: httpx.Client) -> pd.DataFrame:
    page = get_text(c, LIST)
    ids = sorted(set(re.findall(r"/ar/tenders/details/(\d+)", page)), reverse=True)[:18]
    recs = []
    for tid in ids:
        url = f"https://www.ppa.gov.lb/ar/tenders/details/{tid}"
        try:
            r = c.get(url, timeout=15.0)
            if r.status_code != 200:
                continue
            html = r.text
        except Exception:
            continue
        text = unescape(re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S))
        text = re.sub(r"<[^>]+>", "\n", text)
        lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines() if ln.strip()]
        blob = " ".join(lines)
        title = next((ln for ln in lines if len(ln) > 18 and "تفاصيل" not in ln and "الجهة" not in ln), tid)
        buyer = ""
        for i, ln in enumerate(lines):
            if "الجهة الشارية" in ln and i + 1 < len(lines):
                buyer = lines[i + 1]
        announced = ""
        opening = ""
        for i, ln in enumerate(lines):
            if "أُعلنت" in ln or "اعلنت" in ln:
                announced = lines[i + 1] if i + 1 < len(lines) else ""
            if "فض العروض" in ln:
                opening = lines[i + 1] if i + 1 < len(lines) else ""
        foodish = any(k.lower() in blob.lower() for k in FOOD)
        recs.append(
            {
                "id": tid,
                "title": title[:220],
                "buyer": buyer,
                "announced": announced,
                "opening": opening,
                "food_related": foodish,
                "url": url,
                "source": "ppa_lebanon",
            }
        )
    return pd.DataFrame(recs)


def refresh(c: httpx.Client):
    return run_connector(
        "lebanon_ppa",
        "tenders",
        LIST,
        "Lebanon Public Procurement Authority, public notices",
        lambda: fetch(c),
        notes="Latest PPA tender notices, flagged when food/catering/flour terms appear.",
        as_of_col="announced",
    )
