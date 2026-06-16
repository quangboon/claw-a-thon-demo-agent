"""Composition root — wires adapters into services (single place for DI).

Profile-aware (multi-tenant): a service is built for a given (profile_id, target_lang).
Tenant data (termbase/corrections/queue) is namespaced per profile via profile_paths;
the default profile keeps the legacy v1 paths for backward compatibility. The profile's
tone/avoid/examples for the target language are injected into the TranslationService.

Both the CLI and the FastAPI layer build the pipeline here so wiring stays DRY.
"""
from __future__ import annotations  # PEP 604 `X | None` support on Python 3.9

from app.agents.qc_reviewer import QCReviewer
from app.agents.term_curator import TermCurator
from app.agents.translator import Translator
from app.application.qc_service import QCService
from app.application.review_service import ReviewService
from app.application.translation_service import TranslationService
from app.infrastructure.channels.file_queue import FileReviewQueue
from app.infrastructure.llm import get_llm_provider
from app.infrastructure.profile_paths import (
    LEGACY_CORRECTIONS,
    LEGACY_QUEUE,
    LEGACY_TERMBASE,
    profile_paths,
)
from app.infrastructure.repositories.correction_file import FileCorrectionStore
from app.infrastructure.repositories.profile_file import FileProfileRepository
from app.infrastructure.repositories.termbase_file import FileTermbaseRepository
from app.settings import settings

# Back-compat aliases (legacy default-profile paths). Kept for existing CLI callers.
DEFAULT_TERMBASE_PATH = LEGACY_TERMBASE
DEFAULT_CORRECTIONS_PATH = LEGACY_CORRECTIONS
DEFAULT_QUEUE_PATH = LEGACY_QUEUE


def build_profile_repository() -> FileProfileRepository:
    return FileProfileRepository(settings.profiles_dir, settings.default_profile_id)


def build_translation_service(
    profile_id: str | None = None,
    target_lang: str = "vi",
    llm_backend: str | None = None,
    termbase_path: str | None = None,
) -> TranslationService:
    profile_id = profile_id or settings.default_profile_id
    paths = profile_paths(profile_id)
    profiles = build_profile_repository()

    llm = get_llm_provider(llm_backend or settings.llm_backend)
    termbase = FileTermbaseRepository(termbase_path or str(paths.termbase))
    translator = Translator(llm)
    qc = QCService(QCReviewer(llm))
    corrections = FileCorrectionStore(str(paths.corrections))  # flywheel: feeds prompt
    review_channel = FileReviewQueue(str(paths.queue))         # send_to_human destination
    return TranslationService(
        termbase, translator, qc,
        corrections=corrections, review_channel=review_channel,
        tone=profiles.tone(profile_id, target_lang),
        avoid=profiles.avoid(profile_id, target_lang),
        examples=profiles.examples(profile_id, target_lang),
        target_lang=target_lang,
    )


def build_review_service(profile_id: str | None = None) -> ReviewService:
    paths = profile_paths(profile_id or settings.default_profile_id)
    return ReviewService(FileReviewQueue(str(paths.queue)), FileCorrectionStore(str(paths.corrections)))


def build_term_curator(llm_backend: str | None = None) -> TermCurator:
    return TermCurator(get_llm_provider(llm_backend or settings.llm_backend))
