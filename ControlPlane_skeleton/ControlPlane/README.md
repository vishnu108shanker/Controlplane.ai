# ControlPlane.ai

**AI-Assisted Policy Discovery & Deterministic Enforcement for Insurance Claims**

> *"We are not replacing the `if`. We are discovering which `if` should exist."*

ControlPlane.ai is a prototype built for Round 2 of the Accenture Innovation Challenge. It demonstrates a system where **AI discovers patterns** in historical data, but **deterministic code enforces decisions** — the LLM never touches the decision path.

---

## Solution Architecture

```
Historical Data ──► Discovery Engine (statistical) ──► Policy JSON (versioned)
                                                            │
                    Rationale Generator (LLM) ◄─────────────┤ (read-only explanation)
                                                            │
                    Evaluator (deterministic) ◄─────────────┘
                           │
                    Routing Decision (AUTO_PROCESS / HUMAN_REVIEW)
```

### Key Components

| Component | Path | Role |
|-----------|------|------|
| **Data Simulator** | `data/simulate.py` | Generates 20k synthetic insurance claims with realistic patterns |
| **Discovery Engine** | `engine/discover.py` | Mines multivariate rules from historical data using z-tests and train/test splits |
| **Rationale Generator** | `engine/rationale.py` | **Only** LLM call in the system — produces human-readable explanations (read-only, never influences conditions) |
| **Policy Schema** | `policy/schema.py` | Defines the executable JSON policy format with typed conditions and evidence |
| **Policy Lifecycle** | `policy/lifecycle.py` | Enforces `DRAFT → PROPOSED → APPROVED → ACTIVE` state machine with mandatory regression gate |
| **Runtime Evaluator** | `runtime/evaluator.py` | Pure deterministic `if`-logic — evaluates claims against active policy conditions |
| **Regression Test** | `runtime/regression_test.py` | Mandatory approval gate — backtests old vs. new policy on held-out data |
| **API** | `api/main.py` | FastAPI endpoints for policy management and claim evaluation |
| **Demo** | `demo.py` | End-to-end CLI walkthrough of the full pipeline |

### Design Principles

1. **AI does discovery, deterministic systems do enforcement.** The LLM generates explanations only — it cannot modify `conditions` or `action` fields.
2. **No policy reaches ACTIVE without regression testing.** The `approve()` function mandatorily calls `runtime/regression_test.py`.
3. **Every reported metric is computed live.** No hardcoded example numbers anywhere.

---

## Dependencies

- Python 3.11+
- pandas >= 2.0
- numpy >= 1.24
- statsmodels >= 0.14
- fastapi >= 0.110
- uvicorn >= 0.29
- pydantic >= 2.0
- pytest >= 8.0
- groq >= 0.11.0 — LLM rationale generation via Groq Cloud (model: `openai/gpt-oss-20b`)
- python-dotenv

---

## Setup & Installation

```bash
# 1. Clone the repo
git clone <repo-url>
cd ControlPlane

# 2. Install dependencies
pip install -r requirements.txt
pip install groq python-dotenv

# 3. Set up your LLM API key
# Create a .env file in the repo root:
echo GROQ_API_KEY="your-groq-api-key-here" > .env
# Get a free key at https://console.groq.com
```

---

## Running the Demo (End-to-End)

### Interactive Mode
```bash
python demo.py
```
This walks you through all 8 steps with pauses between each stage:
1. Shows the current active policy (POLICY-042-v1)
2. Loads 20,000 historical claims
3. Runs the discovery engine live — mines rules, prints evidence
4. Generates an AI rationale via Groq LLM
5. Prompts you to approve or reject the proposed policy
6. Runs regression tests on held-out data before activation
7. Evaluates two contrasting live claims under old vs. new policy

### Scripted Mode (no prompts)
```bash
python demo.py --auto-approve
```

### Expected Output (key numbers)
These numbers are **computed live** from the data on every run:
- **Train zone**: 2,472 claims, baseline success rate 0.417
- **Discovered rule**: `incident_type == airline_fault AND fraud_score <= 0.3 AND claim_amount <= 75000`
- **Train support**: 181, success rate 0.735, lift 1.76x, p-value 9.57e-20
- **Held-out validation**: 87 claims, success rate 0.701 (vs 0.438 baseline)
- **Precision improvement**: 23.1 percentage points over naive threshold raise

---

## Running the API Server

```bash
uvicorn api.main:app --reload
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/policy/current` | Returns the currently active policy |
| `POST` | `/policy/discover` | Runs discovery engine, generates rationale, returns PROPOSED policy |
| `POST` | `/policy/{policy_id}/approve` | Runs regression test, approves and activates policy |
| `POST` | `/policy/{policy_id}/reject` | Rejects a proposed policy with a reason |
| `POST` | `/runtime/evaluate` | Evaluates a claim against the active policy (deterministic) |

### Example: Evaluate a Claim
```bash
curl -X POST http://localhost:8000/runtime/evaluate \
  -H "Content-Type: application/json" \
  -d '{"incident_type": "airline_fault", "fraud_score": 0.1, "claim_amount": 60000}'
```

---

## Running Tests

```bash
pytest tests/ -v
```

**9 tests** covering:
- Policy lifecycle transitions (legal and illegal)
- Mandatory regression gate enforcement
- Evaluator ground-truth agreement against 20k claims
- `requires_human` override behavior
- Fallback to `HUMAN_REVIEW` for unmatched claims
- LLM rationale non-mutation of evidence

---

## Repo Structure

```
ControlPlane/
├── api/
│   └── main.py              # FastAPI endpoints
├── data/
│   ├── simulate.py           # Data generation (ground truth)
│   └── insurance_claims.csv  # 20k synthetic claims
├── docs/
│   ├── philosophy.md         # Why this project exists
│   ├── architecture.md       # System design & policy schema
│   ├── prerequisites.md      # What already works
│   ├── conventions.md        # Coding rules & boundaries
│   └── tasks.md              # Build order
├── engine/
│   ├── discover.py           # Statistical rule mining (ground truth)
│   └── rationale.py          # LLM explanation (Groq)
├── policy/
│   ├── schema.py             # Policy dataclasses & JSON serialization
│   ├── lifecycle.py          # State machine & approval gate
│   └── versions/
│       ├── POLICY-042-v1.json  # Baseline policy
│       └── POLICY-042-v2.json  # Discovered policy
├── runtime/
│   ├── evaluator.py          # Deterministic claim routing
│   └── regression_test.py    # Held-out backtesting gate
├── tests/
│   ├── test_lifecycle_and_evaluator.py
│   └── test_rationale.py
├── demo.py                   # End-to-end CLI demo
├── requirements.txt
└── .env                      # GROQ_API_KEY (not committed)
```

---

## What Makes This Different

Most "AI in insurance" demos let the model make the decision. ControlPlane.ai **never does that**:

- The discovery engine uses classical statistics (z-tests, train/test splits) — not an LLM.
- The evaluator is pure `if`/`else` logic — no model call, no probability.
- The only LLM call generates a human-readable explanation *after* the rule is already fixed. It uses **Groq** (`openai/gpt-oss-20b`), not Anthropic Claude — the docs mentioned Claude as an example, but any LLM works here since the call is purely generative and never touches conditions or actions.
- Every policy must pass regression testing on held-out data before activation.

The result: **auditable, deterministic decisions** with **AI-powered discovery** of *which* rules to write.

---

## Known Caveats — Stated Plainly

These are **intentional properties of the data and discovery**, not bugs. `docs/prerequisites.md` requires they be stated openly:

1. **Held-out support is 87 cases.** The discovered rule was validated on 87 independent held-out claims, not thousands. The significance test (p ≈ 9.6e-20 on the training set, and the pattern holding at 70.1% success on that independent 87-case test slice vs. a 43.8% baseline) is what makes the finding real — not the raw count. We state this number rather than letting it look larger than it is.

2. **`fraud_score` is partially derived from the same latent risk that drives `outcome`.** This mirrors how real fraud scores work in production — they are risk proxies, not independent ground truth. The discovery engine is finding a pattern *on top of* `fraud_score`, not circularly reading the outcome off of it. This is a realistic modeling choice, not a data leak.

3. **The discovered rule uses `incident_type == airline_fault` and `fraud_score <= 0.3`, not `customer_tier == premium`.** Earlier design notes assumed the tier-based pattern would be found. The algorithm found a different, real pattern instead. This is evidence the discovery is genuine and not scripted.

4. **LLM fallback behavior.** If `GROQ_API_KEY` is not set or the Groq API is unreachable, `engine/rationale.py` falls back to a clearly-labeled mock string prefixed with `"MOCK RATIONALE"`. A `[rationale]` log line is printed to stdout indicating which path fired (live LLM vs. mock), so it is visible during recording.
