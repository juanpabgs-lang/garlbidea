from __future__ import annotations

import time
from typing import Any

import httpx

from .config import settings

DEFAULT_HEADERS = {
    "User-Agent": settings.user_agent,
    "Accept": "*/*",
}


def client(timeout: float = 45.0) -> httpx.Client:
    return httpx.Client(
        timeout=httpx.Timeout(timeout),
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
    )


def get_json(c: httpx.Client, url: str, *, params: dict[str, Any] | None = None, retries: int = 3) -> Any:
    last: Exception | None = None
    for i in range(retries):
        try:
            r = c.get(url, params=params)
            r.raise_for_status()
            return r.json()
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.4 * (i + 1))
    raise last  # type: ignore[misc]


def get_text(c: httpx.Client, url: str, *, params: dict[str, Any] | None = None, retries: int = 3) -> str:
    last: Exception | None = None
    for i in range(retries):
        try:
            r = c.get(url, params=params)
            r.raise_for_status()
            return r.text
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.4 * (i + 1))
    raise last  # type: ignore[misc]


def get_bytes(c: httpx.Client, url: str, *, retries: int = 3) -> bytes:
    last: Exception | None = None
    for i in range(retries):
        try:
            r = c.get(url)
            r.raise_for_status()
            return r.content
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.4 * (i + 1))
    raise last  # type: ignore[misc]


def post_json(c: httpx.Client, url: str, payload: Any, retries: int = 3) -> Any:
    last: Exception | None = None
    for i in range(retries):
        try:
            r = c.post(url, json=payload, headers={"Content-Type": "application/json", "Accept": "application/json"})
            r.raise_for_status()
            return r.json()
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.2 * (i + 1))
    raise last  # type: ignore[misc]
