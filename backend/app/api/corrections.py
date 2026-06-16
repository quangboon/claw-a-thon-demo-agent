"""GET /corrections — list recorded wrong→right corrections (flywheel view)."""
from fastapi import APIRouter, Depends

from app.api.dependencies import corrections_for, get_profile_id

router = APIRouter()


@router.get("/corrections")
def list_corrections(profile_id: str = Depends(get_profile_id)) -> list:
    return corrections_for(profile_id).all()
