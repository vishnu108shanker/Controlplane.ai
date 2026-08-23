from __future__ import annotations
import argparse
import os
import subprocess
import json
from dotenv import load_dotenv

def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="ControlPlane.ai demo walkthrough")
    parser.add_argument("--auto-approve", action="store_true",
                         help="Skip the interactive approval prompt (for scripted runs)")
    args = parser.parse_args()

    # Step 1: from policy.lifecycle import get_active_policy; print it.
    from policy.lifecycle import get_active_policy
    active_policy = get_active_policy()
    print("=" * 60)
    print("Step 1: Current (active) policy")
    print(f"Policy ID: {active_policy.policy_id}")
    print(f"Action: {active_policy.action.value}")
    print("Conditions:")
    for c in active_policy.conditions:
        print(f"  - {c.field} {c.operator.value} {c.value}")
    
    # Step 2: load data/insurance_claims.csv.
    import pandas as pd
    print("\n" + "=" * 60)
    print("Step 2: Loading historical claims data")
    df = pd.read_csv("data/insurance_claims.csv")
    print(f"Loaded {len(df)} historical claims.")
    
    if not args.auto_approve:
        input("\nPress Enter to run Discovery Engine...")
    
    # Step 3-4: call engine/discover.py's discovery function; print evidence.
    print("\n" + "=" * 60)
    print("Step 3 & 4: Running Discovery Engine and Validating Evidence")
    # Change working directory so discover.py finds ../data
    engine_dir = os.path.join(os.path.dirname(__file__), "engine")
    subprocess.run(["python", "discover.py"], cwd=engine_dir)
    
    # Reload the proposed policy
    from policy.schema import Policy
    new_policy_path = os.path.join("policy", "versions", "POLICY-042-v2.json")
    proposed_policy = Policy.from_json_file(new_policy_path)
    
    # Set to DRAFT manually for workflow
    from policy.schema import PolicyStatus
    proposed_policy.status = PolicyStatus.DRAFT
    
    # Save draft to disk so get_active_policy ignores it during regression test
    try:
        os.remove(new_policy_path)
    except FileNotFoundError:
        pass
    proposed_policy.to_json_file(new_policy_path)
    
    if not args.auto_approve:
        input("\nPress Enter to generate Rationale...")
        
    # Step 5: call engine/rationale.py; print the rationale + diff.
    print("\n" + "=" * 60)
    print("Step 5: Generating AI Rationale")
    from engine.rationale import generate_rationale, generate_diff_description
    
    old_summary = "All claims < $50k auto-processed"
    cond_summary = " AND ".join(f"{c.field} {c.operator.value} {c.value}" for c in proposed_policy.conditions)
    rationale = generate_rationale(proposed_policy.evidence, cond_summary, old_summary)
    diff = generate_diff_description(old_summary, cond_summary)
    
    print("\nDIFF DESCRIPTION:")
    print(diff.encode('utf-8', 'ignore').decode('utf-8', 'ignore'))
    print("\nAI RATIONALE:")
    print(rationale.encode('utf-8', 'ignore').decode('cp1252', 'ignore'))
    
    proposed_policy.rationale = rationale + "\n\nDiff: " + diff
    
    # Step 6: prompt (or auto-approve); call policy/lifecycle.py's propose()/approve().
    from policy.lifecycle import propose, approve, reject
    proposed_policy = propose(proposed_policy)
    
    print("\n" + "=" * 60)
    print(f"Policy '{proposed_policy.policy_id}' is now PROPOSED.")
    if not args.auto_approve:
        choice = input("Do you want to APPROVE this policy? (y/n): ").strip().lower()
        if choice != 'y':
            reject(proposed_policy, "Rejected by user in demo.")
            print("Policy rejected.")
            return
            
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
    
    approve(proposed_policy)
    try:
        os.remove(new_policy_path)
    except FileNotFoundError:
        pass
    proposed_policy.to_json_file(new_policy_path)
    print(f"\nPolicy '{proposed_policy.policy_id}' is now APPROVED and ACTIVE.")
    
    # Step 8: construct one clearly-in-pattern unseen claim and one clearly-not
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

if __name__ == "__main__":
    main()
