"""API composition root — lazy singletons wired via FastAPI Depends.

Lazy (lru_cache) so /health works even if the LLM key is absent: the LLM provider
is only built on first /translate call. All routers share the SAME termbase/queue/
correction instances, so writes via the API are visible to the translation pipeline.
"""
from functools import lru_cache

from app.agents.qc_reviewer import QCReviewer
from app.agents.translator import Translator
from app.application.qc_service import QCService
from app.application.review_service import ReviewService
from app.application.translation_service import TranslationService
from app.composition import (
    DEFAULT_CORRECTIONS_PATH,
    DEFAULT_QUEUE_PATH,
    DEFAULT_TERMBASE_PATH,
)
from app.infrastructure.channels.file_queue import FileReviewQueue
from app.infrastructure.llm import get_llm_provider
from app.infrastructure.repositories.correction_file import FileCorrectionStore
from app.infrastructure.repositories.termbase_file import FileTermbaseRepository
from app.settings import settings


@lru_cache
def get_termbase() -> FileTermbaseRepository:
    return FileTermbaseRepository(DEFAULT_TERMBASE_PATH)


@lru_cache
def get_corrections() -> FileCorrectionStore:
    return FileCorrectionStore(DEFAULT_CORRECTIONS_PATH)


@lru_cache
def get_queue() -> FileReviewQueue:
    return FileReviewQueue(DEFAULT_QUEUE_PATH)


@lru_cache
def _llm():
    return get_llm_provider(settings.llm_backend)  # built lazily on first translate


@lru_cache
def get_translation_service() -> TranslationService:
    llm = _llm()
    return TranslationService(
        get_termbase(), Translator(llm), QCService(QCReviewer(llm)),
        corrections=get_corrections(), review_channel=get_queue(),
    )


@lru_cache
def get_review_service() -> ReviewService:
    return ReviewService(get_queue(), get_corrections())
