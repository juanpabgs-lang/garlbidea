from __future__ import annotations

import httpx
import pandas as pd

from ..http import get_json
from .base import run_connector

URL = "https://en.sse.net.cn/currentIndex"


def fetch(c: httpx.Client) -> pd.DataFrame:
    recs = []
    for index in ("ccfi", "scfi"):
        data = get_json(c, URL, params={"indexName": index})
        payload = data.get("data") or data
        date = payload.get("currentDate")
        last = payload.get("lastDate")
        for line in payload.get("lineDataList") or []:
            props = line.get("properties") or {}
            recs.append(
                {
                    "index": index.upper(),
                    "date": date,
                    "prev_date": last,
                    "lane": props.get("lineName_EN") or props.get("lineName_ZH"),
                    "unit": props.get("unit_EN"),
                    "value": line.get("currentContent"),
                    "prev": line.get("lastContent"),
                    "pct": line.get("percentage"),
                    "source": "sse",
                }
            )
    return pd.DataFrame(recs)


def refresh(c: httpx.Client):
    return run_connector(
        "sse_freight",
        "freight_index",
        URL,
        "Shanghai Shipping Exchange weekly indices, public website",
        lambda: fetch(c),
        notes="CCFI composite and lane indices (Persian Gulf/Red Sea, East Africa, Med).",
        as_of_col="date",
    )
