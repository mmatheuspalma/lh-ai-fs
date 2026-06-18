from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from agents import (
    authority_verifier,
    citation_extractor,
    cross_doc_consistency,
    judicial_memo,
)
from agents import quote_checker as quote_checker_agent
from flags import build_summary
from schemas import (
    CitationVerdicts,
    ExtractionResult,
    FactFindings,
    PipelineStatus,
    QuoteVerdicts,
    Summary,
    VerificationReport,
)

MOTION_KEY = "motion_for_summary_judgment"
CASE_NAME = "Rivera v. Harmon Construction Group, Inc."


def _run(name: str, fn):
    """Run an agent thunk, capturing success/failure without raising."""
    try:
        return name, fn(), "ok", None
    except Exception as exc:  # graceful degradation: never let one agent sink the run
        return name, None, "failed", f"{name}: {exc}"


def run_pipeline(
    documents: dict[str, str],
    extractor=citation_extractor.extract,
    verifier=authority_verifier.verify,
    quote_checker=quote_checker_agent.check,
    cross_doc=cross_doc_consistency.check,
    memo=judicial_memo.synthesize,
) -> VerificationReport:
    status = PipelineStatus()
    motion = documents.get(MOTION_KEY, "")

    # --- Stage 1: extraction ---
    name, extraction, st, err = _run("citation_extractor", lambda: extractor(motion))
    status.agents[name] = st
    if err:
        status.errors.append(err)
    extraction = extraction or ExtractionResult()

    # --- Stage 2: independent verifiers, run concurrently ---
    stage2 = [
        ("authority_verifier", lambda: verifier(extraction.citations)),
        ("quote_checker", lambda: quote_checker(extraction.quotes)),
        ("cross_doc_consistency", lambda: cross_doc(documents)),
    ]
    with ThreadPoolExecutor(max_workers=3) as ex:
        results = list(ex.map(lambda pair: _run(pair[0], pair[1]), stage2))

    by_name = {}
    for name, res, st, err in results:
        status.agents[name] = st
        if err:
            status.errors.append(err)
        by_name[name] = res

    citation_findings = (by_name["authority_verifier"] or CitationVerdicts()).findings
    quote_findings = (by_name["quote_checker"] or QuoteVerdicts()).findings
    fact_findings = (by_name["cross_doc_consistency"] or FactFindings()).findings

    # --- Stage 3: judicial memo ---
    name, memo_text, st, err = _run(
        "judicial_memo",
        lambda: memo(citation_findings, quote_findings, fact_findings),
    )
    status.agents[name] = st
    if err:
        status.errors.append(err)
    if memo_text is None:
        memo_text = "Judicial memo unavailable: synthesis agent failed."

    report = VerificationReport(
        case=CASE_NAME,
        generated_at=datetime.now(timezone.utc).isoformat(),
        summary=Summary(total_flags=0),
        citations=citation_findings,
        quotes=quote_findings,
        cross_document=fact_findings,
        judicial_memo=memo_text,
        pipeline_status=status,
    )
    report.summary = build_summary(report)
    return report
