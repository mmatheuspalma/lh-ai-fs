from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Severity = Literal["high", "medium", "low"]


class Citation(BaseModel):
    id: str
    case_name: str
    reporter_cite: Optional[str] = None
    pincite: Optional[str] = None
    jurisdiction: Optional[str] = None
    proposition: str
    raw_text: str


class Quote(BaseModel):
    id: str
    quoted_text: str
    attributed_to: str
    context: str = ""


class ExtractionResult(BaseModel):
    citations: list[Citation] = Field(default_factory=list)
    quotes: list[Quote] = Field(default_factory=list)


CitationVerdict = Literal[
    "supports", "overstates", "misattributed",
    "likely_fabricated", "wrong_jurisdiction", "could_not_verify",
]


class CitationFinding(BaseModel):
    citation_id: str
    case_name: str
    verdict: CitationVerdict
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_reasoning: str
    severity: Severity


class CitationVerdicts(BaseModel):
    findings: list[CitationFinding] = Field(default_factory=list)


QuoteVerdict = Literal["accurate", "altered", "overstated", "unverifiable"]


class QuoteFinding(BaseModel):
    quote_id: str
    quoted_text: str
    verdict: QuoteVerdict
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_reasoning: str
    severity: Severity


class QuoteVerdicts(BaseModel):
    findings: list[QuoteFinding] = Field(default_factory=list)


FactStatus = Literal["corroborated", "contradicted", "unverifiable"]


class Evidence(BaseModel):
    doc: str
    excerpt: str


class FactFinding(BaseModel):
    claim: str
    status: FactStatus
    evidence: list[Evidence] = Field(default_factory=list)
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_reasoning: str
    severity: Severity


class FactFindings(BaseModel):
    findings: list[FactFinding] = Field(default_factory=list)


class Memo(BaseModel):
    memo: str


class Summary(BaseModel):
    total_flags: int
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)


class PipelineStatus(BaseModel):
    agents: dict[str, str] = Field(default_factory=dict)  # name -> "ok" | "failed"
    errors: list[str] = Field(default_factory=list)


class VerificationReport(BaseModel):
    case: str
    generated_at: str
    summary: Summary
    citations: list[CitationFinding] = Field(default_factory=list)
    quotes: list[QuoteFinding] = Field(default_factory=list)
    cross_document: list[FactFinding] = Field(default_factory=list)
    judicial_memo: str
    pipeline_status: PipelineStatus
