"""Phase 05 — profile-scoped API + profile CRUD (FastAPI TestClient)."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.settings import settings


@pytest.fixture
def client(isolated_profiles, monkeypatch):
    monkeypatch.setattr(settings, "llm_backend", "mock")  # no network in tests
    return TestClient(app)


def test_terms_isolated_by_profile_header(client):
    client.post("/terms", json={"source": "灵石", "vi": "Linh Thạch"}, headers={"X-Profile-Id": "a"})
    a = client.get("/terms", headers={"X-Profile-Id": "a"}).json()
    b = client.get("/terms", headers={"X-Profile-Id": "b"}).json()
    assert [t["source"] for t in a] == ["灵石"]
    assert b == []  # B never sees A's term


def test_missing_header_falls_back_to_default(client):
    client.post("/terms", json={"source": "金币", "vi": "Vàng"})  # no header → default
    default_terms = client.get("/terms").json()
    assert [t["source"] for t in default_terms] == ["金币"]


def test_translate_respects_profile_and_lang(client):
    client.post("/terms", json={"source": "金币", "vi": "Vàng", "targets": {"th": "เหรียญทอง"}},
                headers={"X-Profile-Id": "g"})
    res = client.post("/translate", json={"source": "金币", "target_lang": "th"},
                      headers={"X-Profile-Id": "g"})
    assert res.status_code == 200
    body = res.json()
    assert body["target_lang"] == "th"
    assert body["output"].rstrip().endswith("แปลโดย AI")


def test_profiles_crud(client):
    # create
    assert client.post("/profiles", json={"id": "team-z", "name": "Team Z",
                                          "target_langs": ["vi", "th"]}).json()["ok"]
    listing = client.get("/profiles").json()
    ids = {p["id"] for p in listing}
    assert {"default", "team-z"} <= ids
    # set tone + avoid, then read detail
    client.put("/profiles/team-z/tone/vi", json={"text": "Tone Z"})
    client.put("/profiles/team-z/avoid/th",
               json={"entries": [{"term": "X", "severity": "error", "category": "monarchy"}]})
    detail = client.get("/profiles/team-z").json()
    assert "vi" in detail["tone_langs"]
    assert detail["avoid_counts"]["th"] == 1


def test_avoid_edit_takes_effect_immediately(client):
    # Mock draft always contains "giả". Ban it via /admin → next translate must block
    # (proves cached translation service is invalidated on profile edit).
    client.post("/profiles", json={"id": "edit-me", "name": "E", "target_langs": ["vi"]})
    h = {"X-Profile-Id": "edit-me"}
    assert client.post("/translate", json={"source": "测试"}, headers=h).json()["decision"] == "auto_approved"
    client.put("/profiles/edit-me/avoid/vi",
               json={"entries": [{"term": "giả", "severity": "error", "category": "compliance"}]})
    after = client.post("/translate", json={"source": "测试"}, headers=h).json()
    assert after["decision"] == "send_to_human"
    assert any(i["axis"] == "need-to-avoid" for i in after["qc"]["issues"])


def test_get_tone_and_avoid_for_editor(client):
    client.post("/profiles", json={"id": "ed", "name": "Ed", "target_langs": ["vi"]})
    client.put("/profiles/ed/tone/vi", json={"text": "Tone Ed"})
    client.put("/profiles/ed/avoid/vi",
               json={"entries": [{"term": "x", "severity": "error", "category": "c"}]})
    assert client.get("/profiles/ed/tone/vi").json()["text"] == "Tone Ed"
    av = client.get("/profiles/ed/avoid/vi").json()
    assert len(av) == 1 and av[0]["term"] == "x" and av[0]["severity"] == "error"
    # missing lang → graceful empty
    assert client.get("/profiles/ed/tone/en").json()["text"] == ""
    assert client.get("/profiles/ed/avoid/en").json() == []


def test_profile_404(client):
    assert client.get("/profiles/nope").status_code == 404
    assert client.put("/profiles/nope/tone/vi", json={"text": "x"}).status_code == 404


def test_path_traversal_rejected(client):
    # Malicious profile id (header + body) must never escape the namespace → 400.
    assert client.get("/terms", headers={"X-Profile-Id": "../../etc"}).status_code == 400
    assert client.post("/translate", json={"source": "x"},
                       headers={"X-Profile-Id": "a/../b"}).status_code == 400
    assert client.post("/profiles", json={"id": "../default", "name": "x"}).status_code == 400
