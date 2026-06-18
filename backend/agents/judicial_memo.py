from __future__ import annotations

import json

from agents.base import call_structured
from schemas import CitationFinding, FactFinding, Memo, QuoteFinding

NAME = "judicial_memo"

SYSTEM = """You are a judicial law clerk. Given a set of structured verification \
findings about a Motion for Summary Judgment, write a SINGLE paragraph (4-7 \
sentences) for the judge summarizing the most serious credibility problems with the \
motion. Be precise and neutral in tone, name the specific authorities and facts at \
issue, and lead with the most damaging findings (overstated/misattributed/fabricated \
citations and direct factual contradictions with the record). If the pipeline could \
not verify something, do not assert it as fact. Do not invent findings beyond those \
provided. Output JSON: {"memo": "..."}."""

USER_TEMPLATE = """Findings (already filtered to the most significant):

CITATION FINDINGS:
{citations}

QUOTE FINDINGS:
{quotes}

CROSS-DOCUMENT FACT FINDINGS:
{facts}

Write the one-paragraph memo for the judge."""


def _rank_key(item) -> float:
    sev = {"high": 3, "medium": 2, "low": 1}.get(getattr(item, "severity", "low"), 1)
    return sev * getattr(item, "confidence", 0.0)


def synthesize(
    citations: list[CitationFinding],
    quotes: list[QuoteFinding],
    facts: list[FactFinding],
    top_n: int = 8,
) -> str:
    # Keep only problematic findings, ranked by severity * confidence.
    cit = [c for c in citations if c.verdict != "supports"]
    qt = [q for q in quotes if q.verdict != "accurate"]
    ft = [f for f in facts if f.status == "contradicted"]
    cit = sorted(cit, key=_rank_key, reverse=True)[:top_n]
    qt = sorted(qt, key=_rank_key, reverse=True)[:top_n]
    ft = sorted(ft, key=_rank_key, reverse=True)[:top_n]

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER_TEMPLATE.format(
            citations=json.dumps([c.model_dump() for c in cit], indent=2),
            quotes=json.dumps([q.model_dump() for q in qt], indent=2),
            facts=json.dumps([f.model_dump() for f in ft], indent=2),
        )},
    ]
    return call_structured(messages, Memo).memo
