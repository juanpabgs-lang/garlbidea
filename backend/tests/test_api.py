from fastapi.testclient import TestClient

from garleb_desk.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_brief():
    r = client.get("/api/brief")
    assert r.status_code == 200
    body = r.json()
    assert "insights" in body
    assert "ticker" in body


def test_ask():
    r = client.post("/api/ask", json={"question": "Who is shipping pasta into Kenya?"})
    assert r.status_code == 200
    assert "text" in r.json()


def test_sources():
    r = client.get("/api/sources")
    assert r.status_code == 200
    assert "slots" in r.json()


def test_whatsapp():
    r = client.get("/api/whatsapp")
    assert r.status_code == 200
    assert "GARLEB Desk" in r.text
