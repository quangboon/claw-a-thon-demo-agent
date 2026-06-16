r"""QC axis #6 — format preservation: placeholders / tags / line breaks must survive.

Game strings carry runtime tokens that MUST pass through translation untouched, else the
UI breaks or shows wrong data. Two checks:

1. Verbatim tokens — compared as a multiset (source vs draft); missing/extra → ERROR (block):
  - braces:   {0} {name} {0:F2}
  - tags:     <b> </b> <color=#fff>
  - brackets: [player_name] [HP]
  - printf:   %s %d %1$s %.2f %@
  - CN engine control codes: \c[3] \n[1] \v[10] (RPG-Maker style)

2. CN full-width MARKUP brackets — count parity per char (the CONTENT inside is translated,
  only the brackets must survive) → WARNING:
  - 【】《》「」『』   (item/skill/quote wrappers common in Chinese game text)

NO-OP when the source has none of these, so plain prose is never falsely flagged. Bare
numbers/percent (e.g. "+20%") and full-width （）［］ are intentionally NOT enforced —
translators legitimately reformat/ASCII-ify them, so exact-match would be too noisy.
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
    re.compile(r"\\[a-zA-Z]+\[\d+\]"),                     # \c[3] \n[1] \v[10] (RPG-Maker)
]

# Chinese full-width markup brackets: keep the bracket chars, translate the content inside.
_CN_BRACKETS = "【】《》「」『』"


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
        # CN full-width markup brackets — char-count parity (content inside is translated).
        bad = [f"{ch}({source.count(ch)}→{draft.count(ch)})"
               for ch in _CN_BRACKETS if (source or "").count(ch) != (draft or "").count(ch)]
        if bad:
            issues.append(QcIssue("format", f"Dấu ngoặc CN không khớp: {', '.join(bad)}", severity="warning"))
        # Line-break parity (count real '\n' + literal '\\n'); softer signal → warning.
        s_lines = (source or "").count("\n") + (source or "").count("\\n")
        d_lines = (draft or "").count("\n") + (draft or "").count("\\n")
        if s_lines != d_lines:
            issues.append(QcIssue("format", f"Số dòng không khớp (nguồn {s_lines} ↔ dịch {d_lines})", severity="warning"))
        return issues
