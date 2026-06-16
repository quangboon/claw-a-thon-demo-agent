"""Run the Term Curator (agent #4) offline over accumulated corrections.

Proposes NEW termbase entries implied by human corrections (for review, not auto-commit).

Usage (from project root):
    PYTHONPATH=backend python backend/cli/run_curator.py
    add --approve to append proposals into termbase.json (after you've reviewed them)
"""
import argparse
import json
from pathlib import Path

from app.composition import build_term_curator
from app.domain.entities import Term
from app.infrastructure.profile_paths import profile_paths
from app.infrastructure.repositories.correction_file import FileCorrectionStore
from app.infrastructure.repositories.termbase_file import FileTermbaseRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Term Curator — propose new terms from corrections (per profile).")
    parser.add_argument("--profile", default="default", help="profile id (resolves corrections + termbase paths)")
    parser.add_argument("--corrections", default=None, help="override corrections path")
    parser.add_argument("--termbase", default=None, help="override termbase path")
    parser.add_argument("--approve", action="store_true", help="append reviewed proposals to termbase")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    paths = profile_paths(args.profile)
    args.corrections = args.corrections or str(paths.corrections)
    args.termbase = args.termbase or str(paths.termbase)
    print(f"profile={args.profile} corrections={args.corrections} termbase={args.termbase}")

    corrections = FileCorrectionStore(args.corrections)._all()
    repo = FileTermbaseRepository(args.termbase)
    existing = {t.source for t in repo.search()}

    curator = build_term_curator(llm_backend="mock" if args.mock else None)
    proposals = curator.propose_terms(corrections, existing)

    print(f"\n{len(proposals)} proposal(s):")
    print(json.dumps(proposals, ensure_ascii=False, indent=2))

    if args.approve:
        for p in proposals:
            repo.upsert(Term(source=p["source"], vi=p["vi"], category=p.get("category", ""),
                             note=p.get("note", ""), trust_score=p.get("trust_score", 0.6)))
        print(f"\nApproved {len(proposals)} proposals → {args.termbase}")
    else:
        print("\n(dry-run) Review proposals, then re-run with --approve.")


if __name__ == "__main__":
    main()
