"""GET /metrics — dashboard KPIs (computed on demand from current state)."""
from fastapi import APIRouter, Depends

from app.api.dependencies import get_corrections, get_queue, get_termbase

router = APIRouter()


@router.get("/metrics")
def metrics(
    termbase=Depends(get_termbase),
    queue=Depends(get_queue),
    corrections=Depends(get_corrections),
) -> dict:
    return {
        "terms_total": len(termbase.search()),
        "terms_active": len(termbase.search(status="active")),
        "reviews_pending": len(queue.list_pending()),
        "corrections_total": len(corrections.all()),
    }
