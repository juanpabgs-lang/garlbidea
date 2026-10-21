from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from .analytics.entities import screen
from .analytics.flows import all_markets, competitor_unit_values, italy_series, market_brief
from .analytics.indicators import all_indicators, landed_cost
from .ask.engine import ask
from .brief import compose, whatsapp
from .config import settings
from .profiles import list_profiles, load_profile
from .shipments import shipment_status
from .slots import slot_payload
from .store import load_manifest, read_table

app = FastAPI(title="GARLEB Desk", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _profile(name: str | None) -> dict:
    return load_profile(name or settings.profile)


@app.get("/api/health")
def health():
    man = load_manifest()
    live = sum(1 for s in man.get("sources", {}).values() if s.get("status") == "live")
    return {"ok": True, "live_sources": live, "built_at": man.get("built_at")}


@app.get("/api/brief")
def brief(profile: str | None = None):
    return compose(_profile(profile))


@app.get("/api/whatsapp", response_class=PlainTextResponse)
def brief_whatsapp(profile: str | None = None):
    return whatsapp(_profile(profile))


@app.post("/api/ask")
def ask_desk(payload: dict):
    q = payload.get("question") or payload.get("q") or ""
    return ask(q, _profile(payload.get("profile")))


@app.get("/api/markets")
def markets():
    return all_markets()


@app.get("/api/markets/{code}")
def market(code: str):
    code = code.upper()
    return {
        "brief": market_brief(code),
        "italy": italy_series(code).to_dict("records"),
        "units": competitor_unit_values(code).to_dict("records"),
        "landed": landed_cost(code),
    }


@app.get("/api/prices")
def prices():
    ind = all_indicators()
    return {
        "durum": ind["durum"],
        "fx": ind["fx"],
        "shelf": ind["shelf"],
        "wheat": read_table("wheat_prices").tail(24).to_dict("records"),
    }


@app.get("/api/freight")
def freight():
    ind = all_indicators()
    return {
        "lanes": ind["lanes"],
        "chokepoints": ind["chokepoints"],
        "ports": ind["ports"],
        "freight": ind["freight"],
    }


@app.get("/api/policy")
def policy():
    return all_indicators()["policy"]


@app.get("/api/quality")
def quality():
    return all_indicators()["quality"]


@app.get("/api/news")
def news():
    return all_indicators()["news"]


@app.get("/api/ticker")
def ticker():
    return all_indicators()["ticker"]


@app.get("/api/calendar")
def calendar(profile: str | None = None):
    return compose(_profile(profile))["calendar"]


@app.get("/api/sources")
def sources():
    man = load_manifest()
    return {"manifest": man, "slots": slot_payload(), "shipments": shipment_status()}


@app.get("/api/screen")
def screen_name(q: str = Query(..., min_length=3)):
    return screen(q)


@app.get("/api/profiles")
def profiles():
    return list_profiles()


@app.get("/api/indicators")
def indicators():
    return all_indicators()


def serve() -> None:
    import uvicorn

    uvicorn.run("garleb_desk.main:app", host=settings.api_host, port=settings.api_port, reload=False)
