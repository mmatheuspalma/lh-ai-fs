# BS Detector

Legal briefs lie. Not always intentionally — but they do. They cite cases that don't say what they claim. They quote authority with words quietly removed. They state facts that contradict the documents sitting right next to them.

Your task: build an AI pipeline that catches it.

# Screenshots

<img width="810" height="526" alt="image" src="https://github.com/user-attachments/assets/cee96497-0658-4aa7-90c4-5bbca7000cbc" />


## Setup

### Docker (recommended)

```bash
cp .env.example .env      # Add your OpenAI API key
docker compose up --build
```

The API runs at `http://localhost:8002`. The UI runs at `http://localhost:5175`.

Both services hot-reload — edit files on your host and changes appear automatically.

### Manual Setup

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Add your OpenAI API key
uvicorn main:app --reload --port 8002
```

The API runs at `http://localhost:8002`.

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI runs at `http://localhost:5175`.

## The Task

Inside `backend/documents/` you'll find a small case file: a Motion for Summary Judgment in a personal injury lawsuit (*Rivera v. Harmon Construction Group*), along with a police report, medical records, and a witness statement.

Build a multi-agent pipeline that analyzes these documents and produces a structured verification report. Your pipeline should:

**Core (Tier 1)**
- Extract all citations from the Motion for Summary Judgment
- For each citation, assess whether the cited authority actually supports the proposition as stated
- Flag direct quotes for accuracy
- Produce structured output (JSON) — not a wall of prose

**Expected (Tier 2)**
- Build an eval harness that measures your pipeline's output quality. It must be runnable via a single command (e.g., `python run_evals.py`). At minimum, measure precision (avoiding false flags), recall (catching known flaws), and hallucination rate (not fabricating findings). You choose the approach — there's no prescribed framework or tooling.
- Cross-document consistency check: compare facts stated in the MSJ against the police report, medical records, and witness statement
- Express uncertainty appropriately — "could not verify" rather than fabricating a finding
- Pass structured data between agents, not raw text blobs

**Stretch (Tier 3)**
- At least 4 well-defined agents with distinct, non-overlapping roles
- A confidence scoring layer: each flag rated by how certain the pipeline is, with reasoning
- A judicial memo agent: synthesizes the top findings into a one-paragraph summary written for a judge
- Agent orchestration that handles failures gracefully
- A UI that displays the report in a structured, readable way — not just raw JSON
- A reflection document explaining the tradeoffs you made and what you'd do differently

## Deliverables

1. A working `POST /analyze` endpoint that returns a structured verification report
2. Agent code with clear, named agents and explicit prompts
3. A runnable eval suite with instructions in your README on how to run it
4. A brief reflection (in the repo or as a separate file) on your design decisions and tradeoffs

## Time

6 hours. This is intentionally scoped beyond what most candidates will finish. Where you invest your time matters more than finishing everything. A well-tested pipeline that catches 3 flaws is stronger than an untested one that attempts 10.

## Evals

We run your eval suite as part of our review. Document how to run it in your README. We care more about thoughtful metric design than perfect scores — an eval that honestly reports 60% recall tells us more than one that reports 100% on cherry-picked cases.

## AI Usage

Use everything. That's the job. We want to see how you use it, not whether you do.

## Evaluation

We are evaluating:

1. How you decompose the problem into agents
2. How precisely you write prompts
3. The quality of your eval approach — do you measure what matters?
4. How far you get through the spec
5. How honest your reflection is

Not lines of code.

---

## How it works (this implementation)

`POST /analyze` runs a 5-agent pipeline over the documents in `backend/documents/`,
passing typed Pydantic models (not raw text) between agents:

1. **CitationExtractor** — pulls every citation and direct quote from the MSJ.
2. **AuthorityVerifier** — judges whether each citation supports its proposition
   (verdicts: `supports` / `overstates` / `misattributed` / `wrong_jurisdiction` /
   `likely_fabricated` / `could_not_verify`).
3. **QuoteChecker** — judges whether each direct quote is `accurate` / `altered` /
   `overstated` / `unverifiable`.
4. **CrossDocConsistency** — compares MSJ factual claims against the police report,
   medical records, and witness statement (`corroborated` / `contradicted` /
   `unverifiable`).
5. **JudicialMemo** — synthesizes the top findings into a one-paragraph memo for a judge.

Stage 2 (agents 2–4) runs concurrently. Every finding carries a confidence score with
reasoning and a severity. Agent failures degrade gracefully — `/analyze` always returns
a report with a `pipeline_status` block rather than erroring.

Agent code: `backend/agents/`. Orchestration: `backend/pipeline.py`. Data contracts:
`backend/schemas.py`.

## Running the evals

```bash
cd backend
source venv/bin/activate        # or your venv
python run_evals.py
```

This runs the live pipeline once against the case file and scores it against a
hand-labeled gold set of the planted flaws (`backend/evals/gold.py`), reporting:

- **Recall** — known flaws caught
- **Precision** — flags that are real, not false alarms (negative controls count against)
- **Hallucination rate** — findings referencing things absent from the source, or
  flagging known-true facts

Matching is deterministic on structured keys — no LLM grades the LLM.

**Observed across live runs (gpt-4o, temperature 0):**

| Metric | Value |
|---|---|
| Recall | 75–87.5% (6–7 of 8 gold flaws) |
| Precision | 100% |
| Hallucination | 0% |

Precision and hallucination are stable run-to-run. The recall variance is entirely in
the two *fabricated* cases (Whitmore, Kellerman): the model alternates between
`likely_fabricated` (a catch) and `could_not_verify` (honest uncertainty, not a catch)
because it cannot prove an obscure case is invented without a legal database. Every
real-case defect (Privette overstatement, Seabright misattribution, out-of-state
cites) and every cross-document contradiction (incident date, PPE) was caught in every
run. This abstention is by design — it protects precision at the cost of some recall.
See [REFLECTION.md](REFLECTION.md).

## Backend tests

```bash
cd backend && source venv/bin/activate && pytest -q
```

## Reflection

Design decisions, tradeoffs, and honest limitations are in [REFLECTION.md](REFLECTION.md).
