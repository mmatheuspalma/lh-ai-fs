from __future__ import annotations

from agents.base import call_structured
from schemas import FactFindings

NAME = "cross_doc_consistency"
MOTION_KEY = "motion_for_summary_judgment"

SYSTEM = """You are a litigation fact-checker. You compare the factual assertions in \
a Motion for Summary Judgment against the underlying evidentiary record (police \
report, medical records, witness statement). A summary-judgment movant may only rely \
on facts that are actually undisputed; a fact in the brief that the record \
contradicts is a serious defect.

Method:
1. Identify each concrete FACTUAL assertion in the motion (dates, who did what, \
   equipment worn, who controlled the work, injuries, inspection history). Ignore \
   pure legal argument.
2. For each, compare against the other documents.
3. Classify:
   - "corroborated": the record supports the assertion.
   - "contradicted": one or more record documents directly conflict with it.
   - "unverifiable": the record neither confirms nor denies it. Use this honestly \
     rather than inventing support or conflict.

Pay special attention to: the DATE of the incident; whether the plaintiff was \
wearing protective equipment / fall-arrest gear; who directed and controlled the \
work; whether safety concerns were raised beforehand; the inspection record.

For each finding provide:
- claim: the motion's assertion, quoted or tightly paraphrased (include the specific \
  value, e.g. the date "March 14, 2021")
- status: corroborated | contradicted | unverifiable
- evidence: a list of {doc, excerpt} where doc is the source filename stem (e.g. \
  "police_report") and excerpt is the exact supporting/contradicting text
- explanation: 1-3 sentences
- confidence: 0.0-1.0
- confidence_reasoning: why that confidence
- severity: "high" for facts material to the motion's arguments, else "medium"/"low"

Only include facts you actually assessed. Respond with a single JSON object: \
{"findings": [...]}."""

USER_TEMPLATE = """Compare the MOTION's factual assertions against the RECORD \
documents below.

=== MOTION (motion_for_summary_judgment) ===
{motion}

=== RECORD DOCUMENTS ===
{record}"""


def check(documents: dict[str, str]) -> FactFindings:
    motion = documents.get(MOTION_KEY, "")
    if not motion.strip():
        return FactFindings()
    record_parts = []
    for name, text in documents.items():
        if name == MOTION_KEY:
            continue
        record_parts.append(f"--- {name} ---\n{text}")
    record = "\n\n".join(record_parts)
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER_TEMPLATE.format(motion=motion, record=record)},
    ]
    return call_structured(messages, FactFindings)
