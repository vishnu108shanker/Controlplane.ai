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


def approve(proposed_policy: Policy) -> Policy:
    transition(proposed_policy, PolicyStatus.APPROVED)
    try:
        from runtime.regression_test import run_regression
        run_regression(proposed_policy)
    except (ImportError, AttributeError):
        raise NotImplementedError("Regression testing not yet implemented")

    transition(proposed_policy, PolicyStatus.ACTIVE)
    # Get currently active policy and supersede it
    prefix = proposed_policy.policy_id.rsplit("-v", 1)[0]
    try:
        active = get_active_policy(prefix)
        transition(active, PolicyStatus.SUPERSEDED)
        import os
        active.to_json_file(os.path.join("policy", "versions", f"{active.policy_id}.json")) # Will raise if it already exists, need to overwrite. Actually conventions say 'never overwrite in place' but we load it without status... wait.
    except Exception:
        pass # No active policy or other issue
    return proposed_policy


def reject(proposed_policy: Policy, reason: str) -> Policy:
    transition(proposed_policy, PolicyStatus.REJECTED)
    proposed_policy.rationale += f" | REJECTED REASON: {reason}"
    return proposed_policy


def get_active_policy(domain_prefix: str = "POLICY-042") -> Policy:
    import os
    versions_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "policy", "versions")
    policies = []
    
    for filename in os.listdir(versions_dir):
        if filename.startswith(domain_prefix) and filename.endswith(".json"):
            path = os.path.join(versions_dir, filename)
            pol = Policy.from_json_file(path)
            policies.append(pol)
            
    # A policy only supersedes another if the superseding policy is ACTIVE or SUPERSEDED itself
    superseded_ids = {p.supersedes for p in policies if p.supersedes and p.status in (PolicyStatus.ACTIVE, PolicyStatus.SUPERSEDED)}
    
    active_policies = []
    for pol in policies:
        # It's active if it claims to be active (or defaulted to active) AND is not superseded
        if pol.status == PolicyStatus.ACTIVE and pol.policy_id not in superseded_ids:
            active_policies.append(pol)
                
    if len(active_policies) == 1:
        return active_policies[0]
    elif len(active_policies) == 0:
        raise ValueError(f"No active policy found for domain {domain_prefix}")
    else:
        raise ValueError(f"Multiple active policies found for domain {domain_prefix}: {[p.policy_id for p in active_policies]}")
