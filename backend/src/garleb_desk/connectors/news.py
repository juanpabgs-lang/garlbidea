from __future__ import annotations

import email.utils
import re
from html import unescape
from xml.etree import ElementTree as ET

import httpx
import pandas as pd

from ..http import get_text
from .base import run_connector

QUERIES = [
    ("en", "US", "US:en", "pasta export Kenya OR Gulf OR Lebanon OR Somalia when:45d"),
    ("en", "US", "US:en", "durum wheat OR semolina price Foggia OR Puglia when:30d"),
    ("en", "US", "US:en", "Strait of Hormuz shipping container when:21d"),
    ("en", "US", "US:en", "Jeddah port Houthi OR Red Sea shipping when:21d"),
    ("en", "US", "US:en", "Gemini Jebel Ali Khor Fakkan when:45d"),
    ("en", "US", "US:en", "Ebro Foods Garofalo pasta when:180d"),
    ("tr", "TR", "TR:tr", "makarna ihracatı when:60d"),
    ("tr", "TR", "TR:tr", "durum buğdayı TMO when:45d"),
    ("it", "IT", "IT:it", "grano duro prezzo Foggia when:30d"),
    ("it", "IT", "IT:it", "Pasta Garofalo OR Pastificio Garofalo when:180d"),
    ("ar", "LB", "LB:ar", "معكرونة لبنان OR قمح when:60d"),
]


def _rss(c: httpx.Client, q: str, hl: str, gl: str, ceid: str) -> list[dict]:
    url = "https://news.google.com/rss/search"
    xml = get_text(c, url, params={"q": q, "hl": hl, "gl": gl, "ceid": ceid})
    root = ET.fromstring(xml)
    items = []
    for item in root.findall(".//item"):
        title = unescape((item.findtext("title") or "").strip())
        link = (item.findtext("link") or "").strip()
        pub = item.findtext("pubDate") or ""
        source = ""
        src = item.find("source")
        if src is not None and src.text:
            source = src.text.strip()
        try:
            dt = email.utils.parsedate_to_datetime(pub).date().isoformat()
        except Exception:
            dt = pub
        items.append({"title": title, "url": link, "date": dt, "outlet": source, "query": q, "lang": hl})
    return items


def fetch(c: httpx.Client) -> pd.DataFrame:
    recs = []
    seen: set[str] = set()
    for hl, gl, ceid, q in QUERIES:
        try:
            rows = _rss(c, q, hl, gl, ceid)
        except Exception:
            continue
        for r in rows:
            key = re.sub(r"\W+", " ", r["title"].lower())[:80]
            if key in seen:
                continue
            seen.add(key)
            recs.append({**r, "source": "google_news_rss"})
    return pd.DataFrame(recs)


def refresh(c: httpx.Client):
    return run_connector(
        "press_pack",
        "news",
        "https://news.google.com/rss",
        "Publisher copyright remains with outlets; titles used as citations",
        lambda: fetch(c),
        notes="English, Turkish, Italian and Arabic RSS packs on pasta, durum, Gulf routing and TMO.",
        as_of_col="date",
    )
