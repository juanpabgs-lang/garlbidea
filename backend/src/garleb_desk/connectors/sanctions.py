from __future__ import annotations

import csv
import io
import xml.etree.ElementTree as ET

import httpx
import pandas as pd

from ..http import get_bytes, get_text
from .base import run_connector

OFAC = "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV"
UN = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
UK = "https://ofsistorage.blob.core.windows.net/publishlive/2022format/ConList.csv"


def fetch_ofac(c: httpx.Client) -> pd.DataFrame:
    raw = get_bytes(c, OFAC)
    text = raw.decode("latin-1", errors="replace")
    # SDN CSV is not a clean header file; parse quoted rows
    recs = []
    reader = csv.reader(io.StringIO(text))
    for row in reader:
        if len(row) < 2:
            continue
        name = row[1].strip() if len(row) > 1 else ""
        if not name or name.lower() == "name":
            continue
        recs.append(
            {
                "list": "OFAC_SDN",
                "uid": row[0],
                "name": name,
                "type": row[2] if len(row) > 2 else "",
                "programs": row[3] if len(row) > 3 else "",
                "source": "ofac",
            }
        )
    return pd.DataFrame(recs)


def fetch_un(c: httpx.Client) -> pd.DataFrame:
    raw = get_bytes(c, UN)
    root = ET.fromstring(raw)
    recs = []
    for node in root.iter():
        tag = node.tag.split("}")[-1]
        if tag not in {"INDIVIDUAL", "ENTITY"}:
            continue
        dataid = node.findtext(".//{*}DATAID") or node.findtext("DATAID") or ""
        first = " ".join(
            (node.findtext(f".//{p}") or "")
            for p in ("FIRST_NAME", "SECOND_NAME", "THIRD_NAME", "FOURTH_NAME")
        ).strip()
        name = first or (node.findtext(".//{*}NAME") or node.findtext("NAME") or "")
        if not name:
            continue
        recs.append({"list": "UN_CONSOLIDATED", "uid": dataid, "name": name, "type": tag, "programs": "", "source": "un"})
    return pd.DataFrame(recs)


def fetch_uk(c: httpx.Client) -> pd.DataFrame:
    raw = get_bytes(c, UK)
    # Stream names only — the full file is ~16MB.
    sample = raw[:4000].decode("utf-8", errors="replace")
    header = next(csv.reader(io.StringIO(sample)))
    name_idx = [i for i, col in enumerate(header) if "name" in col.lower()]
    uid_idx = next((i for i, col in enumerate(header) if col.lower() in {"unique id", "group id"}), 0)
    recs = []
    seen: set[str] = set()
    reader = csv.reader(io.StringIO(raw.decode("utf-8", errors="replace")))
    next(reader, None)
    for row in reader:
        parts = [row[i] for i in name_idx if i < len(row) and row[i]]
        name = " ".join(parts).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        recs.append(
            {
                "list": "UK_OFSI",
                "uid": row[uid_idx] if uid_idx < len(row) else "",
                "name": name,
                "type": "",
                "programs": "",
                "source": "uk_ofsi",
            }
        )
    return pd.DataFrame(recs)


def refresh_all(c: httpx.Client) -> list:
    return [
        run_connector(
            "ofac_sdn",
            "sanctions_ofac",
            OFAC,
            "US Treasury OFAC, public domain",
            lambda: fetch_ofac(c),
            notes="Full SDN list, names only used for counterparty screening.",
        ),
        run_connector(
            "un_sanctions",
            "sanctions_un",
            UN,
            "UN Security Council consolidated list",
            lambda: fetch_un(c),
            notes="UN consolidated individuals and entities.",
        ),
        run_connector(
            "uk_ofsi",
            "sanctions_uk",
            UK,
            "UK OFSI consolidated list, Open Government Licence",
            lambda: fetch_uk(c),
            notes="UK names for screening. EU list is a slot (25MB, same coverage as UN+OFAC for this desk).",
        ),
    ]
