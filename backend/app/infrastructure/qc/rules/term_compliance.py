"""QC axis #2 — term compliance: every required term's translation must appear in the draft.

Uses a case-insensitive substring check rather than a regex word boundary: `\b` is
unreliable across scripts (e.g. Thai terms ending in a combining mark have no word
boundary after them), and game terms are specific enough that substring is safe.
"""
from __future__ import annotations  # PEP 604 `X | None` hints on Python 3.9

from app.domain.entities import QcIssue
from app.infrastructure.qc.registry import register_qc_rule


@register_qc_rule("term-compliance")
class TermComplianceRule:
    def check(self, source: str, draft: str, matched_terms: list, context: dict | None = None) -> list[QcIssue]:
        text = (draft or "").lower()
        target_lang = (context or {}).get("target_lang", "vi")
        issues: list[QcIssue] = []
        for term in matched_terms:
            expected = term.translation(target_lang)
            if not expected:
                continue  # no known translation for this lang → nothing to assert
            if expected.lower() not in text:
                issues.append(
                    QcIssue("term-compliance", f"Thiếu thuật ngữ bắt buộc: {term.source} → {expected}")
                )
        return issues
