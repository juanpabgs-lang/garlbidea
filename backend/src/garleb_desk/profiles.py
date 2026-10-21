from __future__ import annotations

from pathlib import Path

import yaml

from .config import PROFILES


def list_profiles() -> list[dict]:
    out = []
    for p in sorted(PROFILES.glob("*.yaml")):
        out.append(load_profile(p.stem))
    return out


def load_profile(name: str = "garleb") -> dict:
    path = PROFILES / f"{name}.yaml"
    if not path.exists():
        path = PROFILES / "garleb.yaml"
    return yaml.safe_load(path.read_text()) or {}
