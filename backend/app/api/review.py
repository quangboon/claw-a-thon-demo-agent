"""Human-review queue endpoints.

GET  /review/pending
POST /review/{job_id}/approve
POST /review/{job_id}/reject   {corrected_text}  → records correction (flywheel)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.dependencies import get_review_service
from app.application.review_service import ReviewService

router = APIRouter()


class RejectRequest(BaseModel):
    corrected_text: str


@router.get("/review/pending")
def pending(service: ReviewService = Depends(get_review_service)) -> list:
    return service.list_pending()


@router.post("/review/{job_id}/approve")
def approve(job_id: str, service: ReviewService = Depends(get_review_service)) -> dict:
    if not service.approve(job_id):
        raise HTTPException(status_code=404, detail="job not found")
    return {"ok": True, "approved": job_id}


@router.post("/review/{job_id}/reject")
def reject(job_id: str, req: RejectRequest, service: ReviewService = Depends(get_review_service)) -> dict:
    if not service.reject(job_id, req.corrected_text):
        raise HTTPException(status_code=404, detail="job not found")
    return {"ok": True, "rejected": job_id}
