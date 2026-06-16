"""QC axis #4 — need-to-avoid: the draft must not contain a profile's banned terms.

Banned terms/patterns come per (profile, lang) via context["avoid"] (list of AvoidEntry).
Severity drives the verdict:
  - "error"   → blocking issue (e.g. political/monarchy/compliance) → no auto-approve
  - "warning" → non-blocking flag (e.g. off-tone wording) → needs_review

This is the compliance "phải đối/không được dùng" check.
"""
from __future__ import annotations  # PEP 604 `X | None` hints on Python 3.9

import re

from app.domain.entities import QcIssue
from app.infrastructure.qc.registry import register_qc_rule


@register_qc_rule("need-to-avoid")
class AvoidPolicyRule:
    def check(self, source: str, draft: str, matched_terms: list, context: dict | None = None) -> list[QcIssue]:
        text = draft or ""
        avoid = (context or {}).get("avoid") or []
        issues: list[QcIssue] = []
        for entry in avoid:
            if not entry.term:
                continue
            if entry.is_pattern:
                hit = re.search(entry.term, text, flags=re.IGNORECASE) is not None
            else:
                # Substring match (works for CJK/Thai which lack word spaces).
                hit = entry.term.lower() in text.lower()
            if hit:
                label = f" ({entry.category})" if entry.category else ""
                issues.append(QcIssue(
                    "need-to-avoid",
                    f"Dùng từ cấm{label}: '{entry.term}'",
                    severity="error" if entry.severity == "error" else "warning",
                ))
        return issues
