"""Termbase manager endpoints.

GET    /terms[?q=&status=]           list/search
POST   /terms                         upsert a term
DELETE /terms/{source}                archive a term
GET    /terms/candidates              extractor/curator proposals (data/termbase.candidates.json)
POST   /terms/candidates/approve      approve one candidate into the termbase
"""
import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import get_termbase
from app.domain.entities import Term
from app.infrastructure.repositories.termbase_file import FileTermbaseRepository

router = APIRouter()
_CANDIDATES_PATH = Path("backend/data/termbase.candidates.json")


class TermIn(BaseModel):
    source: str
    vi: str
    category: str = ""
    note: str = ""
    trust_score: float = 1.0


@router.get("/terms")
def list_terms(q: str = "", status: Optional[str] = None,
               repo: FileTermbaseRepository = Depends(get_termbase)) -> list:
    return [asdict(t) for t in repo.search(query=q, status=status)]


@router.post("/terms")
def upsert_term(term: TermIn, repo: FileTermbaseRepository = Depends(get_termbase)) -> dict:
    repo.upsert(Term(**term.model_dump()))
    return {"ok": True, "source": term.source}


@router.delete("/terms/{source}")
def archive_term(source: str, repo: FileTermbaseRepository = Depends(get_termbase)) -> dict:
    repo.archive(source)
    return {"ok": True, "archived": source}


@router.get("/terms/candidates")
def list_candidates() -> list:
    if not _CANDIDATES_PATH.exists():
        return []
    return json.loads(_CANDIDATES_PATH.read_text(encoding="utf-8"))


@router.post("/terms/candidates/approve")
def approve_candidate(term: TermIn, repo: FileTermbaseRepository = Depends(get_termbase)) -> dict:
    repo.upsert(Term(**term.model_dump()))
    return {"ok": True, "approved": term.source}
