"""
policy/lifecycle.py

Architecture component: Policy compilation / lifecycle (architecture.md §3, deterministic).

Implements the state machine: draft -> proposed -> approved/rejected -> active/superseded.
See docs/philosophy.md -- the Approve step is a mandatory, non-bypassable gate. There is
no code path in this module that moves a policy to ACTIVE without passing through
APPROVED first.

STATUS: stub. See docs/tasks.md task 2 for the definition of done, including the
required unit test for every transition (including illegal ones).
"""

from __future__ import annotations
from policy.schema import Policy, PolicyStatus

# Legal transitions. Anything not listed here must raise.
_ALLOWED_TRANSITIONS: dict[PolicyStatus, set[PolicyStatus]] = {
    PolicyStatus.DRAFT: {PolicyStatus.PROPOSED},
    PolicyStatus.PROPOSED: {PolicyStatus.APPROVED, PolicyStatus.REJECTED},
    PolicyStatus.APPROVED: {PolicyStatus.ACTIVE},
    PolicyStatus.ACTIVE: {PolicyStatus.SUPERSEDED},
    PolicyStatus.REJECTED: set(),
    PolicyStatus.SUPERSEDED: set(),
}


class IllegalTransitionError(Exception):
    pass


def transition(policy: Policy, new_status: PolicyStatus) -> Policy:
    if new_status not in _ALLOWED_TRANSITIONS[policy.status]:
        raise IllegalTransitionError(f"Cannot transition from {policy.status} to {new_status}")
    policy.status = new_status
    return policy


def propose(draft_policy: Policy) -> Policy:
    return transition(draft_policy, PolicyStatus.PROPOSED)


MIN_SUCCESS_RATE_TOLERANCE = 0.005 # 0.5% drop allowed

def approve(proposed_policy: Policy) -> Policy:
    transition(proposed_policy, PolicyStatus.APPROVED)
    try:
        from runtime.regression_test import run_regression
        report = run_regression(proposed_policy)
        if report.new_auto_process_count < report.old_auto_process_count:
            raise ValueError(f"Regression failed: New auto-process count ({report.new_auto_process_count}) is less than old count ({report.old_auto_process_count}).")
        if report.new_success_rate_on_auto_processed < (report.old_success_rate_on_auto_processed - MIN_SUCCESS_RATE_TOLERANCE):
            raise ValueError(f"Regression failed: New success rate ({report.new_success_rate_on_auto_processed:.2%}) dropped more than tolerance from old rate ({report.old_success_rate_on_auto_processed:.2%}).")
    except (ImportError, AttributeError):
        raise NotImplementedError("Regression testing not yet implemented")

    transition(proposed_policy, PolicyStatus.ACTIVE)
    
    from policy.store import get_active_policy, save_policy
    # Get currently active policy and supersede it
    prefix = proposed_policy.policy_id.rsplit("-v", 1)[0]
    try:
        active = get_active_policy(prefix)
        transition(active, PolicyStatus.SUPERSEDED)
        save_policy(active)
    except Exception:
        pass # No active policy or other issue
    return proposed_policy


def reject(proposed_policy: Policy, reason: str) -> Policy:
    transition(proposed_policy, PolicyStatus.REJECTED)
    proposed_policy.rationale += f" | REJECTED REASON: {reason}"
    return proposed_policy
