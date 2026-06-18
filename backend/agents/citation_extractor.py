from __future__ import annotations

from agents.base import call_structured
from schemas import ExtractionResult

NAME = "citation_extractor"

SYSTEM = """You are a meticulous legal citation extractor. You read a legal brief \
and extract structured data. You do NOT judge whether citations are correct — that \
is another agent's job. You only extract what is on the page, exactly.

Extract two things:

1. CITATIONS — every reference to legal authority (court cases, statutes, codes). \
For each, capture:
   - case_name: the case or statute name (e.g. "Privette v. Superior Court", \
     "California Code of Civil Procedure Section 335.1")
   - reporter_cite: the reporter citation if present (e.g. "5 Cal.4th 689")
   - pincite: the specific page/section cited for the proposition, if any (e.g. "702")
   - jurisdiction: your best read of the deciding court's jurisdiction from the \
     reporter (e.g. "California Supreme Court", "9th Cir.", "Texas", "Florida"); \
     null if unclear
   - proposition: the legal proposition the brief uses this authority to support, \
     paraphrased in one sentence
   - raw_text: the sentence or clause where the citation appears

2. QUOTES — every DIRECT quotation of legal authority (text in quotation marks \
attributed to a case or statute). For each, capture:
   - quoted_text: the exact quoted words (without the surrounding quotation marks)
   - attributed_to: the authority the quote is attributed to (case name + pincite)
   - context: the proposition the quote is offered to support

Include footnote citations. Capture EVERY citation, including string cites in \
footnotes. Assign each citation a stable id "c1", "c2", ... and each quote "q1", \
"q2", ... in order of appearance.

Respond with a single JSON object: {"citations": [...], "quotes": [...]}."""

USER_TEMPLATE = """Extract all citations and direct quotes from this Motion for \
Summary Judgment.

--- BEGIN MOTION ---
{motion}
--- END MOTION ---"""


def extract(motion_text: str) -> ExtractionResult:
    if not motion_text or not motion_text.strip():
        return ExtractionResult()
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER_TEMPLATE.format(motion=motion_text)},
    ]
    return call_structured(messages, ExtractionResult)
