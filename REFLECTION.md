# Reflection

## What I built

A 5-agent pipeline behind `POST /analyze`:

**CitationExtractor → (AuthorityVerifier ‖ QuoteChecker ‖ CrossDocConsistency) → JudicialMemo**

Stage 1 extracts; stage 2 runs three independent verifiers concurrently; stage 3
synthesizes a one-paragraph memo for the judge. Agents communicate via typed Pydantic
models, never raw text. Plus a deterministic eval harness (`run_evals.py`) and a
structured React UI.

## Measured results (live runs, gpt-4o, temperature 0)

| Metric | Value (across runs) |
|---|---|
| Recall | **75–87.5%** (6–7 of 8 gold flaws) |
| Precision | **100%** (0 false flags, every run) |
| Hallucination rate | **0%** (every run) |

Per-category: quotes 1/1 and cross-document facts 2/2 in every run; citations 3–4/5.

The variance is the most interesting result, and I'm reporting it rather than the best
single run. **Precision and hallucination never moved** — the pipeline raised zero false
flags and invented nothing. **All recall variance is in the two fabricated cases**
(*Whitmore v. Delgado Scaffolding* and *Kellerman v. Pacific Coast Construction*): the
model alternates between `likely_fabricated` (scored as a catch) and `could_not_verify`
(confidence ~0.30, honest uncertainty, not a catch) because it cannot prove an obscure
case is invented without a legal database. Every famous-real-case defect and every
cross-document contradiction was caught in every run.

This is the pipeline behaving **exactly as designed**: when unsure, it abstains rather
than fabricating a confident "fabricated" verdict — protecting precision at the cost of
some recall. I deliberately did **not** loosen the eval matchers to convert these
abstentions into catches; an honest 75–87.5% that surfaces this behavior is more
informative than a gamed 100%.

## Key design decisions

- **Decomposition by failure mode, not by document.** The three ways a brief lies —
  unsupported citation, altered quote, contradicted fact — map to three independent
  verifier agents with non-overlapping prompts. Extraction is split from judgment so
  the judging agents receive clean structured input and can run in parallel.
- **Confidence as a first-class schema field, not a separate agent.** Every finding
  carries `confidence` + `confidence_reasoning` + `severity`. The memo ranks on
  severity × confidence. Cheaper and more honest than a bolt-on calibration agent.
- **Uncertainty is a verdict, not a flag.** `could_not_verify` / `unverifiable` are
  explicit verdicts that are excluded from the flag set, so expressing uncertainty
  neither inflates recall nor counts against precision. This is the only intellectually
  honest design absent a real case-law database.
- **Deterministic eval matching — no LLM judging the LLM.** Scores come from
  structured-key matchers against a hand-labeled gold set plus negative controls, so
  the eval can't hallucinate its own success and is reproducible at temperature 0.
- **Graceful degradation over hard failure.** Stage-2 agents are independently wrapped;
  a single agent failure yields a partial report with explicit `pipeline_status`, never
  a 500. The endpoint and the eval both surface degradation honestly.

## Tradeoffs

- **Model knowledge vs. ground truth.** Citation verification relies on the model's
  trained legal knowledge. It correctly recognized the famous real cases (*Privette*,
  *Seabright*) and their actual holdings, but can only say `could_not_verify` for
  obscure ones. A production system would call a real corpus (Westlaw / CourtListener).
- **Fact hallucination detection is weaker than citation/quote.** Cross-document claims
  are paraphrased, so the "referent appears in source" hallucination check is only
  applied to citations and quotes; facts rely on negative-control matching. This
  under-detects fact hallucinations — a conservative, disclosed bias.
- **Eval matchers can undercount recall.** A correct finding phrased unexpectedly may
  not match its gold predicate. I biased toward conservative matchers, so reported
  recall is a floor, not a ceiling.
- **Run-to-run drift.** Even at temperature 0, flag counts vary slightly between runs
  (I observed 7–8 flags across runs). The harness reports a single run and says so.

## What I'd do differently with more time

- Add a real citation-existence check via CourtListener's free API — this would let the
  pipeline confidently distinguish "fabricated" from "obscure but real."
- Add an adversarial second-pass verifier that tries to *refute* each flag (majority
  vote) to push precision even higher and stress-test borderline findings.
- Expand the gold set: more negative controls, graded partial-credit matching, and a
  second adversarial document with different planted flaws to guard against overfitting
  the prompts to this one case file.
- Cache agent outputs by document hash so the eval can run offline and cheaply in CI.
- Stream per-agent progress to the UI instead of one blocking request.

## Honest limitations

This pipeline catches the *kinds* of lies present in this specific case file well. It
has been validated against exactly one document set, so the prompts are inevitably
somewhat tuned to it. The eval numbers above are real and reproducible, but they
measure performance on a single brief — not a guarantee of generalization.
