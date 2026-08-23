# conventions.md — rules that keep the prototype honest

## Code style

- Python: PEP8, type hints on function signatures, a one-line docstring on every public
  function stating which `architecture.md` §3 component it belongs to.
- No premature abstraction. This is a scoped prototype, not a framework — a straight
  function is better than a plugin system nobody asked for.
- Every module that produces a number shown anywhere (README, demo, frontend) must be
  runnable standalone and must print that number to stdout, so it can be independently
  verified by re-running it.

## Discovery-engine integrity rules (non-negotiable)

A "discovered" rule is disqualified — and must not be presented as a result anywhere —
if any of these are true:

- It was found by iterating until a predetermined answer appeared, instead of scoring
  all candidates and picking the best by the stated criteria.
- It's reported using only the train split, without independent held-out validation.
- The minimum support threshold was lowered specifically to make a particular result
  qualify.
- The significance test was dropped, weakened, or replaced with an eyeballed
  judgment call.

If a change to `discover.py` would violate any of the above, don't make it — flag it
in `tasks.md`-style output instead ("this would require lowering the support
threshold to X, which conventions.md disallows — confirm before proceeding").

## No black-box models in the discovery path

Rule discovery must stay interpretable: statistical rule mining, shallow decision
trees with extracted leaf rules, or equivalent. Do not swap in a gradient-boosted
model, a neural net, or any method whose output can't be read as a small set of
human-checkable conditions. Interpretability is part of the pitch (see the research
paper §7.3) — an uninterpretable "discovery" step undermines the whole product claim.

## LLM usage boundary (non-negotiable)

- An LLM call may only ever write to a `rationale` (or equivalently named,
  explicitly advisory) text field.
- An LLM call must never populate, modify, or influence the `conditions`, `action`, or
  `requires_human` fields of a policy object, directly or indirectly (e.g., don't have
  the LLM "double check" a decision and let its answer silently override the
  deterministic evaluator).
- Any LLM output used in the product must be reviewable by a human before it affects
  anything — if there's no human-review step between an LLM call and an effect, that's
  a violation regardless of how the code is structured.

## Policy object conventions

- ID format: `POLICY-<domain-id>-v<N>`, e.g. `POLICY-042-v2`. Domain id `042` is
  already in use for the insurance claims workflow — keep it unless a real second
  workflow is added in Phase 2.
- Every version is kept as its own file under `/policy/versions/` — never overwrite a
  previous version in place. `supersedes` points to the prior version's `policy_id`.
- The `evidence` object is mandatory on any policy created via discovery (not required
  for the original hand-written `v1` baseline policy, which predates discovery and
  should be marked `"evidence": null` or omitted, not fabricated).
- Field names in `conditions[].field` must match the exact column names in
  `insurance_claims.csv` (see `prerequisites.md`) — no renaming/aliasing layer.

## Testing conventions

- Any new policy version must pass through `regression_test.py` (re-evaluate both the
  old and new policy against the same held-out historical slice) before it can be
  marked `active`. There is no code path that activates a policy without this step.
- Unit tests for the deterministic runtime evaluator should include at least one case
  per condition operator in use, plus one case that should clearly route
  `HUMAN_REVIEW` and one that should clearly route `AUTO_PROCESS` under the current
  active policy.

## Reporting/README conventions

- Every metric that appears in the README or the demo script must include a one-line
  note of which script produced it and (if relevant) the seed used, so it's
  independently reproducible by someone reading the repo.
- Never state a competitive claim ("nobody else does X") in the README without it
  being explicitly sourced from the research paper's competitive-landscape section —
  and even then, phrase it conservatively (the research paper's own Appendix A already
  flags this as unverified-at-authorship-time).

## Git/commit conventions (for the public GitHub repo deliverable)

- Commit messages describe what changed and which architecture component it touches,
  e.g. `runtime: add deterministic evaluator for policy conditions`.
- Keep `/data/insurance_claims.csv` and generated policy version files committed (not
  gitignored) — a judge cloning the repo should be able to run the demo without
  regenerating anything, though regeneration should also work if they choose to.
