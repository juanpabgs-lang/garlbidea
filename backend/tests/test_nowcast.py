from pathlib import Path

from garleb_desk.analytics.flows import market_brief
from garleb_desk.config import SNAPSHOT


def test_kenya_nowcast_is_egyptian_not_italian():
    if not (SNAPSHOT / "comtrade_flows.parquet").exists():
        return
    ke = market_brief("KE")
    origins = {o["origin"]: o["share"] for o in ke["origins"] if o.get("share") is not None}
    assert origins.get("EG", 0) > 0.4
    assert origins.get("IT", 0) < 0.1


def test_somalia_is_turkish():
    if not (SNAPSHOT / "comtrade_flows.parquet").exists():
        return
    so = market_brief("SO")
    origins = {o["origin"]: o["share"] for o in so["origins"] if o.get("share") is not None}
    if origins:
        assert origins.get("TR", 0) > 0.7
