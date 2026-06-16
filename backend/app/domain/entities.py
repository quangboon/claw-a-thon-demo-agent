"""Domain entities — pure data, no external dependencies (stdlib only)."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Term:
    """A termbase entry: ZH source surface form → canonical translation(s).

    `vi` stays the primary/default VI translation (v1 compatibility). `targets`
    holds extra target-language translations (e.g. {"th": "...", "en": "..."}),
    so a single termbase serves a multi-language profile without a schema break.
    """
    source: str                     # ZH surface form (e.g. "灵石")
    vi: str                         # canonical VI translation (e.g. "Linh Thạch")
    category: str = ""              # item | skill | place | mechanic | currency ...
    note: str = ""
    trust_score: float = 1.0        # raised on use/approve, lowered when long unused
    last_used: Optional[str] = None  # ISO date string
    status: str = "active"          # active | archived
    targets: dict = field(default_factory=dict)  # {lang: translation} for non-VI langs

    def translation(self, lang: str = "vi") -> str:
        """Translation for `lang`: `vi` is the default column, others read `targets`."""
        if lang == "vi":
            return self.vi
        return self.targets.get(lang, "")


@dataclass
class Profile:
    """A Domain Pack: one team/business owns its own terms, tone, avoid-list, examples.

    Pure config — adding a team means adding a profile, never editing core code (OCP).
    """
    id: str
    name: str = ""
    source_lang: str = "zh"
    target_langs: list = field(default_factory=lambda: ["vi"])
    char_name_convention: str = ""  # optional note on character-name / POV handling
    format_enabled: bool = True     # run the format-preservation QC rule for this profile
    format_extra_tokens: list = field(default_factory=list)  # extra literal tokens to preserve verbatim


@dataclass
class AvoidEntry:
    """A need-to-avoid rule for a (profile, lang): a banned word or pattern."""
    term: str                       # the banned surface form (or regex if is_pattern)
    category: str = ""              # political | monarchy | competitor | tone ...
    severity: str = "warning"       # warning -> needs_review | error -> block (no auto-approve)
    is_pattern: bool = False        # treat `term` as a regex instead of a literal


@dataclass
class Example:
    """A few-shot example for a (profile, lang): a good (and optionally bad) rendering."""
    source: str                     # ZH source snippet
    good: str                       # the preferred translation
    bad: str = ""                   # an anti-example to steer away from (optional)
    lang: str = "vi"


@dataclass
class QcIssue:
    """A single QC finding on one of the three review axes."""
    axis: str                       # completeness | term-compliance | fluency
    message: str
    severity: str = "error"         # error | warning


@dataclass
class QcVerdict:
    """Aggregated QC result for a translation draft."""
    status: str                     # pass | needs_review | fail
    issues: list[QcIssue] = field(default_factory=list)
    fluency_score: Optional[float] = None
