from __future__ import annotations

from datetime import date

from ..analytics.indicators import all_indicators
from ..playbook.rules import run_playbook


def compose(profile: dict | None = None) -> dict:
    profile = profile or {}
    insights = run_playbook(profile)
    ind = all_indicators()
    top = insights[:3]
    headline = " · ".join(i["title"] for i in top) if top else "Desk is quiet — refresh sources."
    return {
        "as_of": date.today().isoformat(),
        "profile": profile.get("id") or "garleb",
        "headline": headline,
        "summary": _summary(top, profile),
        "insights": insights[:12],
        "ticker": ind.get("ticker") or [],
        "ramadan": ind.get("ramadan") or {},
        "calendar": _calendar(insights, ind),
    }


def _summary(top: list[dict], profile: dict) -> str:
    name = profile.get("name") or "GARLEB"
    if not top:
        return f"{name} desk has no scored insights. Check Sources."
    bits = [i["title"] for i in top]
    return (
        f"Morning for {name}. {bits[0]}. "
        + (f"Also: {bits[1]}." if len(bits) > 1 else "")
        + (f" And {bits[2]}." if len(bits) > 2 else "")
    )


def _calendar(insights: list[dict], ind: dict) -> list[dict]:
    out = []
    ram = ind.get("ramadan") or {}
    if ram.get("order_by"):
        out.append({"date": ram["order_by"], "label": f"Ramadan {ram.get('hijri_year')} order-by"})
    if ram.get("start"):
        out.append({"date": ram["start"], "label": f"Ramadan {ram.get('hijri_year')} starts"})
    ad = next((i for i in insights if i["id"] == "ad_garofalo"), None)
    if ad and ad.get("timing") and "20" in str(ad["timing"]):
        out.append({"date": str(ad["timing"]).split()[-1], "label": "US AD hearing-request window (est.)"})
    out.append({"date": "2027-02-15", "label": "US pasta AD final results (typical 120–150 days after prelim)"})
    return out


def whatsapp(profile: dict | None = None) -> str:
    brief = compose(profile)
    lines = [f"*GARLEB Desk — {brief['as_of']}*", brief["summary"], ""]
    for i, ins in enumerate(brief["insights"][:6], 1):
        lines.append(f"*{i}. {ins['title']}*")
        lines.append(ins["why"][:280])
        lines.append(f"→ {ins['action'][:200]}")
        lines.append("")
    lines.append("_Sources on the desk. No GARLEB files in this build._")
    return "\n".join(lines)
