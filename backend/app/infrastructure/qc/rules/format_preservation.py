"""QC axis #6 — format preservation: placeholders / tags / line breaks must survive.

Game strings carry runtime tokens that MUST pass through translation untouched, else the
UI breaks or shows wrong data:
  - braces:   {0} {name} {0:F2}
  - tags:     <b> </b> <color=#fff>
  - brackets: [player_name] [HP]
  - printf:   %s %d %1$s %.2f %@

We compare the multiset of tokens in source vs draft. Missing/extra → ERROR (block);
line-break count mismatch → WARNING. The rule is a NO-OP when the source has no such
tokens, so plain prose / marketing copy is never falsely flagged (no per-profile config
needed). Note: bare numbers/percent (e.g. "+20%") are intentionally NOT enforced —
translators legitimately reformat them and exact-match would be too noisy.
"""
from __future__ import annotations

import re
from collections import Counter

from app.domain.entities import QcIssue
from app.infrastructure.qc.registry import register_qc_rule

_PATTERNS = [
    re.compile(r"\{[^{}]*\}"),                              # {0}, {name}, {0:F2}
    re.compile(r"<[^<>]+>"),                                # <b>, </b>, <color=#fff>
    re.compile(r"\[[^\[\]]+\]"),                            # [player_name], [HP]
    re.compile(r"%(?:\d+\$)?[-+ #0]*\d*(?:\.\d+)?[a-zA-Z@]"),  # %s %d %1$s %.2f %@
]


def _tokens(text: str) -> Counter:
    c: Counter = Counter()
    for pat in _PATTERNS:
        c.update(pat.findall(text or ""))
    return c


def _fmt(counter: Counter) -> str:
    return ", ".join(f"{k}×{v}" if v > 1 else k for k, v in counter.items())


@register_qc_rule("format-preservation")
class FormatPreservationRule:
    def check(self, source: str, draft: str, matched_terms: list, context: dict | None = None) -> list[QcIssue]:
        src, dst = _tokens(source), _tokens(draft)
        issues: list[QcIssue] = []
        missing = src - dst  # in source, missing or fewer in draft
        extra = dst - src    # added/duplicated in draft
        if missing:
            issues.append(QcIssue("format", f"Thiếu/sai placeholder hoặc tag: {_fmt(missing)}", severity="error"))
        if extra:
            issues.append(QcIssue("format", f"Placeholder/tag thừa hoặc lạ: {_fmt(extra)}", severity="error"))
        # Line-break parity (count real '\n' + literal '\\n'); softer signal → warning.
        s_lines = (source or "").count("\n") + (source or "").count("\\n")
        d_lines = (draft or "").count("\n") + (draft or "").count("\\n")
        if s_lines != d_lines:
            issues.append(QcIssue("format", f"Số dòng không khớp (nguồn {s_lines} ↔ dịch {d_lines})", severity="warning"))
        return issues
