"""FastAPI entrypoint — serves the API and (when built) the static React UI.

Hard requirements for AgentBase runtime: listen on port 8080, expose GET /health → 200.
"""
import os

from fastapi import FastAPI

from app.api import corrections, health, metrics, review, terms, translate

app = FastAPI(title="ZH→VI Translate + QC Agent")

# Order matters: API routers register first; static catch-all (if present) is last.
for module in (health, translate, terms, review, corrections, metrics):
    app.include_router(module.router)

# Serve the built React UI (Phase 09) if present — single-container deploy.
_static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(_static_dir):
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
