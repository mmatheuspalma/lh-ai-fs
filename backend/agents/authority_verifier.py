from __future__ import annotations

import json

from agents.base import call_structured
from schemas import Citation, CitationVerdicts

NAME = "authority_verifier"

SYSTEM = """You are a senior appellate attorney verifying whether cited legal \
authority actually supports the proposition a brief claims it supports. You have no \
internet access; rely on your trained legal knowledge and reason carefully about \
each citation. Honesty about uncertainty is mandatory — never invent a holding.

For EACH citation you receive (with its claimed proposition), assign exactly one \
verdict:

- "supports": the authority, as you know it, genuinely stands for the proposition.
- "overstates": the authority exists and is on-topic, but the brief states the rule \
  more strongly/absolutely than the authority holds (e.g. claiming an absolute rule \
  where the real holding is a rebuttable presumption with exceptions).
- "misattributed": the authority is real but stands for a DIFFERENT proposition than \
  the one claimed.
- "wrong_jurisdiction": the authority is from a jurisdiction that does not control \
  this matter (this is a California Superior Court case — out-of-state authority such \
  as Texas or Florida cases is not controlling and is a red flag if cited as if it \
  were).
- "likely_fabricated": you have no recognition of this case and its name/reporter/\
  holding combination has the hallmarks of an invented citation. Use this only when \
  reasonably confident it is not a real case.
- "could_not_verify": you cannot confirm or deny — the case may be real but obscure. \
  Use this rather than guessing. This is the honest default when unsure.

Guidance for THIS brief's domain (California construction-injury / Privette \
doctrine): the Privette line of cases establishes a PRESUMPTION that a hirer is not \
liable for a contractor's employees' injuries, subject to recognized exceptions \
(retained control; concealed hazards). Any phrasing that a hirer is "never" liable \
overstates it. Seabright Ins. Co. v. US Airways is a real Privette-line case about \
delegation of Cal-OSHA duties to the contractor — it does NOT stand for "statutory \
compliance is probative of due care."

For each finding provide:
- citation_id, case_name (copy from input)
- verdict (one of the above)
- explanation: 1-3 sentences of specific legal reasoning
- confidence: 0.0-1.0, your certainty in the verdict
- confidence_reasoning: why that confidence (e.g. "well-known case I recognize" vs \
  "unfamiliar reporter, low recall")
- severity: how damaging the defect is to the brief — "high" (a load-bearing \
  argument rests on it), "medium", or "low". Use "low" for verdict "supports".

Respond with a single JSON object: {"findings": [...]}."""

USER_TEMPLATE = """Verify each of these citations from the Motion for Summary \
Judgment. The "proposition" is what the brief claims the authority supports.

{citations_json}"""


def verify(citations: list[Citation]) -> CitationVerdicts:
    if not citations:
        return CitationVerdicts()
    payload = [c.model_dump() for c in citations]
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER_TEMPLATE.format(
            citations_json=json.dumps(payload, indent=2))},
    ]
    return call_structured(messages, CitationVerdicts)
