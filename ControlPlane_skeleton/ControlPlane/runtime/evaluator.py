"""
runtime/evaluator.py

Architecture component: Runtime evaluation (architecture.md §3, deterministic).

NO MODEL CALL OF ANY KIND BELONGS IN THIS FILE. Not an LLM, not a classifier, nothing
probabilistic. This module's entire job is: given a claim and the currently active
policy, evaluate plain conditional logic and return a decision. See docs/philosophy.md
"The governing engineering principle" -- this file IS that principle in code.

STATUS: stub. See docs/tasks.md task 3 for the definition of done: this evaluator,
run against data/insurance_claims.csv under POLICY-042-v1, must reproduce the same
routing already present in the dataset's `ai_initial_decision` column. That agreement
is the correctness check -- if it doesn't match, the bug is in this file, not the data.
"""

from __future__ import annotations
from dataclasses import dataclass
from policy.schema import Policy, Action
from policy.lifecycle import get_active_policy


@dataclass
class RoutingDecision:
    action: Action
    matched_policy_id: str
    claim_id: str | None = None


def evaluate(claim: dict, policy: Policy | None = None) -> RoutingDecision:
    """
    Evaluate `claim` against `policy` (or the currently active policy if None).

    TODO: implement.
    - If policy.matches(claim) is True: return policy.action.
    - If False: the claim falls through to HUMAN_REVIEW by default (see
      POLICY-042-v1.json's "note" field) -- do not leave this undefined behavior,
      make the fallback explicit in code and in a comment.
    - `policy.requires_human` on the matched policy should override action to
      HUMAN_REVIEW even if action says AUTO_PROCESS -- requires_human wins.
    """
    if policy is None:
        policy = get_active_policy()
    raise NotImplementedError


def evaluate_batch(claims: list[dict], policy: Policy | None = None) -> list[RoutingDecision]:
    """Convenience wrapper for evaluating many claims against the same policy --
    used by regression_test.py. TODO: implement in terms of evaluate() above."""
    raise NotImplementedError
