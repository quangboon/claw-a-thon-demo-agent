"""QC service — combines deterministic rules (axes #1/#2/#4/#5) with the fluency agent (#3).

Status logic:
  - completeness / term-compliance issue            -> fail (fixable, retry-worthy)
  - need-to-avoid ERROR / format ERROR              -> fail (block, never auto-approve)
  - need-to-avoid WARNING / term-confidence / format WARNING / weak fluency -> needs_review
  - clean                                           -> pass

Rules receive a `context` dict carrying the profile's per-language avoid list and the
target language, so the same rule code serves every (profile, lang).
"""
from __future__ import annotations  # PEP 604 `X | None` hints on Python 3.9

from app.agents.qc_reviewer import QCReviewer
from app.domain.entities import QcIssue, QcVerdict
from app.infrastructure.qc import all_qc_rules

# Axes that always fail the draft. need-to-avoid only blocks when severity == "error".
_HARD_FAIL_AXES = {"completeness", "term-compliance"}


class QCService:
    def __init__(self, reviewer: QCReviewer, fluency_threshold: float = 3.0):
        self._reviewer = reviewer
        self._fluency_threshold = fluency_threshold

    def review(self, source: str, draft: str, matched_terms: list,
               avoid_list: list | None = None, target_lang: str = "vi",
               format_config: dict | None = None) -> QcVerdict:
        context = {"avoid": avoid_list or [], "target_lang": target_lang, "format": format_config or {}}
        issues: list[QcIssue] = []
        for rule in all_qc_rules():
            issues.extend(rule.check(source, draft, matched_terms, context))

        # Only spend an LLM call on fluency if the deterministic axes passed.
        fluency: float | None = None
        if not issues:
            fluency = self._reviewer.score_fluency(source, draft)
            if fluency < self._fluency_threshold:
                issues.append(QcIssue("fluency", f"Độ trôi chảy thấp ({fluency}/5)", severity="warning"))

        blocking = any(i.axis in _HARD_FAIL_AXES for i in issues) or \
            any(i.axis in {"need-to-avoid", "format"} and i.severity == "error" for i in issues)
        if blocking:
            status = "fail"
        elif issues:
            status = "needs_review"
        else:
            status = "pass"
        return QcVerdict(status=status, issues=issues, fluency_score=fluency)
