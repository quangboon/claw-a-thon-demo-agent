"""QC axis #5 — term confidence: flag low-confidence output for human help.

If a target-language draft still contains Han (CJK) characters, the model likely
left a term untranslated / unmapped — exactly the "thuật ngữ chưa đúng expect → cần
hỗ trợ" signal. Emits a WARNING (→ needs_review), never auto-blocks. Skipped when the
target language itself is Chinese.
"""
from __future__ import annotations  # PEP 604 `X | None` hints on Python 3.9

import re

from app.domain.entities import QcIssue
from app.infrastructure.qc.registry import register_qc_rule

_HAN = re.compile(r"[一-鿿]")


@register_qc_rule("term-confidence")
class TermConfidenceRule:
    def check(self, source: str, draft: str, matched_terms: list, context: dict | None = None) -> list[QcIssue]:
        target_lang = (context or {}).get("target_lang", "vi")
        if target_lang == "zh":
            return []
        leftovers = sorted(set(_HAN.findall(draft or "")))
        if leftovers:
            sample = "".join(leftovers[:8])
            return [QcIssue(
                "term-confidence",
                f"Còn ký tự Hán chưa dịch/chưa có trong termbase ('{sample}') — cần hỗ trợ dịch",
                severity="warning",
            )]
        return []
