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
    """
    Move `policy` to `new_status` if legal, else raise IllegalTransitionError.

    TODO: implement using _ALLOWED_TRANSITIONS above. This function should be the
    ONLY way policy.status is ever changed anywhere in the codebase -- api/main.py's
    approve/reject endpoints must call this, not set .status directly.
    """
    raise NotImplementedError


def propose(draft_policy: Policy) -> Policy:
    """
    draft -> proposed. Called after engine/discover.py produces a candidate and
    engine/rationale.py has attached its explanation text.

    TODO: implement, using transition() above.
    """
    raise NotImplementedError


def approve(proposed_policy: Policy) -> Policy:
    """
    proposed -> approved -> active.

    TODO: implement. This function MUST call runtime/regression_test.py before
    completing the approved -> active transition. If regression testing is not
    yet implemented, this function must raise NotImplementedError rather than
    silently skip the check -- see docs/conventions.md "Testing conventions".

    On success, the previously active policy for the same domain (same leading
    POLICY-<id> prefix) must transition ACTIVE -> SUPERSEDED.
    """
    raise NotImplementedError


def reject(proposed_policy: Policy, reason: str) -> Policy:
    """proposed -> rejected. TODO: implement, store `reason` somewhere retrievable
    (e.g. append to the policy's rationale, or a separate audit log -- your choice,
    just don't silently drop it)."""
    raise NotImplementedError


def get_active_policy(domain_prefix: str = "POLICY-042") -> Policy:
    """
    TODO: implement. Scan policy/versions/ for the file with status == "active"
    matching domain_prefix. Exactly one must be active at any time -- if zero or
    more than one are found, raise, don't guess.
    """
    raise NotImplementedError
