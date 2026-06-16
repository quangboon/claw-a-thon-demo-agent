"""Translation service — orchestrates the full pipeline (per profile + target language).

match termbase → translate (inject glossary + tone + avoid + examples + corrections)
→ QC (incl. need-to-avoid + term-confidence) → self-correct (1 retry) → decision
(auto_approved | send_to_human). Footer is appended to the final output.

The service is built per (profile, target_lang) by the composition root, so the tone,
avoid list and examples for that pairing are injected once at construction.
"""
from __future__ import annotations  # lazy annotations: allow `Protocol | None` in signatures

import uuid
from dataclasses import asdict

from app.agents.translator import Translator, with_footer
from app.application.glossary import glossary_lines
from app.application.qc_service import QCService
from app.domain.entities import AvoidEntry, Example, QcVerdict
from app.domain.ports import CorrectionStore, ReviewChannel, TermbaseRepository


def _feedback_from(verdict: QcVerdict) -> str:
    return "\n".join(f"- [{i.axis}] {i.message}" for i in verdict.issues)


def _corrections_prompt(items: list[dict]) -> str:
    return "\n".join(f"- '{c.get('wrong')}' should be '{c.get('right')}'" for c in items)


def _avoid_prompt(entries: list[AvoidEntry]) -> str:
    return ", ".join(e.term for e in entries if e.term)


class TranslationService:
    def __init__(self, termbase: TermbaseRepository, translator: Translator, qc: QCService,
                 corrections: CorrectionStore | None = None,
                 review_channel: ReviewChannel | None = None, max_retries: int = 1,
                 tone: str = "", avoid: list[AvoidEntry] | None = None,
                 examples: list[Example] | None = None, target_lang: str = "vi",
                 format_config: dict | None = None):
        self._termbase = termbase
        self._translator = translator
        self._qc = qc
        self._corrections = corrections
        self._review_channel = review_channel
        self._max_retries = max_retries
        self._tone = tone
        self._avoid = avoid or []
        self._examples = examples or []
        self._target_lang = target_lang
        self._format_config = format_config or {}

    def run(self, source: str) -> dict:
        lang = self._target_lang
        matched = self._termbase.match_in(source)
        glossary = glossary_lines(matched, lang)
        corr_items = self._corrections.for_text(source) if self._corrections else []
        corr_prompt = _corrections_prompt(corr_items)
        avoid_prompt = _avoid_prompt(self._avoid)

        attempts = 0
        feedback = ""
        verdict: QcVerdict | None = None
        draft = ""
        while attempts <= self._max_retries:
            attempts += 1
            draft = self._translator.translate(
                source, glossary, corr_prompt, feedback,
                tone=self._tone, avoid=avoid_prompt, examples=self._examples, target_lang=lang,
            )
            verdict = self._qc.review(source, draft, matched, avoid_list=self._avoid,
                                      target_lang=lang, format_config=self._format_config)
            # Only retry on `fail` (fixable term/completeness/banned issues). `needs_review`
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
            "output": with_footer(draft, lang),  # final text carries the per-lang AI footer
            "decision": decision,
            "target_lang": lang,
            "attempts": attempts,
            "terms_required": [{"source": t.source, "vi": t.translation(lang)} for t in matched],
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
                "target_lang": lang,
                "qc": result["qc"],
            })
        return result
