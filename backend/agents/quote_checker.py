from __future__ import annotations

import json

from agents.base import call_structured
from schemas import Quote, QuoteVerdicts

NAME = "quote_checker"

SYSTEM = """You are a legal quotation auditor. A brief has quoted legal authority \
directly. Your job is to judge whether each quotation faithfully represents what the \
cited authority actually says. You have no internet; rely on trained knowledge and \
careful reasoning. Be honest about uncertainty.

For EACH quote (with its attributed source) assign one verdict:

- "accurate": the quotation faithfully reflects the authority's actual language and \
  meaning, as best you know it.
- "altered": words appear to have been changed, omitted, or inserted in a way that \
  changes the meaning (e.g. a qualifier silently dropped, a word swapped).
- "overstated": the quote frames the holding more absolutely or broadly than the \
  authority actually supports (e.g. inserting "never"/"always", or quoting language \
  that asserts an absolute rule where the real rule is qualified).
- "unverifiable": you cannot confirm the authority's actual wording. Use this rather \
  than guessing.

Domain note: Privette v. Superior Court did NOT hold that a hirer is "never" liable; \
it established a rebuttable presumption with recognized exceptions. A quote attributed \
to Privette asserting a hirer is "never" liable is overstated/altered.

For each finding provide: quote_id, quoted_text (copy from input), verdict, \
explanation (1-3 sentences), confidence (0.0-1.0), confidence_reasoning, severity \
("high"/"medium"/"low"; "low" for "accurate").

Respond with a single JSON object: {"findings": [...]}."""

USER_TEMPLATE = """Audit each of these direct quotes taken from the brief.

{quotes_json}"""


def check(quotes: list[Quote]) -> QuoteVerdicts:
    if not quotes:
        return QuoteVerdicts()
    payload = [q.model_dump() for q in quotes]
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER_TEMPLATE.format(
            quotes_json=json.dumps(payload, indent=2))},
    ]
    return call_structured(messages, QuoteVerdicts)
