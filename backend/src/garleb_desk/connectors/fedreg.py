from __future__ import annotations

import re

import httpx
import pandas as pd

from ..http import get_json, get_text
from .base import run_connector

API = "https://www.federalregister.gov/api/v1/documents.json"
DOC = "https://www.federalregister.gov/api/v1/documents/{n}.json"


MARGIN_RE = re.compile(
    r"(?P<name>La Molisana, S\.p\.A\.|Pastificio Lucio Garofalo S\.p\.A\.|Companies Not Selected[^\n]*|Non-Selected Companies[^\n]*|Non-Individually Examined Companies[^\n]*)"
    r"\.+\s+(?P<margin>\d+\.\d+)",
    re.I,
)


def _search(c: httpx.Client, term: str, per_page: int = 20) -> list[dict]:
    data = get_json(
        c,
        API,
        params={
            "conditions[term]": term,
            "order": "newest",
            "per_page": per_page,
            "fields[]": ["document_number", "title", "publication_date", "abstract", "html_url", "type"],
        },
    )
    return list(data.get("results") or [])


def _parse_margins(text: str) -> list[dict]:
    out = []
    for m in MARGIN_RE.finditer(text):
        name = re.sub(r"\s+", " ", m.group("name")).strip()
        if "Garofalo" in name:
            firm = "Garofalo"
        elif "Molisana" in name:
            firm = "La Molisana"
        else:
            firm = "others"
        out.append({"firm": firm, "raw_name": name, "margin_pct": float(m.group("margin"))})
    return out


def fetch(c: httpx.Client) -> pd.DataFrame:
    recs = []
    pasta = _search(c, '"certain pasta from italy"', 25)
    ofac = get_json(
        c,
        API,
        params={
            "conditions[agencies][]": "foreign-assets-control-office",
            "order": "newest",
            "per_page": 12,
            "fields[]": ["document_number", "title", "publication_date", "abstract", "html_url", "raw_text_url"],
        },
    ).get("results", [])
    for row in pasta:
        doc_no = row.get("document_number")
        meta = get_json(c, DOC.format(n=doc_no))
        text = ""
        url = meta.get("raw_text_url")
        if url:
            try:
                text = get_text(c, url)
            except Exception:
                text = ""
        margins = _parse_margins(text)
        recs.append(
            {
                "kind": "trade_remedy",
                "document_number": doc_no,
                "title": row.get("title"),
                "publication_date": row.get("publication_date"),
                "abstract": (meta.get("abstract") or row.get("abstract") or "")[:800],
                "html_url": row.get("html_url") or meta.get("html_url"),
                "margins_json": margins,
                "garofalo_margin": next((m["margin_pct"] for m in margins if m["firm"] == "Garofalo"), None),
                "molisana_margin": next((m["margin_pct"] for m in margins if m["firm"] == "La Molisana"), None),
                "source": "federal_register",
            }
        )
    for row in ofac:
        recs.append(
            {
                "kind": "ofac",
                "document_number": row.get("document_number"),
                "title": row.get("title"),
                "publication_date": row.get("publication_date"),
                "abstract": (row.get("abstract") or "")[:800],
                "html_url": row.get("html_url"),
                "margins_json": [],
                "garofalo_margin": None,
                "molisana_margin": None,
                "source": "federal_register",
            }
        )
    return pd.DataFrame(recs)


def refresh(c: httpx.Client):
    return run_connector(
        "federal_register",
        "policy_notices",
        "https://www.federalregister.gov",
        "US Federal Register, public domain",
        lambda: fetch(c),
        notes="US AD/CVD pasta notices with parsed dumping margins, plus latest OFAC actions.",
        as_of_col="publication_date",
    )
