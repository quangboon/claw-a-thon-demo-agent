"""Lightweight login gate — username/password from env, stateless bearer token.

Goal: stop casual visitors from burning LLM tokens on the public endpoint. NOT a full
auth system (no per-user accounts, no rotation). The token is a deterministic digest of
the configured credentials; the client sends it as `Authorization: Bearer <token>` and
the auth middleware (main.py) validates it on the token-spending endpoints.

Auth is ENABLED only when `AUTH_PASSWORD` is set; empty → endpoints stay open (dev/v1).
"""
import hashlib
import hmac

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.settings import settings

router = APIRouter()


def auth_enabled() -> bool:
    return bool(settings.auth_password)


def expected_token() -> str:
    """Deterministic token derived from the configured credentials."""
    raw = f"{settings.auth_username}:{settings.auth_password}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def token_ok(token: str) -> bool:
    return hmac.compare_digest(token or "", expected_token())


class LoginIn(BaseModel):
    username: str
    password: str


@router.get("/auth/status")
def auth_status() -> dict:
    """Public: tells the UI whether a login screen is required."""
    return {"auth_required": auth_enabled()}


@router.post("/auth/login")
def login(body: LoginIn) -> dict:
    if not auth_enabled():
        return {"token": "", "auth_required": False}
    ok = hmac.compare_digest(body.username, settings.auth_username) and \
        hmac.compare_digest(body.password, settings.auth_password)
    if not ok:
        raise HTTPException(status_code=401, detail="Sai tài khoản hoặc mật khẩu")
    return {"token": expected_token(), "auth_required": True}
