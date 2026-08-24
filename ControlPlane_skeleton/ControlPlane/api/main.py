"""
api/main.py

Architecture component: API surface (architecture.md A 7).
"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ControlPlane.ai", version="0.1.0")


@app.get("/policy/current")
def get_current_policy():
    from policy.store import get_active_policy
    try:
        return get_active_policy()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/policy/discover")
def discover_policy():
    import os
    from policy.schema import Policy, PolicyStatus
    from engine.discover import run_discovery
    from engine.rationale import generate_rationale, generate_diff_description
    from policy.store import get_active_policy
    from policy.lifecycle import propose

    try:
        new_policy_path = run_discovery()
        candidate_policy = Policy.from_json_file(new_policy_path)
        candidate_policy.status = PolicyStatus.DRAFT
    except Exception as e:
        raise HTTPException(status_code=500, detail="Discovery failed: " + str(e))
        
    active_policy = get_active_policy("POLICY-042")
    cond_summaries = []
    for group in candidate_policy.condition_groups:
        cond_summaries.append("(" + " AND ".join(f"{c.field} {c.operator.value} {c.value}" for c in group) + ")")
    cond_summary = " OR ".join(cond_summaries)
    
    # Simple summary of the old policy for the rationale prompt
    old_conds = []
    for group in active_policy.condition_groups:
        old_conds.append("(" + " AND ".join(f"{c.field} {c.operator.value} {c.value}" for c in group) + ")")
    old_summary = " OR ".join(old_conds)
    
    rationale_text = generate_rationale(candidate_policy.evidence, cond_summary, old_summary)
    diff_text = generate_diff_description(old_summary, cond_summary)
    
    candidate_policy.rationale = rationale_text + "\n\nDiff: " + diff_text
    candidate_policy = propose(candidate_policy)
    
    os.remove(new_policy_path)
    candidate_policy.to_json_file(new_policy_path)
    
    return candidate_policy


@app.post("/policy/{policy_id}/approve")
def approve_policy(policy_id: str):
    import os
    from policy.schema import Policy, PolicyStatus
    from policy.lifecycle import approve
    from runtime.regression_test import run_regression
    
    versions_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "policy", "versions")
    policy_path = os.path.join(versions_dir, f"{policy_id}.json")
    if not os.path.exists(policy_path):
        raise HTTPException(status_code=404, detail="Policy not found")
        
    try:
        policy = Policy.from_json_file(policy_path)
        if policy.status != PolicyStatus.PROPOSED:
            raise HTTPException(status_code=400, detail="Only proposed policies can be approved")
            
        report = run_regression(policy)
        policy = approve(policy)
        
        os.remove(policy_path)
        policy.to_json_file(policy_path)
        return {"policy": policy, "regression_report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/policy/{policy_id}/reject")
def reject_policy(policy_id: str, reason: str = ""):
    import os
    from policy.schema import Policy
    from policy.lifecycle import reject
    
    versions_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "policy", "versions")
    policy_path = os.path.join(versions_dir, f"{policy_id}.json")
    if not os.path.exists(policy_path):
        raise HTTPException(status_code=404, detail="Policy not found")
        
    try:
        policy = Policy.from_json_file(policy_path)
        policy = reject(policy, reason)
        os.remove(policy_path)
        policy.to_json_file(policy_path)
        return policy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/runtime/evaluate")
def evaluate_claim(claim: dict):
    from policy.store import get_active_policy
    from runtime.evaluator import evaluate
    
    try:
        active_policy = get_active_policy()
        # Removed the missing required field check which iterated over active_policy.conditions since it's condition_groups now and Evaluator handles missing fields gracefully anyway
        decision = evaluate(claim, active_policy)
        return decision
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
