from __future__ import annotations

import re
from typing import Any

from ..analytics.entities import screen
from ..analytics.flows import competitor_unit_values, italy_series, market_brief, share_nowcast
from ..analytics.indicators import (
    all_indicators,
    chokepoint_stress,
    freight,
    landed_cost,
    lane_stress,
    port_stress,
    shelf_prices,
)
from ..catalog import MARKETS, PRODUCTS, country_by_any, country_name, product_by_any, resolve_region
from ..config import settings
from ..playbook.rules import run_playbook
from ..store import read_table

INTENTS = (
    "who",
    "trend",
    "compare",
    "price",
    "freight",
    "policy",
    "sanctions",
    "news",
    "what",
    "shelf",
    "screen",
)


def _entities(q: str) -> dict:
    low = q.lower()
    markets = []
    origins = []
    for word in re.findall(r"[A-Za-zÀ-ÿ']+", q):
        rec = country_by_any(word)
        if rec and rec.iso2 != "WORLD":
            if rec.iso2 in MARKETS:
                markets.append(rec.iso2)
            else:
                origins.append(rec.iso2)
    for name, codes in (
        ("gulf", resolve_region("gulf")),
        ("gcc", resolve_region("gcc")),
        ("east africa", resolve_region("east africa")),
        ("levant", resolve_region("levant")),
    ):
        if name in low:
            markets.extend(codes)
    product = product_by_any(q)
    if "semolina" in low:
        product = PRODUCTS["110311"]
    if "tomato" in low:
        product = PRODUCTS["200290"]
    if "durum" in low or "grano" in low:
        product = PRODUCTS["100119"]
    intent = "what"
    if any(w in low for w in ("who", "which", "share", "shipping", "ship")):
        intent = "who"
    if any(w in low for w in ("trend", "heading", "month", "since", "growth")):
        intent = "trend"
    if any(w in low for w in ("price", "usd/t", "per tonne", "unit value", "cost")):
        intent = "price"
    if any(w in low for w in ("freight", "hormuz", "suez", "jeddah", "jebel", "lane", "port")):
        intent = "freight"
    if any(w in low for w in ("dumping", "anti-dumping", "margin", "federal register", "safeguard")):
        intent = "policy"
    if any(w in low for w in ("sanction", "ofac", "screen", "sdn")):
        intent = "sanctions"
    if "news" in low or "headline" in low:
        intent = "news"
    if "shelf" in low or "retail" in low or "wfp" in low:
        intent = "shelf"
    if any(w in low for w in ("what should", "what do", "do about", "action")):
        intent = "what"
    return {
        "intent": intent,
        "markets": list(dict.fromkeys(markets)),
        "origins": list(dict.fromkeys(origins)),
        "product": product.code if product else "1902",
        "product_name": product.name if product else "pasta",
    }


def _llm_polish(text: str) -> str:
    approved = settings.approved_set()
    if "openai" not in approved and "ollama" not in approved:
        return text
    if not settings.openai_base_url or not settings.openai_api_key:
        return text
    try:
        import httpx

        r = httpx.post(
            settings.openai_base_url.rstrip("/") + "/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "messages": [
                    {"role": "system", "content": "Tighten this trade-desk answer. Do not add facts."},
                    {"role": "user", "content": text},
                ],
            },
            timeout=20,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception:
        return text


def ask(question: str, profile: dict | None = None) -> dict[str, Any]:
    q = (question or "").strip()
    ent = _entities(q)
    intent = ent["intent"]
    market = ent["markets"][0] if ent["markets"] else None
    answer: dict[str, Any] = {
        "question": q,
        "intent": intent,
        "entities": ent,
        "text": "",
        "table": [],
        "chart": [],
        "sources": [],
        "followups": [],
    }

    if intent == "who" and market:
        mb = market_brief(market)
        rows = mb.get("origins") or []
        answer["table"] = rows
        if rows:
            top = rows[0]
            answer["text"] = (
                f"{mb['name']} pasta (period {mb['period']}) is led by {top['origin_name']} "
                f"at {100*(top.get('share') or 0):.1f}% of the reconciled nowcast "
                f"(source {top.get('src')}, confidence {top.get('confidence')}). "
                + (
                    f"Italy is {100*mb['italy_share']:.1f}%."
                    if mb.get("italy_share") is not None
                    else "Italy does not appear in the latest cut."
                )
            )
        else:
            answer["text"] = f"No reconciled origin shares for {mb['name']} yet."
        answer["sources"] = [{"title": "Share nowcast", "note": "Comext + Comtrade + GASTAT + TİM"}]
        answer["followups"] = [f"Trend of Italian pasta into {mb['name']}", f"Unit values into {mb['name']}"]
        return answer

    if intent == "trend" and market:
        series = italy_series(market, "1902")
        if series.empty:
            series = italy_series(market, "190219")
        answer["chart"] = [
            {"period": r["period"], "tonnes": r["tonnes"], "unit": r["unit"]} for _, r in series.iterrows()
        ]
        if not series.empty:
            a, b = series.iloc[0], series.iloc[-1]
            answer["text"] = (
                f"Italy HS 1902 to {country_name(market)}: {a['tonnes']:.0f} t in {a['period']} → "
                f"{b['tonnes']:.0f} t in {b['period']}, unit value €{b['unit']:.0f}/t last print."
            )
        else:
            answer["text"] = f"No Comext monthly series for Italy → {country_name(market)}."
        answer["sources"] = [{"title": "Eurostat Comext", "url": "https://ec.europa.eu/eurostat"}]
        return answer

    if intent == "price":
        if market:
            lc = landed_cost(market)
            answer["table"] = lc["ladder"]
            if lc["ladder"]:
                top = lc["ladder"][0]
                answer["text"] = (
                    f"Cheapest print into {country_name(market)} is {top['origin']} "
                    f"at about ${top.get('landed_usd_t') or 0:.0f}/t landed (proxy). "
                    + lc["note"]
                )
            else:
                answer["text"] = f"No unit-value ladder for {country_name(market)} yet. " + lc["note"]
            return answer
        durum = all_indicators()["durum"]
        answer["chart"] = durum.get("series") or []
        answer["text"] = (
            f"Foggia/IT durum last {durum.get('as_of')}: €{durum.get('price_eur_t')} /t "
            f"({durum.get('delta'):+.1f} vs ~a month earlier)."
            if durum.get("price_eur_t")
            else "No durum print."
        )
        return answer

    if intent == "shelf":
        shelf = shelf_prices()
        answer["table"] = shelf
        if shelf:
            bits = [f"{s['name']} ${s['usd_per_kg']:.2f}/kg ({s['as_of']})" for s in shelf]
            answer["text"] = "WFP retail pasta: " + "; ".join(bits) + "."
        else:
            answer["text"] = "No WFP pasta prices in the snapshot."
        return answer

    if intent == "freight":
        lanes = lane_stress()
        answer["table"] = [{"id": l["id"], "dest": l["dest"], "score": l["score"], "label": l["label"]} for l in lanes]
        hormuz = next((c for c in chokepoint_stress() if "Hormuz" in c["name"]), None)
        answer["text"] = (
            f"Hormuz is running {hormuz['recent_avg']:.1f} ships/day vs a {hormuz['base_avg']:.1f} baseline ({100*hormuz['drop']:.0f}% down). "
            if hormuz
            else ""
        ) + "Lane stress is an index, not a rate."
        answer["chart"] = hormuz["series"] if hormuz else []
        return answer

    if intent == "policy":
        pasta = (all_indicators().get("policy") or {}).get("pasta_ad") or []
        answer["table"] = pasta
        g = next((p for p in pasta if p.get("garofalo_margin")), None)
        answer["text"] = (
            f"{g['title']} — Garofalo {g['garofalo_margin']}%, La Molisana {g.get('molisana_margin')}%."
            if g
            else "No pasta AD notice parsed."
        )
        answer["sources"] = [{"title": p.get("title"), "url": p.get("url")} for p in pasta[:4]]
        return answer

    if intent == "sanctions":
        # extract a name-like span
        name = re.sub(r"(?i)screen|ofac|sanction[s]?|check|for|the", " ", q).strip()
        hits = screen(name or q)
        answer["table"] = hits
        answer["text"] = (
            f"{len(hits)} fuzzy hits on '{name or q}'." if hits else f"No SDN/UN/UK hit above the cutoff for '{name or q}'."
        )
        return answer

    if intent == "news":
        news = all_indicators().get("news") or []
        answer["table"] = news[:12]
        answer["text"] = news[0]["title"] if news else "No headlines in the snapshot."
        return answer

    # default / what-to-do: playbook + BM25-ish keyword over insights and news
    insights = run_playbook(profile)
    scored = []
    tokens = set(re.findall(r"[a-z0-9]+", q.lower()))
    for ins in insights:
        blob = (ins["title"] + " " + ins["why"] + " " + " ".join(ins.get("tags") or [])).lower()
        overlap = len(tokens & set(re.findall(r"[a-z0-9]+", blob)))
        scored.append((overlap, ins))
    scored.sort(key=lambda x: (x[0], x[1]["score"]), reverse=True)
    best = [s[1] for s in scored if s[0] > 0][:3] or insights[:2]
    answer["table"] = [{"title": b["title"], "action": b["action"], "why": b["why"]} for b in best]
    answer["text"] = _llm_polish(" ".join(f"{b['title']}. {b['why']} Do: {b['action']}" for b in best))
    answer["followups"] = best[0].get("followups") if best else []
    return answer
