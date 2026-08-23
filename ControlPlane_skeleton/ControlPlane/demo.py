"""
demo.py (repo root)

Architecture component: Demo interface (docs/tasks.md task 7).

Runs the full Observe -> Discover -> Propose -> Approve -> Enforce loop end to end
as a scripted CLI walkthrough, for use in the recorded demo video and as a manual
sanity check that the whole system actually works together.

STATUS: stub. Every print() in the real implementation must show a number that was
actually computed in this run -- no hardcoded example numbers. See
docs/conventions.md "Reporting/README conventions".

Expected sequence (docs/tasks.md task 7):
  1. Show current (active) policy.
  2. Load historical claims data.
  3. Run discovery live -- print progress, not just the final answer.
  4. Show the evidence (support, success rate, lift, p-value; then held-out numbers).
  5. Show the diff / rationale for the proposed policy.
  6. Prompt for Approve / Reject (or auto-approve with a flag for CI use).
  7. Run and print the regression test result.
  8. Take a new, unseen example claim and show the routing decision under the new
     policy, contrasted with what the old policy would have said.
"""

from __future__ import annotations
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="ControlPlane.ai demo walkthrough")
    parser.add_argument("--auto-approve", action="store_true",
                         help="Skip the interactive approval prompt (for scripted runs)")
    args = parser.parse_args()

    # TODO Step 1: from policy.lifecycle import get_active_policy; print it.
    # TODO Step 2: load data/insurance_claims.csv.
    # TODO Step 3-4: call engine/discover.py's discovery function; print evidence.
    # TODO Step 5: call engine/rationale.py; print the rationale + diff.
    # TODO Step 6: prompt (or auto-approve); call policy/lifecycle.py's propose()/approve().
    # TODO Step 7: call runtime/regression_test.py; print the report.
    # TODO Step 8: construct one clearly-in-pattern unseen claim and one clearly-not,
    #              evaluate both under old vs new policy, print the contrast.
    raise NotImplementedError


if __name__ == "__main__":
    main()
