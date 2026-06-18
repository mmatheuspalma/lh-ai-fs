from schemas import (
    ExtractionResult, Citation, Quote, CitationVerdicts, CitationFinding,
    QuoteVerdicts, FactFindings, FactFinding, VerificationReport,
)
from pipeline import run_pipeline


def _agents(extract=None, verify=None, quote=None, cross=None, memo=None):
    """Build a kwargs dict of stub agents, defaulting each to a benign stub."""
    return dict(
        extractor=extract or (lambda motion: ExtractionResult()),
        verifier=verify or (lambda cits: CitationVerdicts()),
        quote_checker=quote or (lambda qs: QuoteVerdicts()),
        cross_doc=cross or (lambda docs: FactFindings()),
        memo=memo or (lambda citations, quotes, facts: "memo"),
    )


def test_happy_path_assembles_report():
    docs = {"motion_for_summary_judgment": "text"}
    agents = _agents(
        extract=lambda m: ExtractionResult(citations=[Citation(
            id="c1", case_name="Privette", proposition="p", raw_text="r")]),
        verify=lambda c: CitationVerdicts(findings=[CitationFinding(
            citation_id="c1", case_name="Privette", verdict="overstates",
            explanation="", confidence=0.8, confidence_reasoning="", severity="high")]),
        cross=lambda d: FactFindings(findings=[FactFinding(
            claim="March 14", status="contradicted", explanation="",
            confidence=0.9, confidence_reasoning="", severity="high")]),
    )
    report = run_pipeline(docs, **agents)
    assert isinstance(report, VerificationReport)
    assert report.summary.total_flags == 2
    assert report.pipeline_status.agents["citation_extractor"] == "ok"
    assert report.pipeline_status.agents["authority_verifier"] == "ok"


def test_extractor_failure_degrades_gracefully():
    def boom(motion):
        raise RuntimeError("LLM down")

    docs = {"motion_for_summary_judgment": "text"}
    report = run_pipeline(docs, **_agents(extract=boom))
    assert report.pipeline_status.agents["citation_extractor"] == "failed"
    assert any("citation_extractor" in e for e in report.pipeline_status.errors)
    assert isinstance(report, VerificationReport)
    assert report.citations == []


def test_one_stage2_agent_failure_does_not_sink_others():
    def boom(cits):
        raise RuntimeError("verifier down")

    docs = {"motion_for_summary_judgment": "text"}
    agents = _agents(
        verify=boom,
        cross=lambda d: FactFindings(findings=[FactFinding(
            claim="x", status="contradicted", explanation="",
            confidence=0.9, confidence_reasoning="", severity="high")]),
    )
    report = run_pipeline(docs, **agents)
    assert report.pipeline_status.agents["authority_verifier"] == "failed"
    assert report.pipeline_status.agents["cross_doc_consistency"] == "ok"
    assert len(report.cross_document) == 1


def test_memo_failure_uses_fallback():
    def boom(citations, quotes, facts):
        raise RuntimeError("memo down")

    docs = {"motion_for_summary_judgment": "text"}
    report = run_pipeline(docs, **_agents(memo=boom))
    assert report.pipeline_status.agents["judicial_memo"] == "failed"
    assert "unavailable" in report.judicial_memo.lower()
