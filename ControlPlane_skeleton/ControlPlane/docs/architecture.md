# architecture.md — system design the code must match

Read `philosophy.md` first. This document is the concrete shape of that philosophy.

## 1. Scope for this prototype

**Domain: insurance claims only.** No other use case gets a live implementation in the
MVP (see `tasks.md` Phase 2 for what's explicitly deferred). One workflow, done for
real, beats three workflows simulated.

## 2. The two-lane system

```
                    RUNTIME (fast path)                LEARNING (slow path)
                    ────────────────────                ─────────────────────
                    New claim arrives                    Historical claims,
                          │                               overrides, outcomes
                          ▼                                      │
                  Load current versioned                         ▼
                       policy                            Rule discovery
                          │                            (statistical/interpretable,
                          ▼                              see §5)
                Deterministic evaluation                         │
                  (plain conditionals,                            ▼
                   NOT a model call)                     Candidate policy +
                          │                                evidence stats
                          ▼                                      │
                AUTO_PROCESS / HUMAN_REVIEW                       ▼
                                                    LLM-drafted rationale + diff
                                                    (explanation only, no authority)
                                                                   │
                                                                   ▼
                                                            Human review
                                                          Approve / Edit / Reject
                                                                   │
                                                                   ▼
                                                          Regression test against
                                                          historical held-out data
                                                                   │
                                                                   ▼
                                                          New policy version
                                                                   │
                                                                   └──► feeds back into
                                                                        Runtime (fast path)
```

The two lanes are never allowed to merge into one request-time call. The runtime never
calls an LLM. The learning path never bypasses human approval to reach the runtime.

## 3. Component classification (what technology each piece is allowed to use)

| Component | Technology class | Notes |
|---|---|---|
| Claim intake / routing | Deterministic | Pure function of claim fields + current policy |
| Current-policy evaluation | Deterministic | Conditional logic over the policy JSON schema (§6) |
| Rule discovery | Statistics / interpretable rule mining | No black-box models. See `conventions.md` |
| Significance testing | Statistics (two-proportion z-test or equivalent) | A discovered rule without a significance check is not a result |
| Policy rationale / diff text | LLM (generative) | Output is a string, written to a `rationale` field only — never to `conditions` or `action` |
| Regression testing | Deterministic | Re-run the *old* and *new* policy against the same held-out historical data, diff the outcomes |
| Policy compilation | Deterministic codegen | Human-approved rule → policy JSON (§6). Mechanical, not a "creative" step |
| Runtime evaluation | Deterministic | Evaluate a new claim dict against the active policy version |

If a task doesn't clearly belong to exactly one row above, stop and ask — see
`tasks.md`.

## 4. Repo layout the code should converge on

```
/data/
    insurance_claims.csv          # reference dataset already generated — see prerequisites.md
    simulate.py                   # reference generator — see prerequisites.md before touching

/engine/
    discover.py                   # rule-mining discovery engine — see prerequisites.md
    rationale.py                  # LLM call producing human-readable proposal text (explanation only)

/policy/
    schema.py                     # pydantic/dataclass definition matching §6 below
    versions/
        POLICY-042-v1.json
        POLICY-042-v2.json        # etc — every version kept, never overwritten
    lifecycle.py                  # state machine: draft -> proposed -> approved/rejected -> versioned

/runtime/
    evaluator.py                  # loads active policy version, evaluates a claim, returns decision
    regression_test.py            # re-runs old vs new policy against held-out data

/api/
    main.py                       # FastAPI app exposing the endpoints below

/frontend/                        # optional for MVP — CLI or minimal UI is acceptable, see tasks.md

/docs/                            # this folder — do not delete or move these files
    architecture.md
    prerequisites.md
    conventions.md
    tasks.md
    philosophy.md
    ControlPlane_ai_Research_Paper.md    # added manually, reference only

README.md                         # repo root — required Round 2 deliverable, separate from /docs
```

## 5. Discovery engine contract

Input: a dataframe of historical claims with fields listed in `prerequisites.md`.
Output: a ranked list of candidate rules, each with `conditions`, `support`,
`success_rate`, `lift`, `p_value`. A rule only counts as a discovered result if it:

- meets a minimum support threshold (do not lower this to make a demo look better),
- has p < 0.01 against the same-zone baseline,
- was selected on a train split and then independently evaluated on a held-out test
  split it did not touch during discovery.

Reporting only the train-set numbers, without the held-out validation, is not allowed
anywhere — not in the API response, not in the frontend, not in the README.

## 6. Policy JSON schema (exact — match this, don't redesign it)

```json
{
  "policy_id": "POLICY-042-v2",
  "supersedes": "POLICY-042-v1",
  "conditions": [
    {"field": "incident_type", "operator": "==", "value": "airline_fault"},
    {"field": "fraud_score", "operator": "<=", "value": 0.3},
    {"field": "claim_amount", "operator": "<=", "value": 75000}
  ],
  "action": "AUTO_PROCESS",
  "requires_human": false,
  "evidence": {
    "train_support": 181,
    "train_success_rate": 0.7348,
    "train_lift": 1.764,
    "train_p_value": 9.57e-20,
    "held_out_support": 87,
    "held_out_success_rate": 0.7011,
    "held_out_baseline_success_rate": 0.4376,
    "naive_threshold_success_rate": 0.4699
  },
  "rationale": "LLM-generated explanation string — advisory only, never authoritative"
}
```

Supported `operator` values: `==`, `!=`, `<=`, `>=`, `<`, `>`, `in`. Add new operators
only if a real discovered rule needs one — don't pre-build operators speculatively.

## 7. API surface (minimum viable, expand only if a task requires it)

- `GET /policy/current` — returns the active policy version for the insurance domain.
- `POST /policy/discover` — runs the discovery engine against current historical data,
  returns a candidate proposal (not yet applied).
- `POST /policy/{id}/approve` | `/reject` — human decision on a proposal. Approving
  triggers regression testing, then versioning, then activation.
- `POST /runtime/evaluate` — takes a new claim object, returns the routing decision
  from the *currently active* policy version, deterministically.

## 8. Round 2 brief items — status in this architecture

These are documented for completeness. Do **not** implement the "new mechanism"
columns unless `tasks.md` explicitly schedules them for this build (see Phase 2).
Building them speculatively is exactly the scope-creep failure mode this project has
already identified and rejected twice.

| Brief concern | How the architecture above already answers it | New mechanism (Phase 2 only, not MVP) |
|---|---|---|
| Different use cases, different risk/latency tolerance | N/A for MVP — single domain | Use Case Profiles |
| Overlapping risk categories (bias/hallucination/privacy) | N/A for MVP — single outcome label | Multi-label risk vectors |
| No reliable real-time ground truth | Outcome-aware discovery already treats human decisions as evidence, not truth | Verifiable/unverifiable claim routing |
| Multi-turn / agentic compounding risk | Policy sits at the action boundary already (claim routing is the action) | Shadow execution / risk-state accumulation |
| Evolving regulation | Policy versioning already supports a human-authored policy change, not just a discovered one | — |
| API-only model access | Nothing in this architecture inspects model internals | — |
| Latency at scale | Fast/slow path split already keeps runtime evaluation free of any model call | — |

## 9. What "done" looks like architecturally

A judge can: see the current policy, trigger discovery against historical data, see
the evidence and the diff, click Approve, see a regression-test result, then submit a
brand-new unseen claim and watch the decision change because of the newly active
policy version. Every number on screen at every step must come from code that actually
ran, not from a hardcoded example.
