from __future__ import annotations

from flags import collect_flags
from evals.gold import GOLD, NEGATIVE_CONTROLS
from schemas import VerificationReport


def _referent_in_source(flag: dict, source: str) -> bool:
    """Citations/quotes refer to text that must appear in the brief. A flag whose
    referent is absent means the pipeline invented it (hallucination). Facts are
    paraphrased, so we skip this check for them and rely on negative-control hits."""
    if flag["category"] == "fact":
        return True
    ref = (flag.get("referent") or "").strip().lower()
    if not ref:
        return False
    probe = ref[:40]
    return probe in source.lower()


def score_report(report: VerificationReport, source_text: str) -> dict:
    flags = collect_flags(report)

    # Recall: fraction of known gold flaws caught by at least one flag.
    caught = []
    missed = []
    for g in GOLD:
        if any(g.matches(f) for f in flags):
            caught.append(g.id)
        else:
            missed.append(g.id)
    recall = len(caught) / len(GOLD) if GOLD else 0.0

    # Precision + hallucination, classified per flag.
    tp = fp = 0
    hallucinations = []
    false_positives = []
    # Precision is computed per-flag (the standard per-prediction definition). Recall
    # is per-gold-entry. Note: if an agent emitted several redundant flags that all map
    # to the same gold flaw, each would count as a separate TP — gpt-4o emits one
    # finding per citation/fact here so it does not arise, but a dedup on the matched
    # gold id would be the fix if a noisier model were used.
    for f in flags:
        is_gold = any(g.matches(f) for g in GOLD)
        is_neg = any(nc.matches(f) for nc in NEGATIVE_CONTROLS)
        in_source = _referent_in_source(f, source_text)

        if is_gold and not is_neg:
            tp += 1
        else:
            fp += 1
            false_positives.append(f["referent"])

        if is_neg or not in_source:
            hallucinations.append(f["referent"])

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    halluc_rate = len(hallucinations) / len(flags) if flags else 0.0

    by_cat = {}
    for cat in ("citation", "quote", "fact"):
        cat_gold = [g for g in GOLD if g.category == cat]
        cat_caught = [g for g in cat_gold if any(g.matches(f) for f in flags)]
        by_cat[cat] = {"caught": len(cat_caught), "total": len(cat_gold)}

    return {
        "recall": round(recall, 3),
        "precision": round(precision, 3),
        "hallucination_rate": round(halluc_rate, 3),
        "flags_total": len(flags),
        "true_positives": tp,
        "false_positives": fp,
        "caught_ids": caught,
        "missed_ids": missed,
        "false_positive_refs": false_positives,
        "hallucinated_refs": hallucinations,
        "by_category": by_cat,
    }
