"""Domain entities — pure data, no external dependencies (stdlib only)."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Term:
    """A termbase entry: ZH source surface form → canonical VI translation."""
    source: str                     # ZH surface form (e.g. "灵石")
    vi: str                         # canonical VI translation (e.g. "Linh Thạch")
    category: str = ""              # item | skill | place | mechanic | currency ...
    note: str = ""
    trust_score: float = 1.0        # raised on use/approve, lowered when long unused
    last_used: Optional[str] = None  # ISO date string
    status: str = "active"          # active | archived


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
