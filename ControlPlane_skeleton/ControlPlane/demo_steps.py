from __future__ import annotations
import os
import json
import logging
from policy.schema import Policy, PolicyStatus
from policy.store import get_active_policy

logger = logging.getLogger(__name__)

def step_1_current_policy() -> Policy:
    active_policy = get_active_policy()
    print("=" * 60)
    print("Step 1: Current (active) policy")
    print(f"Policy ID: {active_policy.policy_id}")
    print(f"Action: {active_policy.action.value}")
    print("Conditions:")
    for i, group in enumerate(active_policy.condition_groups):
        if i > 0:
            print("  OR")
        for c in group:
            print(f"  - {c.field} {c.operator.value} {c.value}")
    return active_policy

def step_2_load_data():
    import pandas as pd
    print("\n" + "=" * 60)
    print("Step 2: Loading historical claims data")
    df = pd.read_csv("data/insurance_claims.csv")
    print(f"Loaded {len(df)} historical claims.")
    return df

def step_3_4_run_discovery() -> Policy:
    print("\n" + "=" * 60)
    print("Step 3 & 4: Running Discovery Engine and Validating Evidence")
    from engine.discover import run_discovery
    
    new_policy_path = run_discovery()
    proposed_policy = Policy.from_json_file(new_policy_path)
    proposed_policy.status = PolicyStatus.DRAFT
    
    try:
        os.remove(new_policy_path)
    except FileNotFoundError:
        pass
    proposed_policy.to_json_file(new_policy_path)
    return proposed_policy

def step_5_generate_rationale(proposed_policy: Policy) -> Policy:
    print("\n" + "=" * 60)
    print("Step 5: Generating AI Rationale")
    from engine.rationale import generate_rationale, generate_diff_description
    
    old_summary = "All claims < $50k auto-processed"
    cond_summaries = []
    for group in proposed_policy.condition_groups:
        cond_summaries.append("(" + " AND ".join(f"{c.field} {c.operator.value} {c.value}" for c in group) + ")")
    cond_summary = " OR ".join(cond_summaries)
    
    rationale = generate_rationale(proposed_policy.evidence, cond_summary, old_summary)
    diff = generate_diff_description(old_summary, cond_summary)
    
    print("\nDIFF DESCRIPTION:")
    print(diff)
    print("\nAI RATIONALE:")
    print(rationale)
    
    proposed_policy.rationale = rationale + "\n\nDiff: " + diff
    return proposed_policy

def step_6_propose(proposed_policy: Policy) -> Policy:
    from policy.lifecycle import propose
    proposed_policy = propose(proposed_policy)
    print("\n" + "=" * 60)
    print(f"Policy '{proposed_policy.policy_id}' is now PROPOSED.")
    return proposed_policy

def step_7_regression_and_approve(proposed_policy: Policy) -> Policy:
    print("\n" + "=" * 60)
    print("Step 7: Running Regression Tests before approval...")
    from runtime.regression_test import run_regression
    report = run_regression(proposed_policy)
    
    print("\nREGRESSION TEST REPORT:")
    print(f"  - Held-out size: {report.held_out_size}")
    print(f"  - Old Auto-process count: {report.old_auto_process_count}")
    print(f"  - New Auto-process count: {report.new_auto_process_count}")
    print(f"  - Newly Auto-processed: {report.newly_auto_processed_count}")
    print(f"  - Success rate on newly auto-processed: {report.newly_auto_processed_success_rate:.2%}")
    print(f"  - Estimated workload delta (human reviews): {report.estimated_workload_delta}")
    
    from policy.lifecycle import approve
    approve(proposed_policy)
    
    new_policy_path = os.path.join("policy", "versions", f"{proposed_policy.policy_id}.json")
    try:
        os.remove(new_policy_path)
    except FileNotFoundError:
        pass
    proposed_policy.to_json_file(new_policy_path)
    print(f"\nPolicy '{proposed_policy.policy_id}' is now APPROVED and ACTIVE.")
    return proposed_policy

def step_8_evaluate_claims(active_policy: Policy, proposed_policy: Policy):
    print("\n" + "=" * 60)
    print("Step 8: Evaluating new live claims")
    from runtime.evaluator import evaluate
    
    in_pattern = {
        "incident_type": "airline_fault",
        "fraud_score": 0.1,
        "claim_amount": 10000,
        "customer_tier": "basic",
        "documents_verified": True,
        "prior_claims_count": 0,
        "claim_id": "c-test-1"
    }
    out_pattern = {
        "incident_type": "baggage_loss",
        "fraud_score": 0.5,
        "claim_amount": 15000,
        "customer_tier": "basic",
        "documents_verified": False,
        "prior_claims_count": 0,
        "claim_id": "c-test-2"
    }
    
    print("\nEvaluating IN-PATTERN claim:")
    print(json.dumps(in_pattern, indent=2))
    print(f"Old Policy Decision: {evaluate(in_pattern, active_policy).action.value}")
    print(f"New Policy Decision: {evaluate(in_pattern, proposed_policy).action.value}")
    
    print("\nEvaluating OUT-OF-PATTERN claim:")
    print(json.dumps(out_pattern, indent=2))
    print(f"Old Policy Decision: {evaluate(out_pattern, active_policy).action.value}")
    print(f"New Policy Decision: {evaluate(out_pattern, proposed_policy).action.value}")
