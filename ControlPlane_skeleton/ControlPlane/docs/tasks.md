# tasks.md — build order, in order, with a definition of done for each

Read `philosophy.md`, `architecture.md`, `prerequisites.md`, and `conventions.md`
before starting. This file tells you *what to build and in what order*; those files
tell you *how* and *why*. If they conflict, this file wins on sequencing, they win on
everything else.

## Phase 1 — MVP (required, this is the whole prototype deliverable)

Work through these in order. Each has a definition of done. Do not start a later task
before the previous one's definition of done is met.

### 1. Repo scaffold
Set up the folder structure from `architecture.md` §4.
**Done when:** the tree exists, `simulate.py`, `discover.py`, `insurance_claims.csv`,
and `policy_v2.json` are placed per `prerequisites.md`, and both scripts run
successfully producing the expected output numbers listed in `prerequisites.md`.

### 2. Policy schema + versioning
Implement `/policy/schema.py` (a typed representation matching `architecture.md` §6)
and `/policy/lifecycle.py` (draft → proposed → approved/rejected → versioned state
machine). Write the hand-authored baseline as `POLICY-042-v1.json`
(`claim_amount < 50000 → AUTO_PROCESS`, else `HUMAN_REVIEW`, matching what
`simulate.py` already encodes as the "current dumb policy").
**Done when:** `POLICY-042-v1.json` exists, the schema validates both v1 and the
already-generated `policy_v2.json` example, and the lifecycle state machine has a unit
test for every transition (including the illegal ones, e.g. cannot go from `draft`
straight to `active` without `approved`).

### 3. Deterministic runtime evaluator
Implement `/runtime/evaluator.py`: given a claim (dict/object with the fields from
`insurance_claims.csv`) and the currently active policy version, evaluate the
conditions and return a decision (`AUTO_PROCESS` / `HUMAN_REVIEW`) plus which policy
version produced it. No model call anywhere in this file.
**Done when:** running the evaluator against a held-out slice of
`insurance_claims.csv` under `POLICY-042-v1` reproduces the same routing that
`simulate.py`'s `ai_initial_decision` column already contains (this is your
correctness check — the evaluator must agree with the ground-truth generation logic).

### 4. Regression test harness
Implement `/runtime/regression_test.py`: given an old policy version and a proposed
new one, evaluate both against the same held-out historical data and report the
before/after routing distribution, before/after estimated success rate, and
before/after estimated processing cost (using the `processing_cost` column already in
the dataset as the cost proxy).
**Done when:** running it with `POLICY-042-v1` vs. the already-generated
`policy_v2.json` reproduces numbers consistent with what `discover.py` already printed
(held-out success rate ≈ 0.701 for the newly-auto-processed subgroup vs. ≈ 0.438
zone baseline).

### 5. Rationale generator (LLM, explanation only)
Implement `/engine/rationale.py`: takes a discovered rule's evidence dict (the same
shape as `policy_v2.json`'s `evidence` object) and produces a short human-readable
rationale string plus a plain-English diff description ("previously claims like this
required human review; the data shows X, so this proposes auto-processing them
instead"). Writes only to the `rationale` field.
**Done when:** running it against `policy_v2.json`'s evidence object produces a
rationale string that a non-technical reviewer could read and understand why the
change is being proposed, and it is demonstrably not influencing `conditions` or
`action` (e.g., a test that the LLM call happens *after* the rule and evidence are
already fixed, not before).

### 6. Minimal API
Implement `/api/main.py` with the four endpoints from `architecture.md` §7.
**Done when:** a judge (or you) can, via HTTP calls or a simple script, walk the full
loop: `GET /policy/current` → `POST /policy/discover` → review the proposal → `POST
/policy/{id}/approve` → see regression test results → `POST /runtime/evaluate` with a
new claim and see the decision reflect the newly active policy.

### 7. Demo interface
A CLI walkthrough script or a minimal frontend (your choice — a working CLI beats a
half-built UI) that performs the 8-step demo sequence: show current policy → replay
historical data → run discovery live → show evidence → show the diff/rationale →
accept the proposal → show regression-test impact → evaluate a new unseen case and
show the decision flip.
**Done when:** the whole sequence runs start to finish without manual data-fudging,
using only numbers the code actually produced in that run.

### 8. README.md (repo root, separate from `/docs`)
Write the actual Round 2 deliverable README: implementation approach, solution
architecture (can summarize `architecture.md`), dependencies, and execution
instructions (how to install, how to run the demo end to end from a clean clone).
**Done when:** someone with no prior context can clone the repo and reproduce the demo
sequence from the README alone.

### 9. Demo video
Not a coding task, but listed here for sequencing: record the video only after step 7
works reliably twice in a row without intervention.

## Phase 2 — explicitly deferred, do not build without instruction

These correspond to `architecture.md` §8's "new mechanism" column. They are real,
documented ideas from the design process, not rejected ones — but building any of
them before Phase 1 is fully done is the exact scope-creep failure this project has
already identified and walked back from twice. Do not start these unless the person
explicitly asks for them by name:

- Use Case Profiles (multi-workflow risk/latency configuration)
- Multi-label risk vectors (overlapping bias/hallucination/privacy scoring)
- Verifiable/unverifiable claim routing with outcome-deferred validation
- Risk-state accumulation across a multi-turn interaction ("risk debt")
- Counterfactual/shadow execution before a consequential agent action
- Taint tracking for privacy scoring

## Stop and ask — don't improvise past these

Stop and flag rather than proceeding if:

- A task seems to require adding a detector, dashboard panel, or feature not listed in
  Phase 1 above.
- You're about to let an LLM's output influence a policy `conditions` or `action`
  field, directly or indirectly.
- You're about to report a metric that didn't come from actually running code in this
  repo.
- You're about to lower a support threshold, drop the significance test, or skip
  held-out validation to make a result look better.
- A task's acceptance criteria can't be met without changing something listed as
  Frozen in `philosophy.md`.

In all of these cases: implement the smallest honest version you can, note the
limitation in a code comment or commit message, and describe what you skipped and why
rather than silently working around it.
