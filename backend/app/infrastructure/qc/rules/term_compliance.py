"""QC axis #2 — term compliance: every required term's VI must appear in the draft."""
import re

from app.domain.entities import QcIssue
from app.infrastructure.qc.registry import register_qc_rule


@register_qc_rule("term-compliance")
class TermComplianceRule:
    def check(self, source: str, draft: str, matched_terms: list) -> list[QcIssue]:
        text = draft or ""
        issues: list[QcIssue] = []
        for term in matched_terms:
            # Word-boundary match avoids a short VI matching inside an unrelated word
            # (e.g. "Đan" inside "Đando"). \b is Unicode-aware in Python 3 re.
            pattern = r"\b" + re.escape(term.vi) + r"\b"
            if not re.search(pattern, text, flags=re.IGNORECASE):
                issues.append(
                    QcIssue("term-compliance", f"Thiếu thuật ngữ bắt buộc: {term.source} → {term.vi}")
                )
        return issues
