"""Termbase manager endpoints.

GET    /terms[?q=&status=]           list/search
POST   /terms                         upsert a term
DELETE /terms/{source}                archive a term
GET    /terms/candidates              extractor/curator proposals (data/termbase.candidates.json)
POST   /terms/candidates/approve      approve one candidate into the termbase
"""
import json
from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import get_profile_id, termbase_for
from app.domain.entities import Term
from app.infrastructure.profile_paths import profile_paths

router = APIRouter()


class TermIn(BaseModel):
    source: str
    vi: str
    category: str = ""
    note: str = ""
    trust_score: float = 1.0
    targets: dict = {}


@router.get("/terms")
def list_terms(q: str = "", status: Optional[str] = None,
               profile_id: str = Depends(get_profile_id)) -> list:
    return [asdict(t) for t in termbase_for(profile_id).search(query=q, status=status)]


@router.post("/terms")
def upsert_term(term: TermIn, profile_id: str = Depends(get_profile_id)) -> dict:
    termbase_for(profile_id).upsert(Term(**term.model_dump()))
    return {"ok": True, "source": term.source}


@router.delete("/terms/{source}")
def archive_term(source: str, profile_id: str = Depends(get_profile_id)) -> dict:
    termbase_for(profile_id).archive(source)
    return {"ok": True, "archived": source}


@router.get("/terms/candidates")
def list_candidates(profile_id: str = Depends(get_profile_id)) -> list:
    path = profile_paths(profile_id).candidates  # per-profile (legacy seed for default)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


@router.post("/terms/candidates/approve")
def approve_candidate(term: TermIn, profile_id: str = Depends(get_profile_id)) -> dict:
    termbase_for(profile_id).upsert(Term(**term.model_dump()))
    return {"ok": True, "approved": term.source}
