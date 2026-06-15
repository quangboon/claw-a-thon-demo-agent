"""POST /translate — run the ZH→VI translate+QC pipeline.

Wraps the service in try/except so an LLM provider/timeout error returns a clean 502
instead of leaking a stack trace to the client.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.dependencies import get_translation_service
from app.application.translation_service import TranslationService

logger = logging.getLogger(__name__)
router = APIRouter()


class TranslateRequest(BaseModel):
    source: str
    target_lang: str = "vi"


@router.post("/translate")
def translate(req: TranslateRequest, service: TranslationService = Depends(get_translation_service)) -> dict:
    if not req.source.strip():
        raise HTTPException(status_code=400, detail="source is empty")
    try:
        return service.run(req.source)
    except Exception as exc:  # provider/timeout/empty-response → clean error, not 500 trace
        logger.exception("translation failed")
        raise HTTPException(status_code=502, detail=f"translation failed: {exc}") from exc
