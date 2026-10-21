from __future__ import annotations

from datetime import datetime

import httpx
import pandas as pd

from ..catalog import CHOKEPOINTS, PORTS
from ..http import get_json
from .base import run_connector

BASE = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services"


def _query(c: httpx.Client, svc: str, where: str, fields: str = "*", n: int = 2000) -> list[dict]:
    url = f"{BASE}/{svc}/FeatureServer/0/query"
    rows: list[dict] = []
    offset = 0
    while True:
        payload = get_json(
            c,
            url,
            params={
                "where": where,
                "outFields": fields,
                "returnGeometry": "false",
                "f": "json",
                "resultRecordCount": n,
                "resultOffset": offset,
                "orderByFields": "date ASC",
            },
        )
        chunk = [f.get("attributes", {}) for f in payload.get("features", [])]
        if not chunk:
            break
        first_key = (chunk[0].get("portid"), chunk[0].get("date"))
        if rows and (rows[0].get("portid"), rows[0].get("date")) == first_key and offset:
            break
        rows.extend(chunk)
        if len(chunk) < n:
            break
        offset += n
        if offset > 4000:
            break
    return rows


def _ts(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, str):
        return v[:10]
    try:
        return datetime.utcfromtimestamp(int(v) / 1000).strftime("%Y-%m-%d")
    except Exception:
        return str(v)


def fetch_chokepoints(c: httpx.Client) -> pd.DataFrame:
    frames = []
    fields = "date,portid,portname,n_total,n_container,n_tanker,n_cargo,capacity,capacity_container"
    for cp in CHOKEPOINTS:
        rows = _query(
            c,
            "Daily_Chokepoints_Data",
            f"portid='{cp.portid}' AND date>=DATE '2025-01-01'",
            fields,
            n=2000,
        )
        if rows:
            frames.append(pd.DataFrame(rows))
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if df.empty:
        return df
    df["date"] = df["date"].map(_ts)
    df["source"] = "imf_portwatch"
    return df


def fetch_ports(c: httpx.Client) -> pd.DataFrame:
    frames = []
    fields = "date,portid,portname,country,portcalls,portcalls_container,import,import_container,export,export_container"
    for p in PORTS:
        try:
            rows = _query(
                c,
                "Daily_Ports_Data",
                f"portid='{p.portid}' AND date>=DATE '2025-07-01'",
                fields,
                n=2000,
            )
        except Exception:
            rows = _query(
                c,
                "Daily_Ports_Data",
                f"portname='{p.name}' AND date>=DATE '2025-07-01'",
                fields,
                n=2000,
            )
        if rows:
            frames.append(pd.DataFrame(rows))
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if df.empty:
        return df
    df["date"] = df["date"].map(_ts)
    df["source"] = "imf_portwatch"
    return df


def refresh_all(c: httpx.Client) -> list:
    return [
        run_connector(
            "portwatch_chokepoints",
            "chokepoints",
            "https://portwatch.imf.org",
            "IMF PortWatch, CC BY 4.0",
            lambda: fetch_chokepoints(c),
            notes="Daily vessel counts at Hormuz, Bab el-Mandeb, Suez, Cape, Gibraltar.",
            as_of_col="date",
        ),
        run_connector(
            "portwatch_ports",
            "ports",
            "https://portwatch.imf.org",
            "IMF PortWatch, CC BY 4.0",
            lambda: fetch_ports(c),
            notes="Daily port calls at GARLEB origin and destination ports.",
            as_of_col="date",
        ),
    ]
