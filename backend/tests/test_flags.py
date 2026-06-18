from schemas import CitationFinding, QuoteFinding, FactFinding, VerificationReport, Summary, PipelineStatus
from flags import collect_flags, build_summary


def _report(citations=None, quotes=None, facts=None):
    return VerificationReport(
        case="t", generated_at="t",
        summary=Summary(total_flags=0), judicial_memo="", pipeline_status=PipelineStatus(),
        citations=citations or [], quotes=quotes or [], cross_document=facts or [],
    )


def test_collect_flags_filters_non_problems():
    rep = _report(
        citations=[
            CitationFinding(citation_id="c1", case_name="Privette", verdict="overstates",
                            explanation="", confidence=0.8, confidence_reasoning="", severity="high"),
            CitationFinding(citation_id="c2", case_name="Good", verdict="supports",
                            explanation="", confidence=0.9, confidence_reasoning="", severity="low"),
            CitationFinding(citation_id="c3", case_name="Obscure", verdict="could_not_verify",
                            explanation="", confidence=0.3, confidence_reasoning="", severity="low"),
        ],
    )
    flags = collect_flags(rep)
    names = {f["referent"] for f in flags}
    assert names == {"Privette"}  # supports + could_not_verify are NOT flags


def test_collect_flags_facts_and_quotes():
    rep = _report(
        quotes=[QuoteFinding(quote_id="q1", quoted_text="never liable", verdict="overstated",
                             explanation="", confidence=0.7, confidence_reasoning="", severity="high")],
        facts=[
            FactFinding(claim="March 14", status="contradicted", explanation="",
                        confidence=0.9, confidence_reasoning="", severity="high"),
            FactFinding(claim="8 years experience", status="unverifiable", explanation="",
                        confidence=0.5, confidence_reasoning="", severity="low"),
        ],
    )
    flags = collect_flags(rep)
    cats = sorted(f["category"] for f in flags)
    assert cats == ["fact", "quote"]  # unverifiable fact is NOT a flag


def test_build_summary_counts():
    rep = _report(
        citations=[CitationFinding(citation_id="c1", case_name="P", verdict="overstates",
                                   explanation="", confidence=0.8, confidence_reasoning="", severity="high")],
        facts=[FactFinding(claim="d", status="contradicted", explanation="",
                           confidence=0.9, confidence_reasoning="", severity="high")],
    )
    s = build_summary(rep)
    assert s.total_flags == 2
    assert s.by_severity["high"] == 2
    assert s.by_category["citation"] == 1 and s.by_category["fact"] == 1
