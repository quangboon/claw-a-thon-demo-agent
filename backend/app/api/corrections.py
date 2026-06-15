"""GET /corrections — list recorded wrong→right corrections (flywheel view)."""
from fastapi import APIRouter, Depends

from app.api.dependencies import get_corrections
from app.infrastructure.repositories.correction_file import FileCorrectionStore

router = APIRouter()


@router.get("/corrections")
def list_corrections(store: FileCorrectionStore = Depends(get_corrections)) -> list:
    return store.all()
