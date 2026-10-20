from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from .config import HISTORY, SNAPSHOT

SNAPSHOT.mkdir(parents=True, exist_ok=True)
HISTORY.mkdir(parents=True, exist_ok=True)

MANIFEST_PATH = SNAPSHOT / "manifest.json"


def parquet_path(table: str) -> Path:
    return SNAPSHOT / f"{table}.parquet"


def write_table(table: str, df: pd.DataFrame) -> Path:
    path = parquet_path(table)
    if df is None or df.empty:
        # keep schema if we already have one
        if not path.exists():
            empty = df if df is not None else pd.DataFrame()
            empty.to_parquet(path, index=False)
        return path
    out = df.copy()
    out.to_parquet(path, index=False)
    return path


def read_table(table: str) -> pd.DataFrame:
    path = parquet_path(table)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def append_history(table: str, df: pd.DataFrame) -> None:
    if df is None or df.empty:
        return
    path = HISTORY / f"{table}.parquet"
    if path.exists():
        old = pd.read_parquet(path)
        merged = pd.concat([old, df], ignore_index=True)
    else:
        merged = df
    merged.to_parquet(path, index=False)


def load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        return {"sources": {}, "built_at": None}
    return json.loads(MANIFEST_PATH.read_text())


def update_manifest(entry: dict[str, Any]) -> dict[str, Any]:
    man = load_manifest()
    man.setdefault("sources", {})
    man["sources"][entry["name"]] = entry
    man["built_at"] = datetime.now(timezone.utc).isoformat()
    MANIFEST_PATH.write_text(json.dumps(man, indent=2, default=str))
    return man


def duck() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(":memory:")
    for p in SNAPSHOT.glob("*.parquet"):
        name = p.stem
        con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_parquet('{p.as_posix()}')")
    return con


def table_exists(table: str) -> bool:
    return parquet_path(table).exists() and parquet_path(table).stat().st_size > 0
