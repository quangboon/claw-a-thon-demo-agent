"""Term Curator — agent #4 (offline / periodic).

Reads accumulated corrections (flywheel) and proposes NEW termbase entries implied by
recurring human fixes, excluding terms already in the termbase. Proposals are for human
review (never auto-committed) and start at a lower trust_score than approved terms.
"""
import logging

from app.agents.term_extractor import _parse_json_array  # reuse robust JSON-array parser (DRY)
from app.domain.ports import LLMProvider

logger = logging.getLogger(__name__)

# Proposed terms start below approved (1.0) — they still need human sign-off.
PROPOSAL_TRUST = 0.6

_SYSTEM = (
    "Bạn là người quản lý termbase game Trung→Việt. Dựa trên các lần người duyệt SỬA bản dịch, "
    "hãy phát hiện THUẬT NGỮ game nên thêm vào termbase (cặp chữ Hán → bản dịch tiếng Việt đúng). "
    "Chỉ trả về JSON array, không giải thích."
)


class TermCurator:
    def __init__(self, llm: LLMProvider):
        self._llm = llm

    def propose_terms(self, corrections: list, existing_sources: set, max_tokens: int = 2048) -> list:
        if not corrections:
            return []
        lines = [
            f"- nguồn: {c.get('source','')} | sai: {c.get('wrong','')} | đúng: {c.get('right','')}"
            for c in corrections
        ]
        user = (
            "Các lần sửa:\n" + "\n".join(lines) +
            '\n\nTrả về JSON array các thuật ngữ NÊN THÊM: '
            '[{"source":"<chữ Hán>","vi":"<bản dịch đúng>","category":"<item|skill|place|mechanic|currency|realm>","note":""}]'
        )
        raw = _parse_json_array(self._llm.chat(
            [{"role": "system", "content": _SYSTEM}, {"role": "user", "content": user}],
            max_tokens=max_tokens,
        ))
        proposals = []
        seen = set()
        for item in raw:
            src = (item.get("source") or "").strip()
            vi = (item.get("vi") or "").strip()
            if not src or not vi or src in existing_sources or src in seen:
                continue  # skip empty + already-known + duplicates
            seen.add(src)
            proposals.append({
                "source": src, "vi": vi,
                "category": item.get("category", ""), "note": item.get("note", ""),
                "trust_score": PROPOSAL_TRUST,
            })
        logger.info("Curator proposed %d new term(s)", len(proposals))
        return proposals
