"""File-backed termbase repository (MVP). Implements the TermbaseRepository port.

Storage: a JSON array of term objects in `termbase.json`. Swappable later for an
AgentBase Memory adapter implementing the same port (no business-logic changes).
"""
import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from app.domain.entities import Term


class FileTermbaseRepository:
    def __init__(self, path: str):
        self._path = Path(path)
        self._terms: list[Term] = self._load()

    def _load(self) -> list[Term]:
        if not self._path.exists():
            return []
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return [Term(**item) for item in data]

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(t) for t in self._terms]
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def match_in(self, source: str) -> list[Term]:
        """Return active terms whose ZH source appears in `source`.

        Chinese has no word spaces, so substring match is sufficient and reliable.
        Sort by source length desc so longer (more specific) terms win.
        """
        hits = [t for t in self._terms if t.status == "active" and t.source and t.source in source]
        return sorted(hits, key=lambda t: len(t.source), reverse=True)

    def search(self, query: str = "", status: Optional[str] = None) -> list[Term]:
        result = self._terms
        if status:
            result = [t for t in result if t.status == status]
        if query:
            q = query.lower()
            result = [t for t in result if q in t.source.lower() or q in t.vi.lower()]
        return result

    def upsert(self, term: Term) -> None:
        for i, t in enumerate(self._terms):
            if t.source == term.source:
                self._terms[i] = term
                self._save()
                return
        self._terms.append(term)
        self._save()

    def archive(self, source: str) -> None:
        for t in self._terms:
            if t.source == source:
                t.status = "archived"
        self._save()
