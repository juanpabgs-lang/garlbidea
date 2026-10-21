"""Small Comtrade pull for the markets the desk cannot miss."""

from __future__ import annotations

import time

from ..http import client, get_json
from .base import run_connector
from .comtrade import _norm


def fetch(c) -> None:
    raise NotImplementedError


def refresh():
    frames = []

    def grab(**params):
        from ..http import get_json as gj

        tag = params.pop("_tag", "comtrade")
        try:
            data = gj(c, "https://comtradeapi.un.org/public/v1/preview/C/A/HS", params=params, retries=2)
            time.sleep(2.0)
            frames.append(_norm(data.get("data") or [], "A", tag))
        except Exception as exc:  # noqa: BLE001
            print("comtrade skip", params, exc, flush=True)

    with client(timeout=40) as c:
        grab(reporterCode=404, period=2025, cmdCode=1902, flowCode="M", _tag="comtrade_import")
        grab(reporterCode=792, period=2025, cmdCode=1902, flowCode="X", _tag="comtrade_export")
        grab(reporterCode=792, period=2024, cmdCode=1902, flowCode="X", _tag="comtrade_export")
        grab(reporterCode=818, period=2025, cmdCode=1902, flowCode="X", _tag="comtrade_export")
        grab(reporterCode=380, period=2025, cmdCode=1902, flowCode="X", _tag="comtrade_export")
        grab(reporterCode=422, period=2024, cmdCode=1902, flowCode="M", _tag="comtrade_import")
        grab(reporterCode=682, period=2024, cmdCode=1902, flowCode="M", _tag="comtrade_import")
        grab(period=2025, partnerCode=706, cmdCode=190219, flowCode="X", _tag="comtrade_mirror")
        grab(period=2025, partnerCode=784, cmdCode=190219, flowCode="X", _tag="comtrade_mirror")
        grab(period=2025, partnerCode=262, cmdCode=190219, flowCode="X", _tag="comtrade_mirror")
        grab(reporterCode=834, period=2025, cmdCode=1902, flowCode="M", _tag="comtrade_import")
        grab(reporterCode=800, period=2025, cmdCode=1902, flowCode="M", _tag="comtrade_import")
        grab(reporterCode=646, period=2025, cmdCode=1902, flowCode="M", _tag="comtrade_import")
        grab(reporterCode=512, period=2025, cmdCode=1902, flowCode="M", _tag="comtrade_import")
        grab(reporterCode=414, period=2025, cmdCode=1902, flowCode="M", _tag="comtrade_import")

        import pandas as pd

        nonempty = [f for f in frames if f is not None and not f.empty]
        df = pd.concat(nonempty, ignore_index=True) if nonempty else pd.DataFrame()
    return run_connector(
        "un_comtrade",
        "comtrade_flows",
        "https://comtradeapi.un.org/public/v1/preview",
        "UN Comtrade public preview, attribution required",
        lambda: df,
        notes="Focused annual pull for GARLEB markets after public-preview quota.",
        as_of_col="period",
    )
