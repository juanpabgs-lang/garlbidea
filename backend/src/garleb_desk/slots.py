from __future__ import annotations

from .config import settings
from .connectors.base import SourceResult

SLOTS = [
    {
        "name": "us_census_trade",
        "table": "census_pasta",
        "kind": "free_key",
        "reason": "Census International Trade API now requires a free key (CENSUS_API_KEY). Needed for US monthly imports of Italian vs Turkish pasta — the AD diversion watch.",
        "url": "https://api.census.gov/data/timeseries/intltrade/imports/hs",
    },
    {
        "name": "wto_eping",
        "table": "eping",
        "kind": "free_key",
        "reason": "WTO ePing SPS/TBT notifications. Public portal; API key or session required for bulk.",
        "url": "https://epingalert.org/en",
    },
    {
        "name": "comtrade_plus",
        "table": "comtrade_plus",
        "kind": "free_key",
        "reason": "Full Comtrade Plus (COMTRADE_API_KEY) unlocks 2026 monthly for more reporters.",
        "url": "https://comtradeplus.un.org",
    },
    {
        "name": "usda_gain",
        "table": "usda_gain",
        "kind": "free_key",
        "reason": "USDA GAIN attaché reports (Turkey durum, GCC food). Endpoint moved; needs current key.",
        "url": "https://gain.fas.usda.gov/",
    },
    {
        "name": "aisstream",
        "table": "ais",
        "kind": "free_key",
        "reason": "Live AIS for Hormuz / Jebel Ali / Jeddah. Free websocket key, not approved in this environment.",
        "url": "https://aisstream.io",
    },
    {
        "name": "ungm_tenders",
        "table": "ungm",
        "kind": "session",
        "reason": "UNGM food-aid pasta tenders. Search API rejected anonymous POST from this host.",
        "url": "https://www.ungm.org/Public/Notice",
    },
    {
        "name": "kap_disclosures",
        "table": "kap",
        "kind": "session",
        "reason": "Borsa Istanbul KAP API for listed Turkish millers (Oba, Golda). Needs a session cookie.",
        "url": "https://www.kap.org.tr",
    },
    {
        "name": "kenya_gazette",
        "table": "kenya_gazette",
        "kind": "pdf",
        "reason": "Kenya Law gazettes are paginated PDFs. Duty/safeguard changes need a PDF parser pass.",
        "url": "https://new.kenyalaw.org/gazettes/",
    },
    {
        "name": "suez_circulars",
        "table": "sca",
        "kind": "pdf",
        "reason": "Suez Canal Authority circulars are HTML/PDF, no machine feed.",
        "url": "https://www.suezcanal.gov.eg",
    },
    {
        "name": "lebanon_customs",
        "table": "lb_customs",
        "kind": "geo_blocked",
        "reason": "customs.gov.lb did not respond from this VM. Needs the regional relay in Beirut/Dubai.",
        "url": "https://www.customs.gov.lb",
    },
    {
        "name": "knbs_kpa",
        "table": "ke_ports",
        "kind": "geo_blocked",
        "reason": "KNBS and KPA timed out. Mombasa line-ups and Kenya trade releases via regional relay.",
        "url": "https://www.knbs.or.ke",
    },
    {
        "name": "uae_fcsc",
        "table": "ae_prices",
        "kind": "geo_blocked",
        "reason": "FCSC returned 403 from this host.",
        "url": "https://fcsc.gov.ae/en-us",
    },
    {
        "name": "tradeint",
        "table": "shipments",
        "kind": "licensed",
        "reason": "TradeInt B/L + customs. License plus GARLEB NDA provider approval required. CSV importer is ready.",
        "url": "https://tradeint.com",
    },
    {
        "name": "drewry_xeneta",
        "table": "contract_rates",
        "kind": "licensed",
        "reason": "Contract container rates. CCFI is the public proxy until a provider is approved.",
        "url": "https://www.drewry.co.uk",
    },
    {
        "name": "eu_sanctions_full",
        "table": "sanctions_eu",
        "kind": "deferred",
        "reason": "EU consolidated list is 25MB. OFAC + UN + UK already cover the desk's counterparties.",
        "url": "https://webgate.ec.europa.eu/fsd/fsf",
    },
]


def register_slots() -> list[SourceResult]:
    out = []
    for s in SLOTS:
        # If a free-key slot is actually configured, leave it as a slot until a connector exists.
        if s["name"] == "us_census_trade" and settings.census_api_key:
            s = {**s, "reason": s["reason"] + " Key is present; connector not wired this build."}
        if s["name"] == "comtrade_plus" and settings.comtrade_api_key:
            s = {**s, "reason": s["reason"] + " Key is present; connector not wired this build."}
        if s["kind"] == "geo_blocked" and settings.regional_relay_url:
            s = {**s, "reason": s["reason"] + " Relay URL is set; fetcher not pointed at this host yet."}
        status = "licensed" if s["kind"] == "licensed" else "slot"
        if s["kind"] == "geo_blocked":
            status = "blocked"
        res = SourceResult(
            name=s["name"],
            table=s["table"],
            status=status,
            rows=0,
            as_of=None,
            source_url=s["url"],
            license="n/a",
            notes=s["reason"],
        )
        res.persist()
        out.append(res)
    return out


def slot_payload() -> list[dict]:
    return SLOTS
