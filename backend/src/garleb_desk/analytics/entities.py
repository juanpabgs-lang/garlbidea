from __future__ import annotations

import pandas as pd
from rapidfuzz import fuzz, process

from ..store import read_table


def _names() -> pd.DataFrame:
    frames = []
    for table, col in (
        ("sanctions_ofac", "name"),
        ("sanctions_un", "name"),
        ("sanctions_uk", "name"),
    ):
        df = read_table(table)
        if df.empty or col not in df.columns:
            continue
        sl = df[[col]].rename(columns={col: "name"})
        sl["list"] = table
        frames.append(sl)
    if not frames:
        return pd.DataFrame(columns=["name", "list"])
    return pd.concat(frames, ignore_index=True)


def screen(query: str, limit: int = 8, cutoff: int = 82) -> list[dict]:
    q = (query or "").strip()
    if len(q) < 3:
        return []
    names = _names()
    if names.empty:
        return []
    choices = names["name"].astype(str).tolist()
    hits = process.extract(q, choices, scorer=fuzz.WRatio, limit=limit)
    out = []
    for name, score, idx in hits:
        if score < cutoff:
            continue
        row = names.iloc[idx]
        out.append({"name": name, "score": int(score), "list": row["list"], "query": q})
    return out
