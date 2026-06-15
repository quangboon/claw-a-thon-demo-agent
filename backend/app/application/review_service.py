"""Review service — human-in-the-loop actions on the review queue.

approve(id)                : mark approved.
reject(id, corrected_text) : mark rejected AND record the wrong→right correction (flywheel).
"""
from __future__ import annotations

from app.domain.ports import CorrectionStore


class ReviewService:
    def __init__(self, queue, corrections: CorrectionStore):
        self._queue = queue
        self._corrections = corrections

    def list_pending(self) -> list:
        return self._queue.list_pending()

    def approve(self, job_id: str) -> bool:
        return self._queue.set_status(job_id, "approved")

    def reject(self, job_id: str, corrected_text: str) -> bool:
        item = self._queue.get(job_id)
        if not item:
            return False
        self._queue.set_status(job_id, "rejected", corrected=corrected_text)
        # Feed the flywheel: the rejected draft was wrong, the human edit is right.
        self._corrections.save(
            source=item.get("source", ""),
            wrong=item.get("translation", ""),
            right=corrected_text,
            note="human-reject",
        )
        return True
