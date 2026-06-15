"""Translator — agent #2.

Translates ZH→VI, forced to obey the injected glossary, and (on a self-correct
pass) given QC feedback. Returns the PURE translation (no footer); the AI-disclosure
footer is appended at the output layer so QC reviews the translation content itself.
"""
from app.domain.ports import LLMProvider

# Mandatory AI-disclosure footer (Rulebook). Appended to final output, not reviewed by QC.
AI_FOOTER = "— Nội dung dịch bởi AI"

_SYSTEM = (
    "Bạn là dịch giả chuyên nghiệp Trung→Việt cho game. Dịch ĐẦY ĐỦ, tự nhiên, đúng văn phong game. "
    "BẮT BUỘC dùng đúng thuật ngữ trong glossary nếu có. Chỉ trả về bản dịch tiếng Việt, không giải thích."
)


def with_footer(translation: str) -> str:
    """Append the mandatory AI-disclosure footer to a final translation."""
    return f"{translation}\n\n{AI_FOOTER}"


class Translator:
    def __init__(self, llm: LLMProvider):
        self._llm = llm

    def translate(self, source: str, glossary: str = "", corrections: str = "",
                  feedback: str = "", max_tokens: int = 1024) -> str:
        parts = [f"Văn bản nguồn (tiếng Trung):\n{source}"]
        if glossary:
            parts.append(f"\nGlossary BẮT BUỘC dùng đúng (ZH → VI):\n{glossary}")
        if corrections:
            parts.append(f"\nTránh các lỗi đã từng mắc:\n{corrections}")
        if feedback:
            parts.append(f"\nLần dịch trước bị QC từ chối, sửa các vấn đề sau:\n{feedback}")
        parts.append("\nTrả về bản dịch tiếng Việt:")
        out = self._llm.chat(
            [{"role": "system", "content": _SYSTEM}, {"role": "user", "content": "\n".join(parts)}],
            max_tokens=max_tokens,
        )
        return out.strip()
