"""File-backed review queue. Implements the ReviewChannel port (enqueue).

Also exposes queue-management ops (list_pending / get / set_status) used by the
ReviewService and the API. Persists to review_queue.jsonl (one record per line).
"""
from __future__ import annotations  # PEP 604 `X | None` support on Python 3.9

import json
from pathlib import Path

from app.infrastructure.channels.registry import register_channel


class FileReviewQueue:
    def __init__(self, path: str):
        self._path = Path(path)

    def _all(self) -> list:
        if not self._path.exists():
            return []
        return [json.loads(line) for line in self._path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def _write_all(self, records: list) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + ("\n" if records else ""),
            encoding="utf-8",
        )

    # --- ReviewChannel port ---
    def enqueue(self, job_id: str, payload: dict) -> None:
        records = self._all()
        records.append({"id": job_id, "status": "pending", **payload})
        self._write_all(records)

    # --- queue management (used by ReviewService / API) ---
    def list_pending(self) -> list:
        return [r for r in self._all() if r.get("status") == "pending"]

    def get(self, job_id: str) -> dict | None:
        return next((r for r in self._all() if r.get("id") == job_id), None)

    def set_status(self, job_id: str, status: str, corrected: str | None = None) -> bool:
        records = self._all()
        found = False
        for r in records:
            if r.get("id") == job_id:
                r["status"] = status
                if corrected is not None:
                    r["corrected"] = corrected
                found = True
        if found:
            self._write_all(records)
        return found


@register_channel("file")
def _build(settings=None):
    path = getattr(settings, "review_queue_path", "backend/review_queue.jsonl") if settings else "backend/review_queue.jsonl"
    return FileReviewQueue(path)
