from garleb_desk.connectors.comext import parse_payload
from garleb_desk.connectors.fedreg import _parse_margins
from garleb_desk.connectors.tim import parse_workbook
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[1] / "data" / "fixtures"


def test_comext_decode():
    payload = {
        "id": ["freq", "reporter", "partner", "product", "flow", "indicators", "time"],
        "size": [1, 1, 1, 1, 1, 2, 1],
        "dimension": {
            "freq": {"category": {"index": {"M": 0}, "label": {}}},
            "reporter": {"category": {"index": {"IT": 0}, "label": {}}},
            "partner": {"category": {"index": {"AE": 0}, "label": {"AE": "UAE"}}},
            "product": {"category": {"index": {"1902": 0}, "label": {"1902": "pasta"}}},
            "flow": {"category": {"index": {"2": 0}, "label": {}}},
            "indicators": {"category": {"index": {"VALUE_IN_EUROS": 0, "QUANTITY_IN_100KG": 1}, "label": {}}},
            "time": {"category": {"index": {"2026-08": 0}, "label": {}}},
        },
        "value": {"0": 1416200, "1": 7872.14},
    }
    df = parse_payload(payload)
    assert len(df) == 1
    assert abs(df.iloc[0]["tonnes"] - 787.214) < 0.01
    assert df.iloc[0]["market"] == "AE"


def test_margin_parse():
    text = """
La Molisana, S.p.A..........................................        3.62
Pastificio Lucio Garofalo S.p.A.............................        6.47
Companies Not Selected for Individual Review ...............        5.05
"""
    rows = _parse_margins(text)
    firms = {r["firm"]: r["margin_pct"] for r in rows}
    assert firms["Garofalo"] == 6.47
    assert firms["La Molisana"] == 3.62


def test_tim_workbook():
    path = FIXTURES / "tim_sample.xlsx"
    if not path.exists():
        return
    df = parse_workbook(path.read_bytes())
    assert not df.empty
