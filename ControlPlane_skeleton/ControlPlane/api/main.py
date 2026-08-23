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
    """
    Returns the currently active policy for the insurance-claims domain.

    TODO: implement via policy.lifecycle.get_active_policy().
    """
    raise NotImplementedError


@app.post("/policy/discover")
def discover_policy():
    """
    Runs engine/discover.py's rule-mining process against the current historical
    dataset, attaches a rationale via engine/rationale.py, and returns a DRAFT/
    PROPOSED policy object -- does NOT activate it.

    TODO: implement. This endpoint must not skip the held-out validation step --
    see docs/conventions.md "Discovery-engine integrity rules".
    """
    raise NotImplementedError


@app.post("/policy/{policy_id}/approve")
def approve_policy(policy_id: str):
    """
    Human approval gate. TODO: implement via policy.lifecycle.approve(), which
    itself must run runtime/regression_test.py before activation completes.
    """
    raise NotImplementedError


@app.post("/policy/{policy_id}/reject")
def reject_policy(policy_id: str, reason: str = ""):
    """TODO: implement via policy.lifecycle.reject()."""
    raise NotImplementedError


@app.post("/runtime/evaluate")
def evaluate_claim(claim: dict):
    """
    Evaluates a new claim against the CURRENTLY ACTIVE policy only. No model call.

    TODO: implement via runtime.evaluator.evaluate(). Validate `claim` has the
    fields the active policy's conditions reference before evaluating -- raise a
    clear HTTPException(422) if a required field is missing, don't silently
    treat a missing field as False.
    """
    raise NotImplementedError
