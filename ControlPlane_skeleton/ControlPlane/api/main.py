from dotenv import load_dotenv
load_dotenv()
"""
api/main.py

Architecture component: API surface (architecture.md §7).

Thin HTTP layer over policy/lifecycle.py, engine/discover.py, and runtime/evaluator.py.
This file should contain almost no logic of its own -- if you find yourself writing
business logic here instead of calling into policy/ or runtime/ or engine/, that logic
belongs in one of those modules instead.

STATUS: stub. See docs/tasks.md task 6 for the definition of done.
"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException

app = FastAPI(title="ControlPlane.ai", version="0.1.0")


@app.get("/policy/current")
def get_current_policy():
    from policy.lifecycle import get_active_policy
    try:
        return get_active_policy()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/policy/discover")
def discover_policy():
    import os, subprocess
    from policy.schema import Policy
    from engine.rationale import generate_rationale, generate_diff_description
    from policy.lifecycle import get_active_policy, propose

    engine_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "engine")
    res = subprocess.run(["python", "discover.py"], cwd=engine_dir, capture_output=True, text=True)
    if res.returncode != 0:
        raise HTTPException(status_code=500, detail="Discovery failed: " + res.stderr)
        
    versions_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "policy", "versions")
    new_policy_path = os.path.join(versions_dir, "POLICY-042-v2.json")
    
    try:
        candidate_policy = Policy.from_json_file(new_policy_path)
        from policy.schema import PolicyStatus
        candidate_policy.status = PolicyStatus.DRAFT
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load generated policy: " + str(e))
        
    old_policy = get_active_policy("POLICY-042")
    old_summary = "All claims < $50k auto-processed"
    cond_summary = " AND ".join(f"{c.field} {c.operator.value} {c.value}" for c in candidate_policy.conditions)
    
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
    from policy.lifecycle import get_active_policy
    from runtime.evaluator import evaluate
    
    try:
        active_policy = get_active_policy()
        for cond in active_policy.conditions:
            if cond.field not in claim:
                raise HTTPException(status_code=422, detail=f"Missing required field: {cond.field}")
        
        decision = evaluate(claim, active_policy)
        return decision
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
