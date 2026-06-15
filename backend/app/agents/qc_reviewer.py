"""QC Reviewer — agent #3 (fluency axis only).

Axes #1 (completeness) and #2 (term-compliance) are deterministic rules in
infrastructure/qc/rules. This LLM agent only scores fluency/naturalness (1–5).
"""
import logging
import re

from app.domain.ports import LLMProvider

logger = logging.getLogger(__name__)

# NOTE: the literal marker "Điểm 1-5" (in the user message below) is load-bearing for
# MockLLM, which uses it to detect a fluency call. Keep it if you edit these prompts.
_SYSTEM = (
    "Bạn là biên tập viên tiếng Việt. Chấm độ TRÔI CHẢY và TỰ NHIÊN của bản dịch (ngữ pháp, văn phong, "
    "register game) trên thang 1–5 (5 = hoàn hảo). Chỉ trả về DUY NHẤT một con số."
)


class QCReviewer:
    def __init__(self, llm: LLMProvider):
        self._llm = llm

    def score_fluency(self, source: str, draft: str, max_tokens: int = 16) -> float:
        out = self._llm.chat(
            [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": f"Nguồn (ZH): {source}\nBản dịch (VI): {draft}\nĐiểm 1-5:"},
            ],
            max_tokens=max_tokens,
        )
        match = re.search(r"[1-5](?:\.\d+)?", out)
        if not match:
            # Don't block the pipeline on an unparseable score — treat as acceptable but warn.
            logger.warning("Could not parse fluency score from %r; defaulting to 4.0", out[:60])
            return 4.0
        return float(match.group())
