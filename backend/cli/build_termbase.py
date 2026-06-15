"""Offline termbase builder (Term Extractor agent #1).

Usage (run from project root):
    PYTHONPATH=backend python backend/cli/build_termbase.py --corpus backend/data/zh_corpus.txt
        → extract candidates, print table, write backend/data/termbase.candidates.json
    add --approve to merge candidates into backend/termbase.json (status=active, trust_score=1.0)

Human review: inspect candidates, fix `vi`, then re-run with --approve (KISS: edit the
candidates JSON before approving, or approve then edit termbase.json directly).
"""
import argparse
import json
from pathlib import Path

from app.agents.term_extractor import TermExtractor
from app.domain.entities import Term
from app.infrastructure.llm import get_llm_provider
from app.infrastructure.repositories.termbase_file import FileTermbaseRepository
from app.settings import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Build termbase from a ZH corpus (offline).")
    parser.add_argument("--corpus", default="backend/data/zh_corpus.txt")
    parser.add_argument("--candidates", default="backend/data/termbase.candidates.json")
    parser.add_argument("--termbase", default="backend/termbase.json")
    parser.add_argument("--approve", action="store_true", help="merge candidates into termbase.json")
    parser.add_argument("--mock", action="store_true", help="use mock LLM (no extraction quality)")
    args = parser.parse_args()

    if args.approve:
        # Approve reads the (human-reviewed) candidates file — does NOT re-extract.
        candidates = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
        repo = FileTermbaseRepository(args.termbase)
        for c in candidates:
            repo.upsert(Term(source=c["source"], vi=c["vi"], category=c.get("category", ""), note=c.get("note", "")))
        print(f"Approved {len(candidates)} reviewed terms from {args.candidates} → {args.termbase}")
        return

    # Extract phase: LLM proposes candidates for human review.
    corpus = Path(args.corpus).read_text(encoding="utf-8")
    backend = "mock" if args.mock else settings.llm_backend
    extractor = TermExtractor(get_llm_provider(backend))
    candidates = extractor.extract(corpus)
    Path(args.candidates).write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n{len(candidates)} candidates → {args.candidates}\n")
    print(f"{'SOURCE':<12}{'VI':<28}{'CATEGORY':<12}NOTE")
    for c in candidates:
        print(f"{c['source']:<12}{c['vi']:<28}{c['category']:<12}{c['note']}")
    print("\nReview/edit the candidates JSON, then re-run with --approve to write termbase.json")


if __name__ == "__main__":
    main()
