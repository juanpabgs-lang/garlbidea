from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd
from hijridate import Gregorian, Hijri

from ..catalog import CHOKEPOINTS, LANES, PORTS, country_name
from ..store import read_table
from .flows import competitor_unit_values, italy_series, share_nowcast


def _num(s) -> float | None:
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    if pd.isna(v):
        return None
    return v


def durum_latest() -> dict:
    df = read_table("durum_prices")
    if df.empty:
        return {}
    df = df.dropna(subset=["price_eur_t"])
    foggia = df[df["market"].astype(str).str.contains("Foggia", case=False, na=False)]
    use = foggia if not foggia.empty else df[df["country"] == "IT"]
    if use.empty:
        use = df
    use = use.sort_values("date")
    last = use.iloc[-1]
    prev = use.iloc[-5] if len(use) > 5 else use.iloc[0]
    return {
        "market": last.get("market"),
        "price_eur_t": _num(last.get("price_eur_t")),
        "prev_eur_t": _num(prev.get("price_eur_t")),
        "as_of": str(last.get("begin_date") or last.get("date"))[:10],
        "delta": (_num(last.get("price_eur_t")) or 0) - (_num(prev.get("price_eur_t")) or 0),
        "series": [
            {"date": str(r.get("begin_date") or r.get("date"))[:10], "price": _num(r.get("price_eur_t"))}
            for _, r in use.tail(26).iterrows()
        ],
    }


def fx_spot() -> dict:
    df = read_table("fx")
    if df.empty:
        return {}
    out = {}
    er = df[df["source"] == "open_er_api"]
    for _, r in er.iterrows():
        out[r["pair"]] = _num(r["rate"])
    ecb = df[df["source"] == "ecb"].sort_values("date")
    for pair in ("EURUSD", "EURTRY"):
        sl = ecb[ecb["pair"] == pair]
        if not sl.empty:
            out[pair] = _num(sl.iloc[-1]["rate"])
            out[f"{pair}_as_of"] = str(sl.iloc[-1]["date"])
    return out


def chokepoint_stress() -> list[dict]:
    df = read_table("chokepoints")
    if df.empty:
        return []
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    out = []
    for cp in CHOKEPOINTS:
        sl = df[df["portid"] == cp.portid].dropna(subset=["date"]).sort_values("date")
        if sl.empty:
            continue
        recent = sl.tail(21)
        base = sl[(sl["date"] >= "2025-10-01") & (sl["date"] < "2026-03-01")]
        recent_avg = recent["n_total"].mean()
        base_avg = base["n_total"].mean() if not base.empty else sl.head(60)["n_total"].mean()
        drop = (base_avg - recent_avg) / base_avg if base_avg else 0
        out.append(
            {
                "id": cp.portid,
                "name": cp.name,
                "recent_avg": float(recent_avg),
                "base_avg": float(base_avg) if base_avg else None,
                "drop": float(drop),
                "as_of": sl["date"].max().date().isoformat(),
                "series": [
                    {"date": d.date().isoformat(), "n": float(v)}
                    for d, v in sl.set_index("date")["n_total"].resample("MS").mean().dropna().items()
                ],
            }
        )
    return out


def port_stress() -> list[dict]:
    df = read_table("ports")
    if df.empty:
        return []
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    out = []
    for p in PORTS:
        sl = df[df["portid"] == p.portid].dropna(subset=["date"]).sort_values("date")
        if sl.empty:
            continue
        recent = sl.tail(14)
        base = sl[(sl["date"] >= "2025-10-01") & (sl["date"] < "2026-03-01")]
        r = recent["portcalls_container"].mean()
        b = base["portcalls_container"].mean() if not base.empty else sl.head(40)["portcalls_container"].mean()
        drop = (b - r) / b if b else 0
        out.append(
            {
                "id": p.portid,
                "name": p.name,
                "country": p.country,
                "kind": p.kind,
                "lon": p.lon,
                "lat": p.lat,
                "recent_container": float(r) if pd.notna(r) else None,
                "base_container": float(b) if pd.notna(b) else None,
                "drop": float(drop) if pd.notna(drop) else None,
                "as_of": sl["date"].max().date().isoformat(),
            }
        )
    return out


def freight() -> list[dict]:
    df = read_table("freight_index")
    if df.empty:
        return []
    ccfi = df[df["index"] == "CCFI"]
    out = []
    for _, r in ccfi.iterrows():
        out.append(
            {
                "lane": r.get("lane"),
                "value": _num(r.get("value")),
                "prev": _num(r.get("prev")),
                "pct": _num(r.get("pct")),
                "as_of": r.get("date"),
            }
        )
    return out


def lane_stress() -> list[dict]:
    cps = {c["name"]: c for c in chokepoint_stress()}
    ports = {p["name"]: p for p in port_stress()}
    fr = freight()
    gulf = next((x for x in fr if x["lane"] and "PERSIAN" in x["lane"].upper()), None)
    out = []
    for lane in LANES:
        via_drop = [cps[v]["drop"] for v in lane["via"] if v in cps]
        dest = ports.get(lane["dest"])
        score = 0.0
        if via_drop:
            score += min(1.0, max(0.0, sum(via_drop) / len(via_drop)))
        if dest and dest.get("drop"):
            score = min(1.0, score * 0.6 + max(0.0, dest["drop"]) * 0.4)
        if gulf and "Hormuz" in str(lane["via"]):
            score = min(1.0, score + 0.15)
        label = "disrupted" if score > 0.65 else "stressed" if score > 0.35 else "open"
        out.append({**lane, "score": round(score, 3), "label": label, "dest_port": dest, "ccfi_gulf": gulf})
    return out


def shelf_prices() -> list[dict]:
    df = read_table("wfp_prices")
    if df.empty:
        return []
    pasta = df[df["commodity"].astype(str).str.contains("Pasta", case=False, na=False)]
    pasta = pasta.dropna(subset=["usd_per_kg"])
    out = []
    for iso, sl in pasta.groupby("market_iso2"):
        sl = sl.sort_values("date")
        last_date = sl["date"].max()
        latest = sl[sl["date"] == last_date]
        out.append(
            {
                "market": iso,
                "name": country_name(iso),
                "usd_per_kg": float(latest["usd_per_kg"].median()),
                "as_of": str(last_date)[:10],
                "n_markets": int(latest["market"].nunique()) if "market" in latest else len(latest),
                "series": [
                    {"date": str(d)[:10], "usd_per_kg": float(g["usd_per_kg"].median())}
                    for d, g in sl.groupby("date")
                ][-18:],
            }
        )
    return out


def turkish_pressure() -> dict:
    fx = fx_spot()
    tryy = fx.get("USDTRY") or fx.get("EURTRY")
    tim = read_table("tim_exports")
    yoy = None
    if not tim.empty:
        focus = tim[tim["iso2"].isin(["LB", "SA", "AE", "KE", "SO", "DJ"])]
        if not focus.empty:
            yoy = float(focus["yoy_sep"].median()) if "yoy_sep" in focus else None
    news = read_table("news")
    tmo = []
    if not news.empty:
        tmo = [
            r["title"]
            for _, r in news.iterrows()
            if "TMO" in str(r.get("title")) or "buğday" in str(r.get("title")).lower()
        ][:5]
    score = 0.0
    if tryy and tryy > 45:
        score += 0.35
    if yoy and yoy > 0.1:
        score += 0.3
    if tmo:
        score += 0.2
    return {
        "usdtry": tryy,
        "tim_yoy_median": yoy,
        "tmo_headlines": tmo,
        "score": min(1.0, score),
        "label": "elevated" if score > 0.5 else "watch",
    }


def quality_radar() -> list[dict]:
    recs = []
    rasff = read_table("rasff")
    if not rasff.empty:
        for _, r in rasff.iterrows():
            recs.append(
                {
                    "system": "RASFF",
                    "date": r.get("date"),
                    "subject": r.get("subject"),
                    "origin": r.get("origin"),
                    "risk": r.get("risk"),
                    "url": r.get("url"),
                }
            )
    fda = read_table("fda_recalls")
    if not fda.empty:
        for _, r in fda.iterrows():
            recs.append(
                {
                    "system": "FDA",
                    "date": r.get("date"),
                    "subject": r.get("product"),
                    "origin": r.get("country"),
                    "risk": r.get("classification"),
                    "url": r.get("url"),
                }
            )
    recs.sort(key=lambda x: str(x.get("date") or ""), reverse=True)
    return recs[:25]


def policy_radar() -> dict:
    notices = read_table("policy_notices")
    pasta = []
    ofac = []
    if not notices.empty:
        for _, r in notices.iterrows():
            item = {
                "document_number": r.get("document_number"),
                "title": r.get("title"),
                "date": r.get("publication_date"),
                "abstract": r.get("abstract"),
                "url": r.get("html_url"),
                "garofalo_margin": _num(r.get("garofalo_margin")),
                "molisana_margin": _num(r.get("molisana_margin")),
            }
            if r.get("kind") == "ofac":
                ofac.append(item)
            else:
                pasta.append(item)
    gaz = read_table("gazette")
    gaz_hits = []
    if not gaz.empty:
        gaz_hits = gaz[gaz["relevant"] == True].to_dict("records")  # noqa: E712
    tenders = read_table("tenders")
    food = []
    if not tenders.empty:
        food = tenders[tenders["food_related"] == True].to_dict("records")  # noqa: E712
        if food == []:
            food = tenders.head(6).to_dict("records")
    return {"pasta_ad": pasta, "ofac": ofac, "gazette": gaz_hits, "tenders": food}


def news_pack() -> list[dict]:
    df = read_table("news")
    if df.empty:
        return []
    df = df.sort_values("date", ascending=False)
    return df.head(40).to_dict("records")


def ramadan() -> dict:
    # Next Ramadan 1 from today
    today = date.today()
    year = today.year
    start = None
    for y in (year, year + 1, year + 2):
        try:
            # 1 Ramadan of hijri year that overlaps y
            # Ramadan 1447 ~ Feb 2026; 1448 ~ Feb 2027
            for hy in range(1446, 1452):
                g = Hijri(hy, 9, 1).to_gregorian()
                d = date(g.year, g.month, g.day)
                if d >= today:
                    start = d
                    hijri_year = hy
                    break
            if start:
                break
        except Exception:
            continue
    if not start:
        return {}
    # order-by = start minus typical 25-day Med-Gulf transit minus 10-day warehouse
    order_by = start - timedelta(days=35)
    return {
        "hijri_year": hijri_year,
        "start": start.isoformat(),
        "order_by": order_by.isoformat(),
        "days_to_start": (start - today).days,
        "days_to_order_by": (order_by - today).days,
    }


def landed_cost(market: str = "AE") -> dict:
    it = italy_series(market, "1902")
    fx = fx_spot()
    eurusd = fx.get("EURUSD") or 1.12
    it_unit = None
    if not it.empty:
        last = it.dropna(subset=["unit"]).iloc[-1] if it["unit"].notna().any() else None
        if last is not None:
            it_unit = _num(last["unit"]) * eurusd
    comps = competitor_unit_values(market)
    ladder = []
    if it_unit:
        ladder.append({"origin": "IT", "fob_usd_t": it_unit, "src": "comext"})
    if not comps.empty:
        for _, r in comps.iterrows():
            unit = _num(r.get("unit"))
            if unit is None:
                continue
            if r.get("currency") == "EUR":
                unit *= eurusd
            ladder.append({"origin": r["origin"], "fob_usd_t": unit, "src": r.get("src")})
    lanes = lane_stress()
    dest_lane = next((l for l in lanes if l.get("market") == market), lanes[0] if lanes else None)
    penalty = 80 * (dest_lane["score"] if dest_lane else 0.3)
    for row in ladder:
        row["freight_proxy"] = 180 + penalty
        row["landed_usd_t"] = (row["fob_usd_t"] or 0) + row["freight_proxy"]
    return {
        "market": market,
        "eurusd": eurusd,
        "lane": dest_lane,
        "ladder": sorted(ladder, key=lambda x: x.get("landed_usd_t") or 9e9),
        "note": "Freight is a documented proxy from CCFI + lane stress, not a contract rate.",
    }


def ticker() -> list[dict]:
    d = durum_latest()
    fx = fx_spot()
    cps = chokepoint_stress()
    hormuz = next((c for c in cps if "Hormuz" in c["name"]), None)
    suez = next((c for c in cps if "Suez" in c["name"]), None)
    ports = port_stress()
    jebel = next((p for p in ports if p["name"] == "Jebel Ali"), None)
    fr = freight()
    gulf = next((x for x in fr if x["lane"] and "PERSIAN" in x["lane"].upper()), None)
    wheat = read_table("wheat_prices")
    wheat_last = None
    if not wheat.empty:
        wheat = wheat.sort_values("date")
        wheat_last = {"date": str(wheat.iloc[-1]["date"])[:10], "usd_t": _num(wheat.iloc[-1]["usd_t"])}
    return [
        {"id": "durum", "label": "Foggia durum", "value": d.get("price_eur_t"), "unit": "€/t", "delta": d.get("delta"), "as_of": d.get("as_of")},
        {"id": "wheat", "label": "IMF wheat", "value": wheat_last["usd_t"] if wheat_last else None, "unit": "$/t", "as_of": wheat_last["date"] if wheat_last else None},
        {"id": "eurusd", "label": "EUR/USD", "value": fx.get("EURUSD"), "as_of": fx.get("EURUSD_as_of")},
        {"id": "usdtry", "label": "USD/TRY", "value": fx.get("USDTRY")},
        {"id": "hormuz", "label": "Hormuz ships/day", "value": hormuz["recent_avg"] if hormuz else None, "delta_pct": hormuz["drop"] if hormuz else None, "as_of": hormuz["as_of"] if hormuz else None},
        {"id": "suez", "label": "Suez ships/day", "value": suez["recent_avg"] if suez else None, "as_of": suez["as_of"] if suez else None},
        {"id": "jebel", "label": "Jebel Ali box calls", "value": jebel["recent_container"] if jebel else None, "delta_pct": jebel["drop"] if jebel else None},
        {"id": "ccfi_gulf", "label": "CCFI Gulf/Red Sea", "value": gulf["value"] if gulf else None, "delta_pct": (gulf["pct"] / 100.0) if gulf and gulf.get("pct") is not None else None, "as_of": gulf["as_of"] if gulf else None},
    ]


def all_indicators() -> dict:
    return {
        "durum": durum_latest(),
        "fx": fx_spot(),
        "chokepoints": chokepoint_stress(),
        "ports": port_stress(),
        "freight": freight(),
        "lanes": lane_stress(),
        "shelf": shelf_prices(),
        "turkish_pressure": turkish_pressure(),
        "quality": quality_radar(),
        "policy": policy_radar(),
        "news": news_pack(),
        "ramadan": ramadan(),
        "ticker": ticker(),
    }
