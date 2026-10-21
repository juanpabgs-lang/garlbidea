from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

from .config import DATA


class ShipmentSource(ABC):
    name: str
    status: str

    @abstractmethod
    def load(self) -> pd.DataFrame: ...

    def describe(self) -> dict:
        return {"name": self.name, "status": self.status}


class CsvShipmentSource(ShipmentSource):
    name = "csv"
    status = "ready"

    def __init__(self, path: Path | None = None):
        self.path = path or DATA / "uploads" / "shipments.csv"

    def load(self) -> pd.DataFrame:
        if not self.path.exists():
            return pd.DataFrame()
        return pd.read_csv(self.path)


class TradeIntSource(ShipmentSource):
    name = "tradeint"
    status = "needs_license_and_garleb_approval"

    def load(self) -> pd.DataFrame:
        raise PermissionError(
            "TradeInt is a licensed bill-of-lading feed. GARLEB must approve the provider before any call is made."
        )


def shipment_status() -> dict:
    csv = CsvShipmentSource()
    return {
        "csv": {
            "status": "ready" if csv.path.exists() else "waiting_for_file",
            "path": str(csv.path),
            "rows": int(len(csv.load())) if csv.path.exists() else 0,
        },
        "tradeint": TradeIntSource().describe(),
        "note": "No synthetic shipment rows are generated. Brief never reads this table.",
    }
