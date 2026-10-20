from __future__ import annotations

from datetime import date, timedelta

from ..analytics.flows import italy_series, market_brief, share_nowcast
from ..analytics.indicators import all_indicators, landed_cost
from ..catalog import country_name


def _insight(**kwargs) -> dict:
    kwargs.setdefault("confidence", 0.7)
    kwargs.setdefault("sources", [])
    kwargs.setdefault("followups", [])
    return kwargs


def run_playbook(profile: dict | None = None) -> list[dict]:
    ind = all_indicators()
    insights: list[dict] = []
    profile = profile or {}
    markets = profile.get("markets") or ["LB", "AE", "SA", "KE"]

    # 1. US AD Garofalo
    pasta = (ind.get("policy") or {}).get("pasta_ad") or []
    latest = next((p for p in pasta if p.get("garofalo_margin")), pasta[0] if pasta else None)
    if latest and latest.get("garofalo_margin"):
        hearing = None
        if latest.get("date"):
            try:
                hearing = (date.fromisoformat(str(latest["date"])[:10]) + timedelta(days=32)).isoformat()
            except ValueError:
                hearing = None
        insights.append(
            _insight(
                id="ad_garofalo",
                title=f"US pasta AD prelim: Garofalo {latest['garofalo_margin']:.2f}%",
                magnitude=latest["garofalo_margin"],
                urgency=0.85,
                relevance=0.95,
                confidence=0.95,
                why=(
                    f"Commerce preliminarily assigned Pastificio Lucio Garofalo S.p.A. a {latest['garofalo_margin']:.2f}% "
                    f"dumping margin (La Molisana {latest.get('molisana_margin') or 'n/a'}%). "
                    "This is a group-level cash-deposit risk on US-bound pasta and a diversion risk into GARLEB markets "
                    "if Italian mills steer volume away from the US."
                ),
                action=(
                    "Flag any US-bound Garofalo cargoes for the new deposit. Ask mills for a 2027 allocation that "
                    f"absorbs diverted volume into {', '.join(country_name(m) for m in markets[:3])}. "
                    + (f"Hearing-request window closes around {hearing}." if hearing else "")
                ),
                owner="compliance + procurement",
                timing=f"hearing ~ {hearing}" if hearing else "this week",
                sources=[{"title": latest.get("title"), "url": latest.get("url"), "as_of": latest.get("date")}],
                followups=["What were Garofalo's last three AD margins?", "Who else is under the Italy pasta order?"],
                tags=["policy", "group"],
            )
        )

    # 2. Hormuz / Jebel Ali
    lanes = ind.get("lanes") or []
    jebel = next((l for l in lanes if l.get("dest") == "Jebel Ali"), None)
    if jebel and jebel["score"] > 0.5:
        insights.append(
            _insight(
                id="gulf_route",
                title="Gulf lane is disrupted: Jebel Ali is not the default",
                magnitude=jebel["score"],
                urgency=0.95,
                relevance=0.9,
                confidence=0.9,
                why=(
                    "Hormuz transits have collapsed versus late-2025, and Jebel Ali container calls are a fraction of "
                    "the pre-war baseline. Gemini has already swapped Jebel Ali for Khor Fakkan. Italian pasta into "
                    "the UAE and the Saudi dhow/truck re-export chain is arriving late or not at all."
                ),
                action=(
                    "Book Khor Fakkan, Fujairah or Sohar plus trucking. Price war-risk. Build 3–4 weeks of UAE/Oman "
                    "safety stock before Ramadan order-by. Do not quote Jebel Ali as the discharge port without a live line."
                ),
                owner="logistics",
                timing="today",
                sources=[{"title": "IMF PortWatch", "url": "https://portwatch.imf.org"}],
                followups=["Compare Khor Fakkan vs Sohar vs Fujairah calls", "What is CCFI Gulf/Red Sea vs Med?"],
                tags=["freight", "gulf"],
            )
        )

    # 3. Jeddah / Red Sea
    jeddah = next((p for p in ind.get("ports") or [] if p["name"] == "Jeddah"), None)
    if jeddah and (jeddah.get("drop") or 0) > 0.5:
        insights.append(
            _insight(
                id="red_sea",
                title="Jeddah container calls have collapsed",
                magnitude=jeddah.get("drop"),
                urgency=0.9,
                relevance=0.8,
                confidence=0.85,
                why=(
                    "Houthi strikes and flight cancellations into Jeddah have emptied the box berth. "
                    "Italy-to-Saudi pasta that used to clear Jeddah is a late or cancelled cargo."
                ),
                action="Offer Dammam or King Abdullah as the west-coast alternative, or truck from Sohar/Fujairah. Requote CIF Jeddah with a war-risk adder and a 3-week buffer.",
                owner="KSA desk",
                timing="this week",
                sources=[{"title": "IMF PortWatch Jeddah", "url": "https://portwatch.imf.org"}],
                tags=["freight", "ksa"],
            )
        )

    # 4. Italy to Saudi surge
    it_sa = italy_series("SA", "1902")
    if not it_sa.empty and len(it_sa) >= 4:
        last4 = it_sa.tail(4)
        first, last = last4.iloc[0]["tonnes"], last4.iloc[-1]["tonnes"]
        if first and last and last > first * 1.4:
            insights.append(
                _insight(
                    id="sa_demand",
                    title=f"Italy→Saudi pasta more than doubled into {last4.iloc[-1]['period']}",
                    magnitude=float(last / first) if first else None,
                    urgency=0.7,
                    relevance=0.85,
                    confidence=0.88,
                    why=f"Comext shows Italy's HS 1902 to Saudi Arabia rising from {first:.0f} t to {last:.0f} t over the last four reported months. That is restocking into a disrupted Gulf, not a one-off.",
                    action="Protect the 2026 Q4 / 2027 Q1 Garofalo allocation for KSA. Do not let spot UAE cargoes cannibalise it.",
                    owner="KSA sales",
                    timing="this month",
                    sources=[{"title": "Eurostat Comext", "url": "https://ec.europa.eu/eurostat"}],
                    tags=["demand", "ksa"],
                )
            )

    # 5. Kenya share
    ke = market_brief("KE")
    if ke.get("origins"):
        leaders = ", ".join(f"{o['origin_name']} {100*(o['share'] or 0):.0f}%" for o in ke["origins"][:3])
        insights.append(
            _insight(
                id="kenya_share",
                title=f"Kenya pasta shelf is not Italian: {leaders}",
                magnitude=ke.get("italy_share") or 0,
                urgency=0.55,
                relevance=0.8,
                confidence=0.8,
                why="Kenya reports Egypt, then Turkey, then Iran ahead of Italy. Italian pasta is a premium sliver. A Turkish or Egyptian price cut takes volume GARLEB will not win on price.",
                action="Sell Italian as a specified brand (foodservice, diaspora, modern trade), not against Egyptian bulk. Watch any Kenya Gazette safeguard.",
                owner="East Africa",
                timing="this quarter",
                sources=[{"title": "UN Comtrade Kenya imports", "url": "https://comtradeplus.un.org"}],
                followups=["Who is shipping pasta into Kenya?", "What is the Egypt vs Italy unit value in Kenya?"],
                tags=["competitors", "kenya"],
            )
        )

    # 6. Somalia / Turkey unit value
    so = market_brief("SO")
    if so.get("turkey_share") and so["turkey_share"] > 0.6:
        insights.append(
            _insight(
                id="somalia_tr",
                title="Somalia is a Turkish pasta market",
                magnitude=so["turkey_share"],
                urgency=0.5,
                relevance=0.7,
                confidence=0.75,
                why="Mirror data puts Turkish dry pasta at the bulk of Somalia's 2025 imports, at roughly $600/t against ~$1,500/t Italian. That is a different product, not a lost tender.",
                action="Do not chase Mogadishu on price. Offer a small Garofalo/premium line through Dubai/Djibouti for hotels and diaspora, and keep the volume fight out of the P&L.",
                owner="East Africa",
                timing="this quarter",
                sources=[{"title": "UN Comtrade mirror", "url": "https://comtradeplus.un.org"}],
                tags=["competitors", "somalia"],
            )
        )

    # 7. Durum pass-through
    durum = ind.get("durum") or {}
    if durum.get("price_eur_t"):
        insights.append(
            _insight(
                id="durum",
                title=f"Foggia durum at €{durum['price_eur_t']:.0f}/t",
                magnitude=durum.get("delta"),
                urgency=0.45,
                relevance=0.85,
                confidence=0.85,
                why=f"EU agri-food last print {durum.get('as_of')}: {durum.get('market')} €{durum['price_eur_t']:.1f}/t. Puglia press is flagging farmer protests and a harvest that 'will not pay diesel'. Semolina cover for 60–90 days of GARLEB sales should be marked to this, not last quarter's contract.",
                action="Re-cost open offers. If mills will not hold, shorten the offer validity to 7 days and move the durum clause into the confirmation.",
                owner="procurement",
                timing="this week",
                sources=[{"title": "EU agri-food durum", "url": "https://agriculture.ec.europa.eu"}],
                tags=["cost"],
            )
        )

    # 8. Garofalo capacity
    news = ind.get("news") or []
    gnews = [n for n in news if "Garofalo" in str(n.get("title")) and ("80" in str(n.get("title")) or "linee" in str(n.get("title")).lower() or "20%" in str(n.get("title")))]
    if gnews:
        insights.append(
            _insight(
                id="garofalo_capex",
                title="Garofalo is adding two lines and +20% output in Gragnano",
                magnitude=0.2,
                urgency=0.6,
                relevance=0.95,
                confidence=0.8,
                why=gnews[0]["title"] + ". More Italian branded tonnes will need a home outside the US (see the AD margin). GARLEB is the Gulf/Levant/EA door.",
                action="Ask for a 2027 volume memorandum: which SKUs, which markets, which exclusivity. Do it before other Gulf houses do.",
                owner="principal",
                timing="this month",
                sources=[{"title": gnews[0]["title"], "url": gnews[0].get("url"), "as_of": gnews[0].get("date")}],
                tags=["group", "supply"],
            )
        )

    # 9. Shelf Lebanon vs Syria
    shelf = {s["market"]: s for s in ind.get("shelf") or []}
    if "LB" in shelf and "SY" in shelf:
        gap = shelf["SY"]["usd_per_kg"] - shelf["LB"]["usd_per_kg"]
        insights.append(
            _insight(
                id="lb_sy_shelf",
                title=f"Spaghetti is ${shelf['LB']['usd_per_kg']:.2f}/kg in Lebanon, ${shelf['SY']['usd_per_kg']:.2f}/kg in Syria",
                magnitude=gap,
                urgency=0.4,
                relevance=0.7,
                confidence=0.75,
                why="WFP retail prints (CC BY-IGO) let us see the shelf, not just the CIF. A Syria opening priced off Beirut will miss local willingness to pay — or overshoot it.",
                action="Use the WFP series as the ceiling for any Damascus/Aleppo offer. Confirm duty and FX settlement before the first truck.",
                owner="Levant",
                timing="this quarter",
                sources=[{"title": "WFP via HDX", "url": "https://data.humdata.org"}],
                tags=["price", "syria"],
            )
        )

    # 10. Turkish pressure
    tp = ind.get("turkish_pressure") or {}
    if tp.get("score", 0) >= 0.4:
        insights.append(
            _insight(
                id="tr_pressure",
                title="Turkish pasta pressure is elevated",
                magnitude=tp.get("score"),
                urgency=0.55,
                relevance=0.8,
                confidence=0.7,
                why=f"USD/TRY {tp.get('usdtry')} and TİM cereals-sector momentum into GARLEB markets sit on top of a 14.7× jump in Turkish durum imports. Cheap foreign wheat plus a weak lira is the Turkish mills' weapon.",
                action="Do not meet Turkish prices. Defend Italian specification and brand. Where TİM shows a retreat (UAE YTD), take the shelf back.",
                owner="all desks",
                timing="this month",
                sources=[{"title": "TİM monthly", "url": "https://tim.org.tr/tr/ihracat-rakamlari"}],
                tags=["competitors", "turkey"],
            )
        )

    # 11. Saudi exporters
    sa = share_nowcast("AE")
    # also read saudi_trade via landed? use market_brief UAE and policy
    from ..store import read_table

    st = read_table("saudi_trade")
    if not st.empty:
        exp = st[st["flow"] == "export"].copy()
        if not exp.empty:
            latest_p = exp["period"].astype(str).max()
            sl = exp[exp["period"].astype(str) == latest_p].sort_values("tonnes", ascending=False)
            top = sl.head(3)
            dests = ", ".join(f"{r.get('country')} {r.get('tonnes'):.0f} t" for _, r in top.iterrows())
            insights.append(
                _insight(
                    id="saudi_export",
                    title=f"Saudi chapter-19 exports in {latest_p}: {dests}",
                    magnitude=float(sl["tonnes"].sum()) if sl["tonnes"].notna().any() else None,
                    urgency=0.5,
                    relevance=0.75,
                    confidence=0.8,
                    why="GASTAT monthly data (not Comtrade's lag) shows Saudi plants pushing cereal preparations into Iraq, the UAE and Yemen. That is a new regional competitor for Italian dry pasta, sitting inside GARLEB's Gulf.",
                    action="Name the Saudi brands on UAE/KSA tenders. Do not assume 'regional' means Egyptian or Turkish only.",
                    owner="Gulf",
                    timing="this month",
                    sources=[{"title": "GASTAT / DataSaudi", "url": "https://datasaudi.sa"}],
                    tags=["competitors", "ksa"],
                )
            )

    # 12. Quality
    quality = ind.get("quality") or []
    if quality:
        q0 = quality[0]
        insights.append(
            _insight(
                id="quality",
                title=f"{q0['system']} : {(q0.get('subject') or '')[:90]}",
                magnitude=1,
                urgency=0.4,
                relevance=0.55,
                confidence=0.7,
                why="A food-safety hit on a competitor origin is a sales argument. A hit on an Italian or tomato-paste supplier is a recall drill.",
                action="If the origin is a GARLEB vendor, pull the lot list. If it is a competitor, brief the buyer with the RASFF/FDA link — do not overclaim.",
                owner="quality",
                timing="this week",
                sources=[{"title": q0.get("subject"), "url": q0.get("url"), "as_of": q0.get("date")}],
                tags=["quality"],
            )
        )

    # 13. Tenders
    tenders = (ind.get("policy") or {}).get("tenders") or []
    foodish = [t for t in tenders if t.get("food_related")]
    if foodish:
        t0 = foodish[0]
        insights.append(
            _insight(
                id="ppa_tender",
                title=f"Lebanon PPA: {t0.get('title', '')[:100]}",
                magnitude=1,
                urgency=0.35,
                relevance=0.5,
                confidence=0.6,
                why="Public kitchens and hospitals in Lebanon still buy flour, pasta and sauces on PPA notices. Missing the opening date is missing a cash tender.",
                action=f"Read {t0.get('url')} before the opening ({t0.get('opening')}).",
                owner="Lebanon",
                timing=str(t0.get("opening") or "upcoming"),
                sources=[{"title": t0.get("title"), "url": t0.get("url")}],
                tags=["tender", "lebanon"],
            )
        )

    # 14. Ramadan
    ram = ind.get("ramadan") or {}
    if ram.get("days_to_order_by") is not None and ram["days_to_order_by"] < 140:
        insights.append(
            _insight(
                id="ramadan",
                title=f"Ramadan {ram.get('hijri_year')} starts {ram.get('start')} — order-by {ram.get('order_by')}",
                magnitude=ram.get("days_to_order_by"),
                urgency=0.5 if ram["days_to_order_by"] > 40 else 0.85,
                relevance=0.9,
                confidence=0.8,
                why="Gulf and Levant pasta sell-in is a Ramadan calendar, not a Gregorian one. Current Hormuz/Red Sea transit plus warehouse time eats ~35 days.",
                action="Lock January/February loadings now. Do not wait for December cover.",
                owner="all desks",
                timing=f"{ram['days_to_order_by']} days",
                sources=[],
                tags=["calendar"],
            )
        )

    # 15. EUR hedge
    fx = ind.get("fx") or {}
    if fx.get("EURUSD"):
        insights.append(
            _insight(
                id="eurusd",
                title=f"EUR/USD {fx['EURUSD']:.4f}",
                magnitude=fx["EURUSD"],
                urgency=0.35,
                relevance=0.7,
                confidence=0.9,
                why="GARLEB pays Italy in euro and sells in USD, AED, SAR and KES. A one-cent move on the euro is ~€10/t on a €1,000 pasta CIF.",
                action="Keep the euro clause on any offer longer than 10 days. Match AED/SAR receipts to the ECB print, not the local board.",
                owner="treasury",
                timing="daily",
                sources=[{"title": "ECB", "url": "https://data.ecb.europa.eu"}],
                tags=["fx"],
            )
        )

    # score
    for ins in insights:
        mag = abs(float(ins.get("magnitude") or 0.5))
        mag_n = min(1.0, mag if mag <= 1 else mag / 100.0)
        ins["score"] = (
            float(ins.get("relevance", 0.5))
            * (0.4 + 0.6 * mag_n)
            * float(ins.get("urgency", 0.5))
            * float(ins.get("confidence", 0.7))
        )
    insights.sort(key=lambda x: x["score"], reverse=True)
    return insights
