"""Glossary formatting — turn matched terms into prompt-injectable lines.

Pure function (no I/O); used by the Translator (Phase 03) and QC term-compliance check.
Multi-language: a term's translation for `target_lang` comes from `Term.translation()`
(the `vi` column for VI, the `targets` map for others). Terms with no translation for
the requested language are skipped (the glossary only asserts what it knows).
"""
from app.domain.entities import Term


def glossary_lines(terms: list[Term], target_lang: str = "vi") -> str:
    """Render matched terms as 'ZH → <target>' lines for prompt injection."""
    out = []
    for t in terms:
        tgt = t.translation(target_lang)
        if tgt:
            out.append(f"{t.source} → {tgt}")
    return "\n".join(out)
