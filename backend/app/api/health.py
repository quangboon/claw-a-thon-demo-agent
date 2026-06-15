"""Health check — required by AgentBase runtime (GET /health → 200 marks ACTIVE).

Must NOT depend on the LLM so the runtime reaches ACTIVE before any translate call.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
