"""Term Extractor — agent #1 (offline).

Reads a ZH corpus and proposes game-domain term candidates (ZH→VI) via the LLM.
Output is *candidates* for human review, never auto-committed to the termbase.
"""
import json
import logging
import re

from app.domain.ports import LLMProvider

logger = logging.getLogger(__name__)

_SYSTEM = (
    "Bạn là chuyên gia bản địa hoá game Trung→Việt. Trích các THUẬT NGỮ chuyên ngành game "
    "(vật phẩm, kỹ năng, địa danh, cơ chế, tiền tệ, cảnh giới tu luyện) từ văn bản tiếng Trung. "
    "Bỏ qua từ phổ thông. Chỉ trả về JSON array, không giải thích."
)
_USER_TMPL = (
    "Trích thuật ngữ từ văn bản sau. Mỗi mục: "
    '{{"source": "<chữ Hán>", "vi": "<bản dịch tiếng Việt chuẩn>", '
    '"category": "<item|skill|place|mechanic|currency|realm>", "note": "<ghi chú ngắn>"}}.\n'
    "Trả về JSON array thuần.\n\n---\n{corpus}\n---"
)


def _parse_json_array(text: str) -> list[dict]:
    """Robustly extract a JSON array from an LLM response (handles ```json fences)."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = cleaned.find("["), cleaned.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON array found in LLM output: {text[:200]!r}")
    return json.loads(cleaned[start : end + 1])


class TermExtractor:
    def __init__(self, llm: LLMProvider):
        self._llm = llm

    def extract(self, corpus: str, max_tokens: int = 4096) -> list[dict]:
        out = self._llm.chat(
            [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": _USER_TMPL.format(corpus=corpus)},
            ],
            max_tokens=max_tokens,
        )
        raw = _parse_json_array(out)
        # Dedupe by source (keep first), drop entries missing source/vi.
        seen, candidates = set(), []
        for item in raw:
            src = (item.get("source") or "").strip()
            vi = (item.get("vi") or "").strip()
            if not src or not vi or src in seen:
                continue
            seen.add(src)
            candidates.append(
                {"source": src, "vi": vi, "category": item.get("category", ""), "note": item.get("note", "")}
            )
        logger.info("Extracted %d term candidates", len(candidates))
        return candidates
