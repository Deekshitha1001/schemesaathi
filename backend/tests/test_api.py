"""HTTP-level tests. Needs FastAPI + httpx (`pip install -r requirements.txt`); skipped otherwise.

NOTE: these were written but could NOT be run in the sandbox where the project was built
(no access to PyPI). Run `pytest` locally; if one fails, it is a real bug to fix.
"""
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from app import main  # noqa: E402


@pytest.fixture()
def client():
    main.limiter.max_calls = 0  # disable rate limiting except in the dedicated test
    return TestClient(main.app)


def test_health(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok" and body["schemes"] == 12


def test_meta_has_every_field(client):
    meta = client.get("/api/meta").json()
    assert "age" in meta["fields"] and meta["languages"] == ["en", "hi", "kn"]


def test_analyze(client):
    r = client.post("/api/analyze", json={"text": "I am 30 and have a bank account"})
    assert r.status_code == 200
    assert {x["id"]: x["status"] for x in r.json()["results"]}["pmsby"] == "eligible"


def test_analyze_overrides_and_null_clears(client):
    r = client.post("/api/analyze", json={"text": "I am 45", "overrides": {"age": None, "gender": "female"}})
    assert r.json()["profile"] == {"gender": "female"}


def test_analyze_validation(client):
    assert client.post("/api/analyze", json={"text": "x" * 6000}).status_code == 422
    assert client.post("/api/analyze", json={"text": 5}).status_code == 422


def test_ask(client):
    r = client.post("/api/ask", json={"question": "How much does PM-KISAN give?"})
    assert r.status_code == 200 and r.json()["grounded"]
    assert client.post("/api/ask", json={"question": ""}).status_code == 422


def test_transcribe_reports_501_when_not_installed(client):
    if main.transcriber is not None:
        pytest.skip("faster-whisper is installed")
    r = client.post("/api/transcribe", files={"audio": ("a.webm", b"123", "audio/webm")}, data={"lang": "hi"})
    assert r.status_code == 501


def test_rate_limit_returns_429(client):
    main.limiter.max_calls = 2
    main.limiter._calls.clear()
    codes = [client.post("/api/analyze", json={"text": "I am 30"}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_cors_allows_the_dev_frontend(client):
    r = client.options("/api/analyze", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
