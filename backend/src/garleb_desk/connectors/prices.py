from __future__ import annotations

import io
from datetime import datetime

import httpx
import pandas as pd

from ..http import get_bytes, get_json, get_text
from .base import run_connector

AGRIFOOD = "https://api.tech.ec.europa.eu/agrifood/api/cereal/prices"
FRED_WHEAT = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=PWHEAMTUSDM"
FFPI = "https://www.fao.org/media/docs/worldfoodsituationlibraries/wfs-library/food_price_indices_data.csv?sfvrsn=523ebd2a_84&download=true"
ECB = "https://data-api.ecb.europa.eu/service/data/EXR/D.USD+TRY+EGP.EUR.SP00.A"
ERAPI = "https://open.er-api.com/v6/latest/USD"


def _parse_euro_price(raw: str) -> float | None:
    if raw is None:
        return None
    s = str(raw).replace("€", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def fetch_durum(c: httpx.Client) -> pd.DataFrame:
    data = get_json(
        c,
        AGRIFOOD,
        params={"memberStateCodes": "IT,FR,ES,GR", "productCodes": "DUR", "beginDate": "01/01/2024"},
    )
    recs = []
    for row in data:
        recs.append(
            {
                "country": row.get("memberStateCode"),
                "market": row.get("marketName"),
                "stage": row.get("stageName"),
                "begin_date": row.get("beginDate"),
                "end_date": row.get("endDate"),
                "price_eur_t": _parse_euro_price(row.get("price")),
                "product": "durum",
                "source": "eu_agrifood",
            }
        )
    df = pd.DataFrame(recs)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["begin_date"], dayfirst=True, errors="coerce")
    return df


def fetch_wheat(c: httpx.Client) -> pd.DataFrame:
    text = get_text(c, FRED_WHEAT)
    df = pd.read_csv(io.StringIO(text))
    df.columns = ["date", "usd_t"]
    df = df[df["usd_t"] != "."]
    df["usd_t"] = pd.to_numeric(df["usd_t"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["source"] = "fred_pwheamtusdm"
    return df.dropna(subset=["date", "usd_t"])


def fetch_ffpi(c: httpx.Client) -> pd.DataFrame:
    raw = get_bytes(c, FFPI)
    text = raw.decode("utf-8", errors="replace")
    # FAO files often have a title row then a header
    lines = [ln for ln in text.splitlines() if ln.strip()]
    header_i = 0
    for i, ln in enumerate(lines[:12]):
        if "Date" in ln or "Food Price Index" in ln or ln.lower().startswith("date"):
            header_i = i
            break
    df = pd.read_csv(io.StringIO("\n".join(lines[header_i:])))
    df.columns = [str(c).strip() for c in df.columns]
    date_col = df.columns[0]
    df = df.rename(columns={date_col: "date"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    keep = [c for c in df.columns if c == "date" or "Food" in c or "Cereal" in c or "Oil" in c]
    df = df[keep]
    df["source"] = "fao_ffpi"
    return df


def fetch_fx(c: httpx.Client) -> pd.DataFrame:
    # Daily ECB EUR crosses
    text = get_text(c, ECB, params={"lastNObservations": 400, "format": "csvdata"})
    ecb = pd.read_csv(io.StringIO(text))
    recs = []
    if "CURRENCY" in ecb.columns and "OBS_VALUE" in ecb.columns:
        for _, r in ecb.iterrows():
            recs.append(
                {
                    "date": r.get("TIME_PERIOD"),
                    "pair": f"EUR{r.get('CURRENCY')}",
                    "rate": r.get("OBS_VALUE"),
                    "source": "ecb",
                }
            )
    spot = get_json(c, ERAPI)
    rates = spot.get("rates") or {}
    asof = spot.get("time_last_update_utc") or datetime.utcnow().isoformat()
    for cur, rate in rates.items():
        recs.append({"date": asof, "pair": f"USD{cur}", "rate": rate, "source": "open_er_api"})
    df = pd.DataFrame(recs)
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
    return df


def refresh_all(c: httpx.Client) -> list:
    return [
        run_connector(
            "eu_durum",
            "durum_prices",
            AGRIFOOD,
            "European Commission agri-food prices",
            lambda: fetch_durum(c),
            notes="Weekly durum wheat prices, Italy/France/Spain/Greece.",
            as_of_col="begin_date",
        ),
        run_connector(
            "fred_wheat",
            "wheat_prices",
            FRED_WHEAT,
            "IMF via FRED, public domain",
            lambda: fetch_wheat(c),
            notes="Global wheat price, monthly USD/t.",
            as_of_col="date",
        ),
        run_connector(
            "fao_ffpi",
            "ffpi",
            FFPI,
            "FAO, attribution required",
            lambda: fetch_ffpi(c),
            notes="FAO Food Price Index and Cereals sub-index.",
            as_of_col="date",
        ),
        run_connector(
            "fx",
            "fx",
            ECB,
            "ECB + open.er-api",
            lambda: fetch_fx(c),
            notes="EUR crosses from ECB; spot USD crosses from open.er-api.",
            as_of_col="date",
        ),
    ]
