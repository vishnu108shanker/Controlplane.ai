from __future__ import annotations
import argparse
import logging
from dotenv import load_dotenv

from demo_steps import (
    step_1_current_policy, step_2_load_data, step_3_4_run_discovery,
    step_5_generate_rationale, step_6_propose, step_7_regression_and_approve,
    step_8_evaluate_claims
)
from policy.lifecycle import reject

def main():
    load_dotenv()
    logging.basicConfig(level=logging.DEBUG)
    
    parser = argparse.ArgumentParser(description="ControlPlane.ai Dev Demo")
    parser.add_argument("--auto-approve", action="store_true", help="Skip prompts")
    args = parser.parse_args()
    
    active_policy = step_1_current_policy()
    step_2_load_data()
    
    if not args.auto_approve:
        input("\nPress Enter to run Discovery Engine...")
    proposed_policy = step_3_4_run_discovery()
    
    if not args.auto_approve:
        input("\nPress Enter to generate Rationale...")
    proposed_policy = step_5_generate_rationale(proposed_policy)
    
    proposed_policy = step_6_propose(proposed_policy)
    
    if not args.auto_approve:
        choice = input("Do you want to APPROVE this policy? (y/n): ").strip().lower()
        if choice != 'y':
            reject(proposed_policy, "Rejected by user in demo.")
            print("Policy rejected.")
            return
            
    approved_policy = step_7_regression_and_approve(proposed_policy)
    step_8_evaluate_claims(active_policy, approved_policy)

if __name__ == "__main__":
    main()
