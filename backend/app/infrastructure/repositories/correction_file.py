"""File-backed correction store (flywheel). Implements the CorrectionStore port.

Appends wrong→right corrections to corrections.jsonl and retrieves ones relevant to a
source via shared Han bigrams (so a correction about 灵石 resurfaces when 灵石 reappears).
"""
import json
import re
from pathlib import Path

_HAN = re.compile(r"[一-鿿]")


def _han_bigrams(text: str) -> set:
    """All 2-char Han substrings in `text` (used as a cheap relevance key)."""
    han = "".join(ch for ch in text if _HAN.match(ch))
    return {han[i : i + 2] for i in range(len(han) - 1)} if len(han) >= 2 else set(han)


class FileCorrectionStore:
    def __init__(self, path: str):
        self._path = Path(path)

    def _all(self) -> list:
        if not self._path.exists():
            return []
        return [json.loads(line) for line in self._path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def all(self) -> list:
        """Public: every recorded correction (most recent last)."""
        return self._all()

    def save(self, source: str, wrong: str, right: str, note: str = "") -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        record = {"source": source, "wrong": wrong, "right": right, "note": note}
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def for_text(self, source: str, top_k: int = 5) -> list:
        """Corrections sharing a Han bigram with `source` (most recent first, capped)."""
        query = _han_bigrams(source)
        relevant = [c for c in self._all() if _han_bigrams(c.get("source", "")) & query]
        return list(reversed(relevant))[:top_k]
