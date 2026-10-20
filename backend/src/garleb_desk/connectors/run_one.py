from __future__ import annotations

import sys

from ..http import client
from ..slots import register_slots
from . import ccfi, comext, comtrade, datasaudi, fda, fedreg, gazette, news, portwatch, ppa, prices, rasff, sanctions, tim, wfp


def main() -> None:
    want = set(sys.argv[1:] or [])
    with client(timeout=60.0) as c:
        mapping = {
            "comext": lambda: [comext.refresh(c)],
            "comtrade": lambda: [comtrade.refresh(c)],
            "prices": lambda: prices.refresh_all(c),
            "portwatch": lambda: portwatch.refresh_all(c),
            "ccfi": lambda: [ccfi.refresh(c)],
            "fedreg": lambda: [fedreg.refresh(c)],
            "wfp": lambda: [wfp.refresh(c)],
            "datasaudi": lambda: [datasaudi.refresh(c)],
            "tim": lambda: [tim.refresh(c)],
            "rasff": lambda: [rasff.refresh(c)],
            "fda": lambda: [fda.refresh(c)],
            "gazette": lambda: [gazette.refresh(c)],
            "ppa": lambda: [ppa.refresh(c)],
            "news": lambda: [news.refresh(c)],
            "sanctions": lambda: sanctions.refresh_all(c),
            "slots": register_slots,
        }
        for name in want:
            print("→", name, flush=True)
            for r in mapping[name]():
                print(f"  {r.status:9} {r.rows:6} {r.name} {r.error or r.as_of}", flush=True)


if __name__ == "__main__":
    main()
