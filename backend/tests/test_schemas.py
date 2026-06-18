import pytest
from pydantic import ValidationError
from schemas import (
    Citation, Quote, ExtractionResult, CitationFinding, CitationVerdicts,
    QuoteFinding, FactFinding, Evidence, VerificationReport, Summary, PipelineStatus,
)


def test_extraction_result_defaults_empty():
    er = ExtractionResult()
    assert er.citations == [] and er.quotes == []


def test_citation_finding_requires_valid_confidence():
    with pytest.raises(ValidationError):
        CitationFinding(
            citation_id="c1", case_name="X", verdict="supports",
            explanation="e", confidence=1.5, confidence_reasoning="r", severity="low",
        )


def test_citation_finding_rejects_unknown_verdict():
    with pytest.raises(ValidationError):
        CitationFinding(
            citation_id="c1", case_name="X", verdict="banana",
            explanation="e", confidence=0.5, confidence_reasoning="r", severity="low",
        )


def test_fact_finding_roundtrips():
    f = FactFinding(
        claim="incident was March 14", status="contradicted",
        evidence=[Evidence(doc="police_report", excerpt="March 12")],
        explanation="dates differ", confidence=0.9,
        confidence_reasoning="three docs agree", severity="high",
    )
    assert f.status == "contradicted"
    assert f.evidence[0].doc == "police_report"


def test_verification_report_minimal():
    r = VerificationReport(
        case="Rivera v. Harmon", generated_at="2026-06-18T00:00:00Z",
        summary=Summary(total_flags=0, by_severity={}, by_category={}),
        judicial_memo="none", pipeline_status=PipelineStatus(),
    )
    assert r.citations == [] and r.quotes == [] and r.cross_document == []
