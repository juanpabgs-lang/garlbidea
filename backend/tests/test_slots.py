from garleb_desk.shipments import TradeIntSource, shipment_status
from garleb_desk.slots import SLOTS


def test_tradeint_refuses():
    try:
        TradeIntSource().load()
        raise AssertionError("should refuse")
    except PermissionError as exc:
        assert "GARLEB" in str(exc)


def test_no_synthetic_shipments():
    st = shipment_status()
    assert st["csv"]["rows"] == 0
    assert "synthetic" in st["note"].lower() or "never" in st["note"].lower()


def test_slots_cover_licensed_and_blocked():
    kinds = {s["kind"] for s in SLOTS}
    assert "licensed" in kinds
    assert "geo_blocked" in kinds
    assert "free_key" in kinds
