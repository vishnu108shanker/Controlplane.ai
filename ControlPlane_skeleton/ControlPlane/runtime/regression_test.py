"""
runtime/regression_test.py

Architecture component: Regression testing (architecture.md §3, deterministic).

Compares an old policy version against a proposed new one on the SAME held-out
historical data. This is the mandatory gate between "approved" and "active" -- see
policy/lifecycle.py's approve() function, which must call this module.

STATUS: stub. See docs/tasks.md task 4 for the definition of done: running this with
POLICY-042-v1 vs. the reference policy/versions/POLICY-042-v2.json should reproduce
numbers consistent with what engine/discover.py already printed (held-out success
rate ~0.701 for the newly-auto-processed subgroup vs ~0.438 zone baseline -- see
docs/prerequisites.md for the exact reference numbers).
"""

from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from policy.schema import Policy
from runtime.evaluator import evaluate_batch


@dataclass
class RegressionReport:
    old_policy_id: str
    new_policy_id: str
    held_out_size: int
    old_auto_process_count: int
    new_auto_process_count: int
    old_success_rate_on_auto_processed: float
    new_success_rate_on_auto_processed: float
    estimated_cost_delta: float
    estimated_workload_delta: int  # negative = fewer human reviews required


def run(old_policy: Policy, new_policy: Policy, held_out_data: pd.DataFrame) -> RegressionReport:
    """
    TODO: implement.
    - Evaluate held_out_data under both policies via evaluate_batch().
    - For claims routed AUTO_PROCESS under each policy, compute the actual
      `successful_outcome` rate from held_out_data (ground truth already exists
      in the dataset -- this is a backtest, not a live outcome).
    - Compute cost delta using the `processing_cost` column already in the dataset.
    - held_out_data passed in here MUST be data the policy's discovery process
      (engine/discover.py) did not use to find the rule -- reuse the same train/test
      split logic and seed already established in engine/discover.py, don't invent
      a new split.
    """
    raise NotImplementedError


def load_held_out_data(csv_path: str = "data/insurance_claims.csv") -> pd.DataFrame:
    """TODO: reproduce the exact same test split engine/discover.py uses
    (rng = np.random.default_rng(7), 70/30 split) so regression testing is scored
    on the same held-out population the discovery claim was validated against."""
    raise NotImplementedError
