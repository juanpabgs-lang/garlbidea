from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

import pandas as pd

from ..store import append_history, update_manifest, write_table


@dataclass
class SourceResult:
    name: str
    table: str
    status: str  # live | empty | error | slot | blocked | licensed
    rows: int
    as_of: str | None
    source_url: str
    license: str
    notes: str = ""
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def persist(self, df: pd.DataFrame | None = None) -> None:
        if df is not None and self.status == "live":
            write_table(self.table, df)
            append_history(self.table, df)
        update_manifest(self.__dict__)


def run_connector(
    name: str,
    table: str,
    source_url: str,
    license: str,
    fetch: Callable[[], pd.DataFrame],
    notes: str = "",
    as_of_col: str | None = None,
) -> SourceResult:
    try:
        df = fetch()
        if df is None or df.empty:
            res = SourceResult(name, table, "empty", 0, None, source_url, license, notes)
            res.persist(df if df is not None else pd.DataFrame())
            return res
        as_of = None
        if as_of_col and as_of_col in df.columns and len(df):
            as_of = str(pd.Series(df[as_of_col]).dropna().astype(str).max())
        res = SourceResult(name, table, "live", int(len(df)), as_of, source_url, license, notes)
        res.persist(df)
        return res
    except Exception as exc:  # noqa: BLE001
        res = SourceResult(
            name,
            table,
            "error",
            0,
            None,
            source_url,
            license,
            notes,
            error=f"{type(exc).__name__}: {exc}",
        )
        res.persist()
        return res


def slot(name: str, table: str, reason: str, source_url: str = "", license: str = "n/a") -> SourceResult:
    res = SourceResult(name, table, "slot", 0, None, source_url, license, notes=reason)
    res.persist()
    return res
