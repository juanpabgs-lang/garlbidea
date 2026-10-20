from __future__ import annotations

import httpx
import pandas as pd

from ..http import post_json
from .base import run_connector

URL = "https://webgate.ec.europa.eu/rasff-window/backend/public/notification/search/consolidated/"
QUERIES = ["pasta", "semolina", "durum", "tomato paste", "makarna"]


def _search(c: httpx.Client, subject: str) -> list[dict]:
    payload = {
        "parameters": {"pageNumber": 1, "itemsPerPage": 40},
        "subject": subject,
    }
    data = post_json(c, URL, payload)
    return list(data.get("notifications") or [])


def fetch(c: httpx.Client) -> pd.DataFrame:
    seen: set[str] = set()
    recs = []
    for q in QUERIES:
        for n in _search(c, q):
            ref = n.get("reference") or str(n.get("notifId"))
            if ref in seen:
                continue
            seen.add(ref)
            origins = n.get("originCountries") or []
            recs.append(
                {
                    "reference": ref,
                    "date": (n.get("ecValidationDate") or "")[:10],
                    "subject": n.get("subject"),
                    "notifying": (n.get("notifyingCountry") or {}).get("organizationName"),
                    "origin": ", ".join(o.get("organizationName", "") for o in origins),
                    "origin_iso": ", ".join(o.get("isoCode", "") for o in origins),
                    "category": (n.get("productCategory") or {}).get("description"),
                    "classification": (n.get("notificationClassification") or {}).get("description"),
                    "risk": (n.get("riskDecision") or {}).get("description"),
                    "published": n.get("published"),
                    "query": q,
                    "source": "rasff",
                    "url": f"https://webgate.ec.europa.eu/rasff-window/screen/notification/{n.get('notifId')}",
                }
            )
    return pd.DataFrame(recs)


def refresh(c: httpx.Client):
    return run_connector(
        "eu_rasff",
        "rasff",
        URL,
        "European Commission RASFF Window, public notifications",
        lambda: fetch(c),
        notes="Food-safety alerts mentioning pasta, semolina, durum or tomato paste.",
        as_of_col="date",
    )
