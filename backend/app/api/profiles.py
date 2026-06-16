"""Profile admin endpoints — manage Domain Packs (multi-tenant).

GET    /profiles                       list profiles
GET    /profiles/{id}                  detail (langs + tone/avoid coverage counts)
POST   /profiles                       create/update a profile (id, name, source/target langs)
PUT    /profiles/{id}/tone/{lang}      set tone guide text for a language
PUT    /profiles/{id}/avoid/{lang}     set the need-to-avoid list for a language

Adding a team = creating a profile here (data/config), never editing core code (OCP).
"""
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.dependencies import get_profiles, translation_service_for
from app.domain.entities import AvoidEntry, Profile
from app.infrastructure.profile_paths import is_valid_profile_id
from app.infrastructure.repositories.profile_file import FileProfileRepository

router = APIRouter()


def _require_valid(profile_id: str) -> None:
    if not is_valid_profile_id(profile_id):
        raise HTTPException(status_code=400, detail="invalid profile id")


def _invalidate_services() -> None:
    """Drop cached translation services so edited tone/avoid/target_langs take effect.

    The service bakes tone/avoid/examples at construction (keyed per profile+lang), so a
    profile edit is invisible until its cache entry is rebuilt. Clear all — they rebuild
    lazily on the next request (cheap, file-backed)."""
    translation_service_for.cache_clear()


class ProfileIn(BaseModel):
    id: str
    name: str = ""
    source_lang: str = "zh"
    target_langs: list[str] = ["vi"]
    char_name_convention: str = ""


class ToneIn(BaseModel):
    text: str


class AvoidEntryIn(BaseModel):
    term: str
    category: str = ""
    severity: str = "warning"
    is_pattern: bool = False


class AvoidIn(BaseModel):
    entries: list[AvoidEntryIn] = []


class FormatIn(BaseModel):
    enabled: bool = True
    extra_tokens: list[str] = []


def _detail(repo: FileProfileRepository, prof: Profile) -> dict:
    data = asdict(prof)
    data["tone_langs"] = [l for l in prof.target_langs if repo.tone(prof.id, l)]
    data["avoid_counts"] = {l: len(repo.avoid(prof.id, l)) for l in prof.target_langs}
    return data


@router.get("/profiles")
def list_profiles(repo: FileProfileRepository = Depends(get_profiles)) -> list:
    return [asdict(p) for p in repo.list()]


@router.get("/profiles/{profile_id}")
def get_profile(profile_id: str, repo: FileProfileRepository = Depends(get_profiles)) -> dict:
    _require_valid(profile_id)
    prof = repo.get(profile_id)
    if not prof:
        raise HTTPException(status_code=404, detail="profile not found")
    return _detail(repo, prof)


@router.post("/profiles")
def upsert_profile(body: ProfileIn, repo: FileProfileRepository = Depends(get_profiles)) -> dict:
    _require_valid(body.id.strip())
    prof = Profile(**body.model_dump())
    existing = repo.get(body.id)
    if existing:  # preserve format config across name/target-lang edits (set it via /format)
        prof.format_enabled = existing.format_enabled
        prof.format_extra_tokens = existing.format_extra_tokens
    repo.upsert(prof)
    _invalidate_services()
    return {"ok": True, "id": body.id}


@router.put("/profiles/{profile_id}/format")
def set_format(profile_id: str, body: FormatIn,
               repo: FileProfileRepository = Depends(get_profiles)) -> dict:
    _require_valid(profile_id)
    prof = repo.get(profile_id)
    if not prof:
        raise HTTPException(status_code=404, detail="profile not found")
    prof.format_enabled = body.enabled
    prof.format_extra_tokens = [t for t in body.extra_tokens if t.strip()]
    repo.upsert(prof)
    _invalidate_services()
    return {"ok": True, "id": profile_id, "enabled": prof.format_enabled,
            "extra_count": len(prof.format_extra_tokens)}


@router.get("/profiles/{profile_id}/tone/{lang}")
def get_tone(profile_id: str, lang: str, repo: FileProfileRepository = Depends(get_profiles)) -> dict:
    _require_valid(profile_id)
    return {"text": repo.tone(profile_id, lang)}


@router.get("/profiles/{profile_id}/avoid/{lang}")
def get_avoid(profile_id: str, lang: str, repo: FileProfileRepository = Depends(get_profiles)) -> list:
    _require_valid(profile_id)
    return [asdict(e) for e in repo.avoid(profile_id, lang)]


@router.put("/profiles/{profile_id}/tone/{lang}")
def set_tone(profile_id: str, lang: str, body: ToneIn,
             repo: FileProfileRepository = Depends(get_profiles)) -> dict:
    _require_valid(profile_id)
    if not repo.exists(profile_id):
        raise HTTPException(status_code=404, detail="profile not found")
    repo.set_tone(profile_id, lang, body.text)
    _invalidate_services()
    return {"ok": True, "id": profile_id, "lang": lang}


@router.put("/profiles/{profile_id}/avoid/{lang}")
def set_avoid(profile_id: str, lang: str, body: AvoidIn,
              repo: FileProfileRepository = Depends(get_profiles)) -> dict:
    _require_valid(profile_id)
    if not repo.exists(profile_id):
        raise HTTPException(status_code=404, detail="profile not found")
    repo.set_avoid(profile_id, lang, [AvoidEntry(**e.model_dump()) for e in body.entries])
    _invalidate_services()
    return {"ok": True, "id": profile_id, "lang": lang, "count": len(body.entries)}
