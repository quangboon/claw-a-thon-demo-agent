"""API composition root — profile-scoped, lazy singletons wired via FastAPI Depends.

A request's profile comes from the `X-Profile-Id` header (default profile if absent),
so v1 clients keep working. Per-profile repos/services are cached by profile_id (and
target_lang for the translation service) so writes via the API are visible to the
pipeline and teams stay fully isolated. LLM is built lazily on first translate so
/health works without a key.
"""
from functools import lru_cache

from fastapi import Header, HTTPException

from app.agents.qc_reviewer import QCReviewer
from app.agents.translator import Translator
from app.application.qc_service import QCService
from app.application.review_service import ReviewService
from app.application.translation_service import TranslationService
from app.infrastructure.channels.file_queue import FileReviewQueue
from app.infrastructure.llm import get_llm_provider
from app.infrastructure.profile_paths import is_valid_profile_id, profile_paths
from app.infrastructure.repositories.correction_file import FileCorrectionStore
from app.infrastructure.repositories.profile_file import FileProfileRepository
from app.infrastructure.repositories.termbase_file import FileTermbaseRepository
from app.settings import settings


def get_profile_id(x_profile_id: str = Header(default="")) -> str:
    """Resolve the active profile from the X-Profile-Id header (fallback: default).

    Rejects unsafe ids (path traversal / separators) with 400 — the id becomes a
    directory name, so this is the tenant-isolation gate.
    """
    pid = x_profile_id.strip() or settings.default_profile_id
    if not is_valid_profile_id(pid):
        raise HTTPException(status_code=400, detail="invalid X-Profile-Id")
    return pid


@lru_cache
def get_profiles() -> FileProfileRepository:
    return FileProfileRepository(settings.profiles_dir, settings.default_profile_id)


@lru_cache
def termbase_for(profile_id: str) -> FileTermbaseRepository:
    return FileTermbaseRepository(str(profile_paths(profile_id).termbase))


@lru_cache
def corrections_for(profile_id: str) -> FileCorrectionStore:
    return FileCorrectionStore(str(profile_paths(profile_id).corrections))


@lru_cache
def queue_for(profile_id: str) -> FileReviewQueue:
    return FileReviewQueue(str(profile_paths(profile_id).queue))


@lru_cache
def _llm():
    return get_llm_provider(settings.llm_backend)  # built lazily on first translate


@lru_cache
def translation_service_for(profile_id: str, target_lang: str) -> TranslationService:
    llm = _llm()
    profiles = get_profiles()
    return TranslationService(
        termbase_for(profile_id), Translator(llm), QCService(QCReviewer(llm)),
        corrections=corrections_for(profile_id), review_channel=queue_for(profile_id),
        tone=profiles.tone(profile_id, target_lang),
        avoid=profiles.avoid(profile_id, target_lang),
        examples=profiles.examples(profile_id, target_lang),
        target_lang=target_lang,
    )


@lru_cache
def review_service_for(profile_id: str) -> ReviewService:
    return ReviewService(queue_for(profile_id), corrections_for(profile_id))
