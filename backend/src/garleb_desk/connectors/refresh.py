from __future__ import annotations

import traceback

from ..http import client
from ..slots import register_slots
from . import ccfi, comext, comtrade, datasaudi, fda, fedreg, gazette, news, portwatch, ppa, prices, rasff, sanctions, tim, wfp
from .base import SourceResult


def refresh_all(skip_heavy: bool = False) -> list[SourceResult]:
    results: list[SourceResult] = []
    with client(timeout=60.0) as c:
        steps = [
            ("comext", lambda: [comext.refresh(c)]),
            ("comtrade", lambda: [comtrade.refresh(c)]),
            ("prices", lambda: prices.refresh_all(c)),
            ("portwatch", lambda: portwatch.refresh_all(c)),
            ("ccfi", lambda: [ccfi.refresh(c)]),
            ("fedreg", lambda: [fedreg.refresh(c)]),
            ("wfp", lambda: [wfp.refresh(c)]),
            ("datasaudi", lambda: [datasaudi.refresh(c)]),
            ("tim", lambda: [tim.refresh(c)]),
            ("rasff", lambda: [rasff.refresh(c)]),
            ("fda", lambda: [fda.refresh(c)]),
            ("gazette", lambda: [gazette.refresh(c)]),
            ("ppa", lambda: [ppa.refresh(c)]),
            ("news", lambda: [news.refresh(c)]),
        ]
        if not skip_heavy:
            steps.append(("sanctions", lambda: sanctions.refresh_all(c)))
        for name, fn in steps:
            print(f"→ {name}", flush=True)
            try:
                chunk = fn()
                results.extend(chunk)
                for r in chunk:
                    print(f"  {r.status:9} {r.rows:6}  {r.name}  {r.error or ''}", flush=True)
            except Exception as exc:  # noqa: BLE001
                results.append(
                    SourceResult(
                        name=name,
                        table=name,
                        status="error",
                        rows=0,
                        as_of=None,
                        source_url="",
                        license="",
                        notes="refresh step failed",
                        error=f"{exc}\n{traceback.format_exc()[-400:]}",
                    )
                )
                results[-1].persist()
    results.extend(register_slots())
    return results


def main() -> None:
    results = refresh_all()
    for r in results:
        print(f"{r.status:9} {r.rows:6}  {r.name:24}  as_of={r.as_of}  {r.error or r.notes[:80]}")


if __name__ == "__main__":
    main()
