"""Translate CLI — run the full pipeline on a file or inline source.

Usage (from project root):
    PYTHONPATH=backend python backend/cli/translate.py --infile backend/data/sample_input.txt
    PYTHONPATH=backend python backend/cli/translate.py --source "灵石 +20%" --mock
"""
import argparse
import json
from pathlib import Path

from app.composition import build_translation_service


def main() -> None:
    parser = argparse.ArgumentParser(description="ZH→VI translate + QC pipeline")
    parser.add_argument("--infile")
    parser.add_argument("--source")
    parser.add_argument("--target-lang", default="vi")
    parser.add_argument("--mock", action="store_true", help="use mock LLM (no key/network)")
    args = parser.parse_args()

    if not args.infile and not args.source:
        parser.error("provide --infile or --source")
    source = args.source or Path(args.infile).read_text(encoding="utf-8").strip()

    service = build_translation_service(llm_backend="mock" if args.mock else None)
    result = service.run(source)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
