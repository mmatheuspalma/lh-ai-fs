import agents.citation_extractor as ce
from schemas import ExtractionResult, Citation


def test_extractor_short_circuits_on_empty(monkeypatch):
    called = {"n": 0}
    monkeypatch.setattr(ce, "call_structured", lambda *a, **k: called.__setitem__("n", called["n"] + 1))
    out = ce.extract("")
    assert isinstance(out, ExtractionResult)
    assert called["n"] == 0  # no LLM call on empty input


def test_extractor_returns_model(monkeypatch):
    canned = ExtractionResult(citations=[Citation(
        id="c1", case_name="Privette v. Superior Court", reporter_cite="5 Cal.4th 689",
        pincite="702", jurisdiction="CA", proposition="hirer not liable", raw_text="...",
    )])
    monkeypatch.setattr(ce, "call_structured", lambda *a, **k: canned)
    out = ce.extract("some motion text")
    assert out.citations[0].case_name.startswith("Privette")


import agents.authority_verifier as av
from schemas import CitationVerdicts, CitationFinding, Citation as Cit


def test_verifier_short_circuits_on_empty(monkeypatch):
    called = {"n": 0}
    monkeypatch.setattr(av, "call_structured", lambda *a, **k: called.__setitem__("n", called["n"] + 1))
    out = av.verify([])
    assert isinstance(out, CitationVerdicts) and out.findings == []
    assert called["n"] == 0


def test_verifier_returns_model(monkeypatch):
    canned = CitationVerdicts(findings=[CitationFinding(
        citation_id="c1", case_name="Privette v. Superior Court", verdict="overstates",
        explanation="...", confidence=0.8, confidence_reasoning="...", severity="high",
    )])
    monkeypatch.setattr(av, "call_structured", lambda *a, **k: canned)
    out = av.verify([Cit(id="c1", case_name="Privette v. Superior Court",
                         proposition="hirer never liable", raw_text="...")])
    assert out.findings[0].verdict == "overstates"


import agents.quote_checker as qc
from schemas import QuoteVerdicts, QuoteFinding, Quote as Q


def test_quote_checker_short_circuits_on_empty(monkeypatch):
    called = {"n": 0}
    monkeypatch.setattr(qc, "call_structured", lambda *a, **k: called.__setitem__("n", called["n"] + 1))
    out = qc.check([])
    assert isinstance(out, QuoteVerdicts) and out.findings == []
    assert called["n"] == 0


def test_quote_checker_returns_model(monkeypatch):
    canned = QuoteVerdicts(findings=[QuoteFinding(
        quote_id="q1", quoted_text="A hirer is never liable", verdict="overstated",
        explanation="...", confidence=0.7, confidence_reasoning="...", severity="high",
    )])
    monkeypatch.setattr(qc, "call_structured", lambda *a, **k: canned)
    out = qc.check([Q(id="q1", quoted_text="A hirer is never liable",
                      attributed_to="Privette at 702")])
    assert out.findings[0].verdict == "overstated"


import agents.cross_doc_consistency as cd
from schemas import FactFindings, FactFinding, Evidence


def test_cross_doc_short_circuits_without_motion(monkeypatch):
    called = {"n": 0}
    monkeypatch.setattr(cd, "call_structured", lambda *a, **k: called.__setitem__("n", called["n"] + 1))
    out = cd.check({})  # no motion document present
    assert isinstance(out, FactFindings) and out.findings == []
    assert called["n"] == 0


def test_cross_doc_returns_model(monkeypatch):
    canned = FactFindings(findings=[FactFinding(
        claim="incident occurred March 14, 2021", status="contradicted",
        evidence=[Evidence(doc="police_report", excerpt="Date of Incident: March 12, 2021")],
        explanation="...", confidence=0.95, confidence_reasoning="...", severity="high",
    )])
    monkeypatch.setattr(cd, "call_structured", lambda *a, **k: canned)
    out = cd.check({"motion_for_summary_judgment": "March 14", "police_report": "March 12"})
    assert out.findings[0].status == "contradicted"


import agents.judicial_memo as jm
from schemas import Memo


def test_memo_returns_string(monkeypatch):
    monkeypatch.setattr(jm, "call_structured", lambda *a, **k: Memo(memo="The motion overstates Privette."))
    out = jm.synthesize(citations=[], quotes=[], facts=[])
    assert isinstance(out, str)
    assert "Privette" in out
