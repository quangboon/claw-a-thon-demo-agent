"""QC axis #1 — completeness: draft must be non-empty, not an untranslated stub, not too short.

Note: we deliberately do NOT flag '[' or '...' — game strings legitimately contain
bracketed variable tokens (e.g. [player_name]) and ellipses in dialogue.
"""
from __future__ import annotations  # PEP 604 `X | None` hints on Python 3.9

from app.domain.entities import QcIssue
from app.infrastructure.qc.registry import register_qc_rule

# Genuine "unfinished translation" markers only (avoid false positives on real content).
_STUB_MARKERS = ("lorem ipsum", "todo", "tbd")


@register_qc_rule("completeness")
class CompletenessRule:
    # VI is usually longer than compact ZH; a much-shorter draft signals dropped content.
    MIN_RATIO = 0.5

    def check(self, source: str, draft: str, matched_terms: list, context: dict | None = None) -> list[QcIssue]:
        issues: list[QcIssue] = []
        text = (draft or "").strip()
        if not text:
            return [QcIssue("completeness", "Bản dịch rỗng")]
        low = text.lower()
        if any(m in low for m in _STUB_MARKERS):
            issues.append(QcIssue("completeness", "Bản dịch còn nội dung chưa hoàn chỉnh (placeholder)"))
        if len(text) < len(source) * self.MIN_RATIO:
            issues.append(QcIssue("completeness", "Bản dịch quá ngắn so với nguồn (có thể rớt nội dung)"))
        return issues
