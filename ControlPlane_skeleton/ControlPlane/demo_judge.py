from __future__ import annotations
import argparse
import logging
import json
from dotenv import load_dotenv

from demo_steps import (
    step_1_current_policy, step_2_load_data, step_3_4_run_discovery,
    step_5_generate_rationale, step_6_propose, step_7_regression_and_approve,
    step_8_evaluate_claims
)
from policy.lifecycle import reject
from runtime.evaluator import evaluate

# Colors for presentation
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_decision(decision_value: str):
    if decision_value == "AUTO_PROCESS":
        return f"{GREEN}{decision_value}{RESET}"
    return f"{YELLOW}{decision_value}{RESET}"

def interactive_loop(active_policy, approved_policy):
    print("\n" + "=" * 60)
    print("Interactive Evaluation Mode")
    print("Enter claim details to see how they route under the old vs. new policy.")
    print("Type 'exit' to quit.\n")
    
    while True:
        try:
            amt_input = input("Enter claim amount (e.g. 60000): ").strip()
            if amt_input.lower() == 'exit':
                break
            amount = float(amt_input)
            
            incident = input("Enter incident type (e.g. airline_fault, baggage_loss): ").strip()
            if incident.lower() == 'exit':
                break
                
            fraud = input("Enter fraud score 0.0 - 1.0 (e.g. 0.1): ").strip()
            if fraud.lower() == 'exit':
                break
            fraud_score = float(fraud)
            
            claim = {
                "incident_type": incident,
                "fraud_score": fraud_score,
                "claim_amount": amount,
                "customer_tier": "basic",
                "documents_verified": True,
                "prior_claims_count": 0,
                "claim_id": "interactive-1"
            }
            
            print(f"\nEvaluating Claim: {json.dumps(claim, indent=2)}")
            old_dec = evaluate(claim, active_policy).action.value
            new_dec = evaluate(claim, approved_policy).action.value
            
            print(f"Old Policy Decision: {print_decision(old_dec)}")
            print(f"New Policy Decision: {print_decision(new_dec)}\n")
            
        except ValueError:
            print("Invalid input, please enter a number.")
        except KeyboardInterrupt:
            print("\nExiting interactive mode.")
            break

def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    
    print(f"{GREEN}ControlPlane.ai Judge Demo{RESET}\n")
    
    active_policy = step_1_current_policy()
    step_2_load_data()
    
    input(f"\n{YELLOW}Press Enter to run Discovery Engine...{RESET}")
    proposed_policy = step_3_4_run_discovery()
    
    input(f"\n{YELLOW}Press Enter to generate Rationale...{RESET}")
    proposed_policy = step_5_generate_rationale(proposed_policy)
    
    proposed_policy = step_6_propose(proposed_policy)
    
    choice = input(f"{YELLOW}Do you want to APPROVE this policy? (y/n): {RESET}").strip().lower()
    if choice != 'y':
        reject(proposed_policy, "Rejected by user in demo.")
        print("Policy rejected.")
        return
        
    approved_policy = step_7_regression_and_approve(proposed_policy)
    step_8_evaluate_claims(active_policy, approved_policy)
    
    interactive_loop(active_policy, approved_policy)

if __name__ == "__main__":
    main()
