from schemas import (
    VerificationReport, Summary, PipelineStatus, CitationFinding, FactFinding,
)
from evals.scoring import score_report


def _report(citations=None, facts=None):
    return VerificationReport(
        case="t", generated_at="t", summary=Summary(total_flags=0),
        judicial_memo="", pipeline_status=PipelineStatus(),
        citations=citations or [], cross_document=facts or [],
    )


SOURCE = "Privette v. Superior Court ... March 14, 2021 ... Section 335.1 ... 14 feet"


def test_perfect_catch_high_recall_high_precision():
    rep = _report(
        citations=[CitationFinding(citation_id="c1", case_name="Privette v. Superior Court",
                                   verdict="overstates", explanation="", confidence=0.9,
                                   confidence_reasoning="", severity="high")],
        facts=[FactFinding(claim="incident March 14, 2021", status="contradicted",
                           explanation="record says March 12", confidence=0.9,
                           confidence_reasoning="", severity="high")],
    )
    res = score_report(rep, SOURCE)
    assert res["recall"] > 0
    assert res["precision"] == 1.0
    assert res["hallucination_rate"] == 0.0


def test_false_positive_on_negative_control_hurts_precision_and_is_halluc():
    rep = _report(
        citations=[CitationFinding(citation_id="c1",
                                   case_name="California Code of Civil Procedure Section 335.1",
                                   verdict="misattributed", explanation="wrongly flagged SOL",
                                   confidence=0.6, confidence_reasoning="", severity="high")],
    )
    res = score_report(rep, SOURCE)
    assert res["precision"] == 0.0
    assert res["hallucination_rate"] == 1.0
    assert res["false_positives"] == 1


def test_fabricated_citation_not_in_source_is_hallucination():
    rep = _report(
        citations=[CitationFinding(citation_id="c1", case_name="Imaginary v. Nobody",
                                   verdict="likely_fabricated", explanation="", confidence=0.5,
                                   confidence_reasoning="", severity="low")],
    )
    res = score_report(rep, SOURCE)
    assert res["hallucination_rate"] == 1.0


def test_missing_everything_zero_recall():
    res = score_report(_report(), SOURCE)
    assert res["recall"] == 0.0
    assert res["flags_total"] == 0
