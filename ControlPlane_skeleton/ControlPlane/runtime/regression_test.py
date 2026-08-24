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
    newly_auto_processed_count: int = 0
    newly_auto_processed_success_rate: float = 0.0


def run(old_policy: Policy, new_policy: Policy, held_out_data: pd.DataFrame) -> RegressionReport:
    claims = held_out_data.to_dict('records')
    
    old_decisions = evaluate_batch(claims, old_policy)
    new_decisions = evaluate_batch(claims, new_policy)
    
    held_out_size = len(claims)
    
    old_auto = [i for i, d in enumerate(old_decisions) if d.action.value == 'AUTO_PROCESS']
    new_auto = [i for i, d in enumerate(new_decisions) if d.action.value == 'AUTO_PROCESS']
    
    old_auto_process_count = len(old_auto)
    new_auto_process_count = len(new_auto)
    
    def get_success_rate(auto_idx):
        if len(auto_idx) == 0:
            return 0.0
        successes = held_out_data.iloc[auto_idx]['successful_outcome'].sum()
        return successes / len(auto_idx)
        
    old_success_rate = get_success_rate(old_auto)
    new_success_rate = get_success_rate(new_auto)
    
    old_cost = held_out_data.iloc[old_auto]['processing_cost'].sum() if old_auto else 0
    new_cost = held_out_data.iloc[new_auto]['processing_cost'].sum() if new_auto else 0
    
    estimated_cost_delta = new_cost - old_cost
    
    old_human = held_out_size - old_auto_process_count
    new_human = held_out_size - new_auto_process_count
    estimated_workload_delta = new_human - old_human
    
    newly_auto = list(set(new_auto) - set(old_auto))
    newly_auto_processed_count = len(newly_auto)
    newly_auto_processed_success_rate = get_success_rate(newly_auto)
    
    return RegressionReport(
        old_policy_id=old_policy.policy_id,
        new_policy_id=new_policy.policy_id,
        held_out_size=held_out_size,
        old_auto_process_count=old_auto_process_count,
        new_auto_process_count=new_auto_process_count,
        old_success_rate_on_auto_processed=old_success_rate,
        new_success_rate_on_auto_processed=new_success_rate,
        estimated_cost_delta=estimated_cost_delta,
        estimated_workload_delta=estimated_workload_delta,
        newly_auto_processed_count=newly_auto_processed_count,
        newly_auto_processed_success_rate=newly_auto_processed_success_rate
    )


def load_held_out_data(csv_path: str = "data/insurance_claims.csv") -> pd.DataFrame:
    import numpy as np
    import os
    if not os.path.exists(csv_path):
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), csv_path)
        
    df = pd.read_csv(csv_path)
    df['documents_verified'] = df['documents_verified'].astype(bool)
    
    rng = np.random.default_rng(7)
    idx = rng.permutation(len(df))
    split = int(len(df) * 0.7)
    test = df.iloc[idx[split:]].copy()
    
    return test

def run_regression(proposed_policy: Policy) -> RegressionReport:
    from policy.store import get_active_policy
    prefix = proposed_policy.policy_id.rsplit("-v", 1)[0]
    old_policy = get_active_policy(prefix)
    df = load_held_out_data()
    return run(old_policy, proposed_policy, df)
