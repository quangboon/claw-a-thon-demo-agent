"""Full-flow check — run the golden set through the pipeline and assert outcomes.

Usage (from project root):
    PYTHONPATH=backend python backend/cli/run_flowcheck.py --mock   # deterministic, no network
    PYTHONPATH=backend python backend/cli/run_flowcheck.py          # real model (prints pass rate)

In --mock mode every case must pass (exit 1 otherwise). In real mode it reports the
pass rate (model variance expected) and exits 0.
"""
import argparse
import json
import sys
from pathlib import Path

from app.composition import build_translation_service

DEFAULT_GOLDEN = "backend/eval/golden_set.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(description="Golden-set full-flow check")
    parser.add_argument("--golden", default=DEFAULT_GOLDEN)
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    cases = [json.loads(l) for l in Path(args.golden).read_text(encoding="utf-8").splitlines() if l.strip()]
    service = build_translation_service(llm_backend="mock" if args.mock else None)

    passed = 0
    for c in cases:
        res = service.run(c["source"])
        out_low = res["output"].lower()
        decision_ok = res["decision"] == c["expect"]
        terms_ok = all(t.lower() in out_low for t in c.get("must_contain", []))
        ok = decision_ok and terms_ok
        passed += ok
        flag = "PASS" if ok else "FAIL"
        print(f"[{flag}] {c['source'][:24]:<24} decision={res['decision']} "
              f"terms_ok={terms_ok} (attempts={res['attempts']})")

    total = len(cases)
    print(f"\n{passed}/{total} passed")
    if args.mock and passed != total:
        sys.exit(1)  # mock is deterministic — any failure is a real regression


if __name__ == "__main__":
    main()
