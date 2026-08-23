"""
tests/test_lifecycle_and_evaluator.py

Minimum required tests per docs/tasks.md tasks 2 and 3. Expand as more of the
skeleton gets implemented -- this file is a starting point, not the full suite.
"""

import pytest


class TestPolicyLifecycleTransitions:
    """docs/tasks.md task 2: every transition, including illegal ones."""

    def test_draft_to_proposed_is_legal(self):
        from policy.schema import Policy, PolicyStatus, Action
        p = Policy("test-v1", None, [], Action.AUTO_PROCESS, False, None, "", PolicyStatus.DRAFT)
        from policy.lifecycle import propose
        p = propose(p)
        assert p.status == PolicyStatus.PROPOSED

    def test_proposed_to_approved_is_legal(self):
        from policy.schema import Policy, PolicyStatus, Action
        p = Policy("test-v1", None, [], Action.AUTO_PROCESS, False, None, "", PolicyStatus.PROPOSED)
        from policy.lifecycle import transition
        # test just the transition function for APPROVED since approve() needs regression testing
        p = transition(p, PolicyStatus.APPROVED)
        assert p.status == PolicyStatus.APPROVED

    def test_proposed_to_rejected_is_legal(self):
        from policy.schema import Policy, PolicyStatus, Action
        p = Policy("test-v1", None, [], Action.AUTO_PROCESS, False, None, "", PolicyStatus.PROPOSED)
        from policy.lifecycle import reject
        p = reject(p, "too risky")
        assert p.status == PolicyStatus.REJECTED
        assert "too risky" in p.rationale

    def test_draft_to_active_is_illegal(self):
        """Cannot skip the approval gate -- see docs/philosophy.md."""
        from policy.schema import Policy, PolicyStatus, Action
        p = Policy("test-v1", None, [], Action.AUTO_PROCESS, False, None, "", PolicyStatus.DRAFT)
        from policy.lifecycle import transition, IllegalTransitionError
        with pytest.raises(IllegalTransitionError):
            transition(p, PolicyStatus.ACTIVE)

    def test_approve_triggers_regression_test(self, monkeypatch):
        """approve() must call runtime/regression_test.py -- see docs/conventions.md
        'Testing conventions'. This test should fail loudly if approve() is changed
        to skip regression testing."""
        from policy.schema import Policy, PolicyStatus, Action
        from policy.lifecycle import approve
        
        called = False
        def mock_run_regression(policy):
            nonlocal called
            called = True
            
        monkeypatch.setattr('runtime.regression_test.run_regression', mock_run_regression)
        
        p = Policy("test-v1", None, [], Action.AUTO_PROCESS, False, None, "", PolicyStatus.PROPOSED)
        approve(p)
        assert called, "regression_test.run_regression was not called!"


class TestRuntimeEvaluator:
    """docs/tasks.md task 3: evaluator must agree with simulate.py's ground truth."""

    def test_evaluator_matches_dataset_ground_truth_under_v1(self):
        import pandas as pd
        import os
        from policy.schema import Policy
        from runtime.evaluator import evaluate_batch
        
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'insurance_claims.csv')
        df = pd.read_csv(csv_path)
        claims = df.to_dict('records')
        policy_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'policy', 'versions', 'POLICY-042-v1.json')
        p = Policy.from_json_file(policy_path)
        
        decisions = evaluate_batch(claims, policy=p)
        for i, decision in enumerate(decisions):
            assert decision.action.value == df.iloc[i]['ai_initial_decision']

    def test_requires_human_overrides_action(self):
        from policy.schema import Policy, PolicyStatus, Action, Condition, Operator
        from runtime.evaluator import evaluate
        p = Policy("test-v1", None, [Condition("amt", Operator.LT, 50)], Action.AUTO_PROCESS, True, None, "", PolicyStatus.ACTIVE)
        claim = {"amt": 10}
        d = evaluate(claim, p)
        assert d.action == Action.HUMAN_REVIEW

    def test_no_matching_policy_falls_through_to_human_review(self):
        from policy.schema import Policy, PolicyStatus, Action, Condition, Operator
        from runtime.evaluator import evaluate
        p = Policy("test-v1", None, [Condition("amt", Operator.LT, 50)], Action.AUTO_PROCESS, False, None, "", PolicyStatus.ACTIVE)
        claim = {"amt": 100}
        d = evaluate(claim, p)
        assert d.action == Action.HUMAN_REVIEW
