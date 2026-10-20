from __future__ import annotations

import httpx
import pandas as pd

from ..http import get_json
from .base import run_connector

OPENFDA = "https://api.fda.gov/food/enforcement.json"


def fetch(c: httpx.Client) -> pd.DataFrame:
    recs = []
    for q in (
        'product_description:"pasta"',
        'product_description:"spaghetti"',
        'product_description:"macaroni"',
        'product_description:"semolina"',
        'product_description:"tomato paste"',
    ):
        data = get_json(c, OPENFDA, params={"search": q, "limit": 20})
        for row in data.get("results") or []:
            recs.append(
                {
                    "recall_number": row.get("recall_number"),
                    "date": row.get("recall_initiation_date") or row.get("report_date"),
                    "status": row.get("status"),
                    "classification": row.get("classification"),
                    "product": (row.get("product_description") or "")[:240],
                    "reason": (row.get("reason_for_recall") or "")[:240],
                    "recalling_firm": row.get("recalling_firm"),
                    "country": row.get("country"),
                    "state": row.get("state"),
                    "source": "openfda",
                    "url": "https://api.fda.gov/food/enforcement.json",
                }
            )
    df = pd.DataFrame(recs)
    if df.empty:
        return df
    return df.drop_duplicates(subset=["recall_number"])


def refresh(c: httpx.Client):
    return run_connector(
        "openfda_recalls",
        "fda_recalls",
        OPENFDA,
        "openFDA, public domain",
        lambda: fetch(c),
        notes="US food recalls mentioning pasta, semolina or tomato paste. Import-refusal CSV is a slot (no stable public dump without a session).",
        as_of_col="date",
    )
