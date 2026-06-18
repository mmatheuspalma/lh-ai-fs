"""Single-command eval harness for the BS Detector pipeline.

Usage:  python run_evals.py
Runs the live pipeline once against the case file and scores it against a
hand-labeled gold set (precision / recall / hallucination). Prints an honest report.
"""
from __future__ import annotations

import sys

from evals.gold import GOLD, gold_by_id
from evals.scoring import score_report
from main import load_documents
from pipeline import MOTION_KEY, run_pipeline


def _bar(label: str, value: float) -> str:
    filled = int(round(value * 20))
    return f"{label:<20} {value*100:5.1f}%  [{'#' * filled}{'.' * (20 - filled)}]"


def main() -> int:
    documents = load_documents()
    source = documents.get(MOTION_KEY, "")

    print("Running pipeline against case file (live LLM calls)...\n")
    report = run_pipeline(documents)

    # Surface any agent degradation honestly — it affects the scores.
    bad = {k: v for k, v in report.pipeline_status.agents.items() if v != "ok"}
    if bad:
        print(f"WARNING: degraded agents: {bad}")
        for e in report.pipeline_status.errors:
            print(f"  - {e}")
        print()

    res = score_report(report, source)

    print("=" * 56)
    print("BS DETECTOR — EVAL REPORT")
    print("=" * 56)
    print(_bar("Recall", res["recall"]))
    print(_bar("Precision", res["precision"]))
    print(_bar("Hallucination", res["hallucination_rate"]))
    print(f"\nFlags raised: {res['flags_total']}  "
          f"(TP={res['true_positives']}, FP={res['false_positives']})")

    print("\nPer-category recall:")
    for cat, d in res["by_category"].items():
        print(f"  {cat:<10} {d['caught']}/{d['total']}")

    print("\nCaught gold flaws:")
    for gid in res["caught_ids"]:
        print(f"  [x] {gid:<26} {gold_by_id(gid).description}")
    print("\nMissed gold flaws:")
    for gid in res["missed_ids"]:
        print(f"  [ ] {gid:<26} {gold_by_id(gid).description}")

    if res["false_positive_refs"]:
        print("\nFalse positives (flagged but not a known flaw):")
        for ref in res["false_positive_refs"]:
            print(f"  ! {ref}")
    if res["hallucinated_refs"]:
        print("\nPossible hallucinations (referent absent from source / negative control):")
        for ref in res["hallucinated_refs"]:
            print(f"  ? {ref}")

    print("\n" + "=" * 56)
    print("Note: scores reflect a single live run at temperature=0 and may drift")
    print("slightly between runs. Matching is deterministic on structured keys.")
    print("=" * 56)
    return 0


if __name__ == "__main__":
    sys.exit(main())
