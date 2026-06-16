"""Human-review queue endpoints.

GET  /review/pending
POST /review/{job_id}/approve
POST /review/{job_id}/reject   {corrected_text}  → records correction (flywheel)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.dependencies import get_profile_id, review_service_for

router = APIRouter()


class RejectRequest(BaseModel):
    corrected_text: str


@router.get("/review/pending")
def pending(profile_id: str = Depends(get_profile_id)) -> list:
    return review_service_for(profile_id).list_pending()


@router.post("/review/{job_id}/approve")
def approve(job_id: str, profile_id: str = Depends(get_profile_id)) -> dict:
    if not review_service_for(profile_id).approve(job_id):
        raise HTTPException(status_code=404, detail="job not found")
    return {"ok": True, "approved": job_id}


@router.post("/review/{job_id}/reject")
def reject(job_id: str, req: RejectRequest, profile_id: str = Depends(get_profile_id)) -> dict:
    if not review_service_for(profile_id).reject(job_id, req.corrected_text):
        raise HTTPException(status_code=404, detail="job not found")
    return {"ok": True, "rejected": job_id}
