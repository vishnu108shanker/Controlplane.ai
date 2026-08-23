# prerequisites.md — environment, existing artifacts, and things to not "fix"

## Artifacts that already exist and already work — treat as ground truth

Four files were already built and validated before this repo existed. They should be
placed at `/data/simulate.py`, `/data/insurance_claims.csv`, `/engine/discover.py`,
and the resulting `/policy/versions/POLICY-042-v1.json` / `-v2.json`. **Do not
regenerate or rewrite these from a design description — copy them in as-is, then
extend.** If something about them seems wrong, flag it in a comment rather than
silently "fixing" it — see the caveats below, some apparent oddities are intentional.

- `simulate.py` — generates 20,000 synthetic insurance claims with a hidden
  multivariate pattern, a decoy confounder, and realistic noise. Seeded
  (`np.random.default_rng(42)`) for reproducibility. Running it regenerates
  `insurance_claims.csv` identically every time.
- `discover.py` — the rule-mining discovery engine. Seeded (`rng = default_rng(7)` for
  the train/test split). Running it against `insurance_claims.csv` reproduces the
  discovered rule and `policy_v2.json` exactly.
- `insurance_claims.csv` — 20,000 rows, the output of `simulate.py`.
- `policy_v2.json` — the actual discovered-and-validated policy from a real run of
  `discover.py`. This is the reference example for the schema in `architecture.md` §6.

## Known caveats — intentional, do not "fix"

- **`fraud_score` is partially derived from the same latent risk that drives
  `outcome`.** This mirrors how real fraud scores work in production (they're risk
  proxies, not independent ground truth) — it is not a data leak to patch. If this
  comes up in a demo or README, say so directly: "fraud_score is itself a modeled
  signal, and the discovery engine is finding a pattern *on top of* it, not
  circularly reading the outcome off of it."
- **The discovered rule in `policy_v2.json` uses `incident_type == airline_fault` and
  `fraud_score <= 0.3`, not `customer_tier == premium`.** Earlier design notes assumed
  the tier-based pattern would be the one found. The algorithm found a different, real
  pattern instead. This is a feature, not a bug — it's evidence the discovery is
  genuine and not scripted. Don't "correct" the discovery engine to find the tier
  pattern instead.
- **Held-out support for the discovered rule is 87 cases.** Small, but the significance
  test (p ≈ 9.6e-20 on train, and the pattern holding on an independent 87-case test
  slice) is what makes it real, not the raw count. State this number plainly in any
  demo or README rather than letting it look larger than it is.

## Environment

- **Python 3.11+**
- Core libraries: `pandas`, `numpy`, `statsmodels` (used for the two-proportion
  z-test in `discover.py`). Install with the environment's normal package manager;
  in sandboxed/managed environments this may require
  `pip install <package> --break-system-packages`.
- Optional, only if a Phase 1 task requires them: `fastapi`, `uvicorn`, `pydantic` for
  the API layer.
- No GPU, no deep learning framework, no vector database is required anywhere in this
  architecture. If a task seems to need one, stop and check `architecture.md` §3 — it
  probably means the task has drifted outside the intended component classification.

## LLM access (for the rationale/explanation step only)

- The rationale-generation step (`/engine/rationale.py`) calls an LLM (e.g. Claude via
  the Anthropic API) to turn a discovered rule's evidence dict into a short
  human-readable explanation and diff description.
- This call must be isolated to that one module. It must never be in the same code
  path as `/runtime/evaluator.py`. If you find yourself importing an LLM client inside
  the runtime evaluator, stop — that violates the architecture.
- API key should be read from an environment variable (e.g. `ANTHROPIC_API_KEY`), never
  hardcoded, and the repo's README/execution instructions should say how to set it.

## Reproducibility requirement

Any number that ends up in the README, the demo video, or on screen in the frontend
must be traceable to an actual run of the code in this repo, with the seeds above (or
newly documented seeds if the dataset is regenerated with different parameters).
Never hand-type a metric into a doc or UI string.

## Running what already exists

```bash
# from /data/
python3 simulate.py         # regenerates insurance_claims.csv deterministically

# from /engine/
python3 discover.py         # reproduces the discovered rule + writes a fresh policy JSON
```

Expected output of `discover.py` (for sanity-checking a fresh environment matches):
train support 181, train success rate ≈ 0.735, held-out support 87, held-out success
rate ≈ 0.701, naive-threshold-only success rate ≈ 0.470 on the same held-out zone.
