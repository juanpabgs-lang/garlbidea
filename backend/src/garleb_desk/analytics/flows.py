from __future__ import annotations

import pandas as pd

from ..catalog import COMPETITOR_ORIGINS, MARKETS, country_name, iso2
from ..store import read_table


def _comext() -> pd.DataFrame:
    df = read_table("comext_flows")
    if df.empty:
        return df
    df = df[df["product"].isin(["1902", "190219"])].copy()
    df["origin"] = df["origin"].map(lambda x: iso2(x) or x)
    df["market"] = df["market"].map(lambda x: iso2(x) or x)
    df["tonnes"] = pd.to_numeric(df["tonnes"], errors="coerce")
    df["value"] = pd.to_numeric(df["value_eur"], errors="coerce")
    df["unit"] = pd.to_numeric(df["unit_eur_t"], errors="coerce")
    df["currency"] = "EUR"
    df["src"] = "comext"
    df["confidence"] = 0.9
    return df[["period", "origin", "market", "product", "tonnes", "value", "unit", "currency", "src", "confidence"]]


def _comtrade() -> pd.DataFrame:
    df = read_table("comtrade_flows")
    if df.empty:
        return df
    recs = []
    for _, r in df.iterrows():
        product = str(r.get("product"))
        if product not in {"1902", "190219", "110311", "200290"}:
            continue
        flow = r.get("flow")
        reporter, partner = r.get("reporter"), r.get("partner")
        if partner == "WLD":
            continue
        if flow == "export":
            origin, market = reporter, partner
            src = "comtrade_export" if r.get("source") != "comtrade_mirror" else "comtrade_mirror"
        elif flow == "import":
            origin, market = partner, reporter
            src = "comtrade_import"
        else:
            continue
        recs.append(
            {
                "period": str(r.get("period")),
                "origin": iso2(origin) or origin,
                "market": iso2(market) or market,
                "product": product,
                "tonnes": r.get("tonnes"),
                "value": r.get("value_usd"),
                "unit": r.get("unit_usd_t"),
                "currency": "USD",
                "src": src,
                "confidence": {"comtrade_import": 0.85, "comtrade_export": 0.75, "comtrade_mirror": 0.7, "comtrade_monthly": 0.8}.get(src, 0.65),
            }
        )
    return pd.DataFrame(recs)


def _saudi() -> pd.DataFrame:
    df = read_table("saudi_trade")
    if df.empty:
        return df
    recs = []
    for _, r in df.iterrows():
        period = str(r.get("period") or "")
        if period and "-" not in period and len(period) == 6:
            period = f"{period[:4]}-{period[4:]}"
        iso = iso2(r.get("iso2") or r.get("country_id") or "")
        if r.get("flow") == "import":
            origin, market = iso, "SA"
        else:
            origin, market = "SA", iso
        if not origin or not market:
            continue
        recs.append(
            {
                "period": period,
                "origin": origin,
                "market": market,
                "product": "19",
                "tonnes": r.get("tonnes"),
                "value": r.get("value_usd"),
                "unit": r.get("unit_usd_t"),
                "currency": "USD",
                "src": "gastat",
                "confidence": 0.88,
            }
        )
    return pd.DataFrame(recs)


def _tim() -> pd.DataFrame:
    df = read_table("tim_exports")
    if df.empty:
        return df
    recs = []
    for _, r in df.iterrows():
        market = r.get("iso2")
        if not market:
            continue
        recs.append(
            {
                "period": str(r.get("as_of") or ""),
                "origin": "TR",
                "market": market,
                "product": "hububat",
                "tonnes": None,
                "value": r.get("sep_yoy_now_usd"),
                "unit": None,
                "currency": "USD",
                "src": "tim_proxy",
                "confidence": 0.45,
                "yoy": r.get("yoy_sep"),
                "yoy_ytd": r.get("yoy_ytd"),
            }
        )
    return pd.DataFrame(recs)


SOURCE_RANK = {
    "comext": 1,
    "gastat": 2,
    "comtrade_import": 3,
    "comtrade_monthly": 4,
    "comtrade_export": 5,
    "comtrade_mirror": 6,
    "tim_proxy": 7,
}


def flow_model() -> pd.DataFrame:
    frames = [_comext(), _comtrade(), _saudi(), _tim()]
    frames = [f for f in frames if f is not None and not f.empty]
    if not frames:
        return pd.DataFrame()
    raw = pd.concat(frames, ignore_index=True)
    raw["rank"] = raw["src"].map(SOURCE_RANK).fillna(9)
    raw = raw.sort_values(["market", "origin", "product", "period", "rank"])
    best = raw.drop_duplicates(["market", "origin", "product", "period"], keep="first")
    return best.reset_index(drop=True)


def _period_year(p: str) -> str:
    s = str(p)
    return s[:4]


def share_nowcast(market: str, product: str = "1902") -> pd.DataFrame:
    fm = flow_model()
    if fm.empty:
        return fm
    df = fm[(fm["market"] == market)].copy()
    if df.empty:
        return df
    # Prefer a multi-origin annual/import cut over an Italy-only monthly print.
    pasta = df[df["product"].isin(["1902", "190219"])]
    use = pasta if not pasta.empty else df[df["product"].isin(["19", "hububat"])]
    if use.empty:
        use = df
    use = use.copy()
    use["n_origins"] = use.groupby("period")["origin"].transform("nunique")
    # Score: more origins, then pasta HS, then recency, then source rank
    use["period_s"] = use["period"].astype(str)
    use["_score"] = (
        use["n_origins"].astype(float) * 10
        + use["product"].isin(["1902", "190219"]).astype(float) * 3
        + use["period_s"].str.len() * 0.1
        + use["period_s"].str.replace("-", "").str.slice(0, 6).astype(float) / 1e6
        - use["rank"].astype(float) * 0.05
    )
    best_period = use.sort_values("_score", ascending=False)["period_s"].iloc[0]
    slice_ = use[use["period_s"] == best_period]
    # Collapse 1902 + 190219 so Italy is not counted twice
    if slice_["product"].isin(["1902", "190219"]).any():
        slice_ = slice_[slice_["product"] == "1902"] if (slice_["product"] == "1902").any() else slice_
    slice_ = slice_.dropna(subset=["origin"]).drop_duplicates("origin")
    if slice_.empty:
        return slice_
    tonnes = pd.to_numeric(slice_["tonnes"], errors="coerce")
    value = pd.to_numeric(slice_["value"], errors="coerce")
    weight = tonnes.fillna(value)
    total = weight.sum()
    out = slice_.copy()
    out["share"] = weight / total if total else None
    out["origin_name"] = out["origin"].map(country_name)
    out["latest_period"] = best_period
    return out.sort_values("share", ascending=False)


def market_brief(market: str) -> dict:
    sn = share_nowcast(market)
    if sn.empty:
        return {"market": market, "name": country_name(market), "origins": [], "period": None}
    top = []
    for _, r in sn.head(8).iterrows():
        top.append(
            {
                "origin": r["origin"],
                "origin_name": country_name(r["origin"]),
                "share": None if pd.isna(r.get("share")) else float(r["share"]),
                "tonnes": None if pd.isna(r.get("tonnes")) else float(r["tonnes"]),
                "value": None if pd.isna(r.get("value")) else float(r["value"]),
                "unit": None if pd.isna(r.get("unit")) else float(r["unit"]),
                "currency": r.get("currency"),
                "src": r.get("src"),
                "confidence": r.get("confidence"),
            }
        )
    return {
        "market": market,
        "name": country_name(market),
        "period": sn["latest_period"].iloc[0],
        "origins": top,
        "italy_share": next((o["share"] for o in top if o["origin"] == "IT"), None),
        "turkey_share": next((o["share"] for o in top if o["origin"] == "TR"), None),
    }


def all_markets() -> list[dict]:
    return [market_brief(m) for m in MARKETS]


def italy_series(market: str, product: str = "1902") -> pd.DataFrame:
    df = _comext()
    if df.empty:
        return df
    return df[(df["market"] == market) & (df["product"] == product)].sort_values("period")


def competitor_unit_values(market: str) -> pd.DataFrame:
    fm = flow_model()
    if fm.empty:
        return fm
    df = fm[(fm["market"] == market) & (fm["origin"].isin(COMPETITOR_ORIGINS))]
    df = df[df["unit"].notna()]
    latest = df.sort_values("period").groupby("origin").tail(1)
    return latest
