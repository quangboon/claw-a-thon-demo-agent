"""Composition root — wires adapters into services (single place for DI).

Both the CLI (cli/translate.py) and the FastAPI layer (api/dependencies.py, Phase 05)
build the pipeline here so wiring stays DRY.
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
from app.infrastructure.repositories.correction_file import FileCorrectionStore
from app.infrastructure.repositories.termbase_file import FileTermbaseRepository
from app.settings import settings

DEFAULT_TERMBASE_PATH = "backend/termbase.json"
DEFAULT_CORRECTIONS_PATH = "backend/corrections.jsonl"
DEFAULT_QUEUE_PATH = "backend/review_queue.jsonl"


def build_translation_service(
    llm_backend: str | None = None,
    termbase_path: str = DEFAULT_TERMBASE_PATH,
) -> TranslationService:
    llm = get_llm_provider(llm_backend or settings.llm_backend)
    termbase = FileTermbaseRepository(termbase_path)
    translator = Translator(llm)
    qc = QCService(QCReviewer(llm))
    corrections = FileCorrectionStore(DEFAULT_CORRECTIONS_PATH)  # flywheel: feeds prompt
    review_channel = FileReviewQueue(DEFAULT_QUEUE_PATH)         # send_to_human destination
    return TranslationService(termbase, translator, qc,
                              corrections=corrections, review_channel=review_channel)


def build_review_service() -> ReviewService:
    return ReviewService(FileReviewQueue(DEFAULT_QUEUE_PATH), FileCorrectionStore(DEFAULT_CORRECTIONS_PATH))


def build_term_curator(llm_backend: str | None = None) -> TermCurator:
    return TermCurator(get_llm_provider(llm_backend or settings.llm_backend))
