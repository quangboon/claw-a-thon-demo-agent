"""Translation service — orchestrates the full pipeline.

match termbase → translate (inject glossary + corrections) → QC → self-correct (1 retry)
→ decision (auto_approved | send_to_human). Footer is appended to the final output.
"""
from __future__ import annotations  # lazy annotations: allow `Protocol | None` in signatures

import uuid
from dataclasses import asdict

from app.agents.translator import Translator, with_footer
from app.application.glossary import glossary_lines
from app.application.qc_service import QCService
from app.domain.entities import QcVerdict
from app.domain.ports import CorrectionStore, ReviewChannel, TermbaseRepository


def _feedback_from(verdict: QcVerdict) -> str:
    return "\n".join(f"- [{i.axis}] {i.message}" for i in verdict.issues)


def _corrections_prompt(items: list[dict]) -> str:
    # Minimal formatter; Phase 04 supplies the CorrectionStore that produces these.
    return "\n".join(f"- '{c.get('wrong')}' nên là '{c.get('right')}'" for c in items)


class TranslationService:
    def __init__(self, termbase: TermbaseRepository, translator: Translator, qc: QCService,
                 corrections: CorrectionStore | None = None,
                 review_channel: ReviewChannel | None = None, max_retries: int = 1):
        self._termbase = termbase
        self._translator = translator
        self._qc = qc
        self._corrections = corrections
        self._review_channel = review_channel
        self._max_retries = max_retries

    def run(self, source: str) -> dict:
        matched = self._termbase.match_in(source)
        glossary = glossary_lines(matched)
        corr_items = self._corrections.for_text(source) if self._corrections else []
        corr_prompt = _corrections_prompt(corr_items)

        attempts = 0
        feedback = ""
        verdict: QcVerdict | None = None
        draft = ""
        while attempts <= self._max_retries:
            attempts += 1
            draft = self._translator.translate(source, glossary, corr_prompt, feedback)
            verdict = self._qc.review(source, draft, matched)
            # Only retry on `fail` (fixable term/completeness issues). `needs_review`
            # is subjective fluency — a retry rarely helps, so short-circuit to human.
            if verdict.status != "fail":
                break
            feedback = _feedback_from(verdict)  # feed issues into the next attempt

        decision = "auto_approved" if verdict and verdict.status == "pass" else "send_to_human"
        job_id = uuid.uuid4().hex[:12]
        result = {
            "id": job_id,
            "source": source,
            "translation": draft,
            "output": with_footer(draft),  # final text carries the mandatory AI footer
            "decision": decision,
            "attempts": attempts,
            "terms_required": [{"source": t.source, "vi": t.vi} for t in matched],
            "qc": {
                "status": verdict.status if verdict else "unknown",
                "fluency_score": verdict.fluency_score if verdict else None,
                "issues": [asdict(i) for i in verdict.issues] if verdict else [],
            },
        }
        # Push drafts that QC couldn't auto-approve into the human-review queue.
        if decision == "send_to_human" and self._review_channel:
            self._review_channel.enqueue(job_id, {
                "source": source,
                "translation": draft,
                "qc": result["qc"],
            })
        return result
