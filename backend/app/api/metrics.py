"""GET /metrics — dashboard KPIs (computed on demand from current state)."""
from fastapi import APIRouter, Depends

from app.api.dependencies import corrections_for, get_profile_id, queue_for, termbase_for

router = APIRouter()


@router.get("/metrics")
def metrics(profile_id: str = Depends(get_profile_id)) -> dict:
    termbase = termbase_for(profile_id)
    return {
        "terms_total": len(termbase.search()),
        "terms_active": len(termbase.search(status="active")),
        "reviews_pending": len(queue_for(profile_id).list_pending()),
        "corrections_total": len(corrections_for(profile_id).all()),
    }
