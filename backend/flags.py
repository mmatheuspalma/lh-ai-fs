from __future__ import annotations

from collections import Counter

from schemas import Summary, VerificationReport

CITATION_PROBLEMS = {"overstates", "misattributed", "likely_fabricated", "wrong_jurisdiction"}
QUOTE_PROBLEMS = {"altered", "overstated"}
FACT_PROBLEMS = {"contradicted"}


def collect_flags(report: VerificationReport) -> list[dict]:
    """Normalize all 'problem' findings into uniform flag dicts.

    'could_not_verify'/'unverifiable' are honest uncertainty, NOT flags, so they are
    excluded here (they neither help recall nor hurt precision).
    """
    flags: list[dict] = []
    for c in report.citations:
        if c.verdict in CITATION_PROBLEMS:
            flags.append({
                "category": "citation", "referent": c.case_name, "case_name": c.case_name,
                "verdict": c.verdict, "severity": c.severity, "text": c.explanation,
            })
    for q in report.quotes:
        if q.verdict in QUOTE_PROBLEMS:
            flags.append({
                "category": "quote", "referent": q.quoted_text, "quoted_text": q.quoted_text,
                "verdict": q.verdict, "severity": q.severity, "text": q.explanation,
            })
    for f in report.cross_document:
        if f.status in FACT_PROBLEMS:
            flags.append({
                "category": "fact", "referent": f.claim, "claim": f.claim,
                "verdict": f.status, "severity": f.severity, "text": f.explanation,
            })
    return flags


def build_summary(report: VerificationReport) -> Summary:
    flags = collect_flags(report)
    by_sev = Counter(f["severity"] for f in flags)
    by_cat = Counter(f["category"] for f in flags)
    return Summary(
        total_flags=len(flags),
        by_severity=dict(by_sev),
        by_category=dict(by_cat),
    )
