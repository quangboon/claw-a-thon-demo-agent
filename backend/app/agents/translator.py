"""Translator — agent #2 (profile-aware, multi-language).

Translates ZH→{target_lang}, forced to obey the injected glossary, the profile's
tone guide, its need-to-avoid list, and few-shot examples. On a self-correct pass it
also receives QC feedback. Returns the PURE translation (no footer); the AI-disclosure
footer is appended at the output layer so QC reviews the translation content itself.

Prompt scaffolding is ENGLISH (token-efficient, lang-agnostic); the glossary, examples
and tone content stay in the target language.
"""
from __future__ import annotations

from app.domain.entities import Example
from app.domain.ports import LLMProvider

# Human-readable target-language names for the (English) prompt.
LANG_NAMES = {"vi": "Vietnamese", "th": "Thai", "en": "English"}

# Mandatory AI-disclosure footer per target language (Rulebook). Appended to final
# output, not reviewed by QC.
FOOTERS = {
    "vi": "— Nội dung dịch bởi AI",
    "th": "— แปลโดย AI",
    "en": "— Translated by AI",
}


def with_footer(translation: str, target_lang: str = "vi") -> str:
    """Append the mandatory AI-disclosure footer (per target language)."""
    return f"{translation}\n\n{FOOTERS.get(target_lang, FOOTERS['vi'])}"


def _system_prompt(target_lang: str) -> str:
    lang = LANG_NAMES.get(target_lang, target_lang)
    return (
        f"You are a professional Chinese-to-{lang} video-game translator. "
        f"Translate fully and naturally in proper game register. "
        f"You MUST use the provided glossary verbatim. "
        f"You MUST NOT use any banned term from the avoid list. "
        f"Match the requested tone. "
        f"Return ONLY the {lang} translation — no explanations."
    )


class Translator:
    def __init__(self, llm: LLMProvider):
        self._llm = llm

    def translate(self, source: str, glossary: str = "", corrections: str = "",
                  feedback: str = "", tone: str = "", avoid: str = "",
                  examples: list[Example] | None = None, target_lang: str = "vi",
                  max_tokens: int = 1024) -> str:
        lang = LANG_NAMES.get(target_lang, target_lang)
        parts = [f"Source text (Chinese):\n{source}"]
        if glossary:
            parts.append(f"\nGlossary — MUST use exactly (ZH to {lang}):\n{glossary}")
        if tone:
            parts.append(f"\nTone guide for this profile:\n{tone}")
        if avoid:
            parts.append(f"\nMUST NOT use these banned terms:\n{avoid}")
        if examples:
            parts.append("\nFew-shot examples (follow the GOOD style, avoid the BAD one):\n"
                         + _format_examples(examples))
        if corrections:
            parts.append(f"\nAvoid mistakes made before:\n{corrections}")
        if feedback:
            parts.append(f"\nThe previous attempt was rejected by QC; fix these issues:\n{feedback}")
        parts.append(f"\nReturn the {lang} translation:")
        out = self._llm.chat(
            [{"role": "system", "content": _system_prompt(target_lang)},
             {"role": "user", "content": "\n".join(parts)}],
            max_tokens=max_tokens,
        )
        return out.strip()


def _format_examples(examples: list[Example]) -> str:
    lines = []
    for ex in examples:
        lines.append(f"- ZH: {ex.source}\n  GOOD: {ex.good}" + (f"\n  BAD: {ex.bad}" if ex.bad else ""))
    return "\n".join(lines)
