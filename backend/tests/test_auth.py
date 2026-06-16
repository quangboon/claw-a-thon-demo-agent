"""Access-gate tests — login + protected-endpoint enforcement."""
import hashlib

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.settings import settings


@pytest.fixture
def auth_client(isolated_profiles, monkeypatch):
    monkeypatch.setattr(settings, "llm_backend", "mock")
    monkeypatch.setattr(settings, "auth_username", "admin")
    monkeypatch.setattr(settings, "auth_password", "secret")
    return TestClient(app)


def _token():
    return hashlib.sha256(b"admin:secret").hexdigest()


def test_health_and_status_public(auth_client):
    assert auth_client.get("/health").status_code == 200
    assert auth_client.get("/auth/status").json() == {"auth_required": True}


def test_protected_endpoint_blocked_without_token(auth_client):
    assert auth_client.get("/profiles").status_code == 401
    assert auth_client.post("/translate", json={"source": "灵石"}).status_code == 401


def test_login_then_access(auth_client):
    bad = auth_client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert bad.status_code == 401
    ok = auth_client.post("/auth/login", json={"username": "admin", "password": "secret"})
    assert ok.status_code == 200
    token = ok.json()["token"]
    assert token == _token()
    headers = {"Authorization": f"Bearer {token}"}
    assert auth_client.get("/profiles", headers=headers).status_code == 200


def test_auth_disabled_when_no_password(isolated_profiles, monkeypatch):
    monkeypatch.setattr(settings, "llm_backend", "mock")
    monkeypatch.setattr(settings, "auth_password", "")  # empty → open
    c = TestClient(app)
    assert c.get("/auth/status").json() == {"auth_required": False}
    assert c.get("/profiles").status_code == 200  # no token needed
