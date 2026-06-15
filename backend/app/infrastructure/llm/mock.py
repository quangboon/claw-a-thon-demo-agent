"""Deterministic mock LLM — for offline runs and tests (no network, no key).

Produces output that passes QC so the happy-path pipeline yields `auto_approved`
offline (Guide Bước 1). Heuristic by call type:
  - fluency review prompt ("Điểm 1-5") -> "5"
  - translation prompt                 -> a clean draft echoing every glossary VI term
"""
import re

from app.infrastructure.llm.registry import register_llm


class MockLLM:
    def chat(self, messages: list, max_tokens: int = 1024, temperature: float = 0.2) -> str:
        text = "\n".join(m.get("content", "") for m in messages)
        # Fluency reviewer asks for a 1–5 score.
        if "Điểm 1-5" in text or "1–5" in text:
            return "5"
        # Translator: emit a clean draft that includes every required glossary VI term
        # (so term-compliance passes) with no placeholder characters.
        vis = [v.strip() for v in re.findall(r"→\s*(.+)", text)]
        if vis:
            return "Bản dịch giả gồm các thuật ngữ: " + ", ".join(vis) + "."
        return "Bản dịch giả cho nội dung nguồn."


@register_llm("mock")
def _build(settings=None):
    return MockLLM()
