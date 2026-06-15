"""Ports — interfaces the application layer depends on (Dependency Inversion).

Infrastructure adapters implement these. Using `typing.Protocol` for structural
typing: adapters need not inherit, they just match the shape. This keeps the
domain free of any infrastructure import.
"""
from typing import Protocol, Optional, runtime_checkable

from app.domain.entities import Term


@runtime_checkable
class LLMProvider(Protocol):
    """An OpenAI-compatible chat LLM. Returns the assistant message content."""
    def chat(self, messages: list[dict], max_tokens: int = 1024, temperature: float = 0.2) -> str: ...


class TermbaseRepository(Protocol):
    """Storage for termbase entries (file now, AgentBase Memory later)."""
    def match_in(self, source: str) -> list[Term]: ...
    def search(self, query: str = "", status: Optional[str] = None) -> list[Term]: ...
    def upsert(self, term: Term) -> None: ...
    def archive(self, source: str) -> None: ...


class ReviewChannel(Protocol):
    """Destination for drafts needing human review (file queue now, Teams later)."""
    def enqueue(self, job_id: str, payload: dict) -> None: ...


class CorrectionStore(Protocol):
    """Persists wrong→right corrections and retrieves ones relevant to a source."""
    def save(self, source: str, wrong: str, right: str, note: str = "") -> None: ...
    def for_text(self, source: str) -> list[dict]: ...
