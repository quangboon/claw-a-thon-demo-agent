"""Glossary formatting — turn matched terms into prompt-injectable lines.

Pure function (no I/O); used by the Translator (Phase 03) and QC term-compliance check.
"""
from app.domain.entities import Term


def glossary_lines(terms: list[Term]) -> str:
    """Render matched terms as 'ZH → VI' lines for prompt injection."""
    return "\n".join(f"{t.source} → {t.vi}" for t in terms)
