"""FastAPI entrypoint — serves the API and (when built) the static React UI.

Hard requirements for AgentBase runtime: listen on port 8080, expose GET /health → 200.
"""
import os

from fastapi import FastAPI

from app.api import corrections, health, metrics, profiles, review, terms, translate

app = FastAPI(title="Multi-Tenant ZH→VI/TH/EN Translate + QC Agent")

# Order matters: API routers register first; static catch-all (if present) is last.
for module in (health, translate, terms, review, corrections, metrics, profiles):
    app.include_router(module.router)

# Serve the built React UI (Phase 09) if present — single-container deploy.
# Mount hashed assets at /assets and serve index.html for all other GETs so
# client-side routes (e.g. /termbase) survive a hard refresh (SPA fallback).
_static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(_static_dir):
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    _assets = os.path.join(_static_dir, "assets")
    if os.path.isdir(_assets):
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    _index = os.path.join(_static_dir, "index.html")

    @app.get("/{full_path:path}")
    def spa(full_path: str):  # noqa: ARG001 — catch-all SPA fallback (registered after API routers)
        return FileResponse(_index)
