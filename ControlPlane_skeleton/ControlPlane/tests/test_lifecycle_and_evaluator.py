"""
tests/test_lifecycle_and_evaluator.py

Minimum required tests per docs/tasks.md tasks 2 and 3. Expand as more of the
skeleton gets implemented -- this file is a starting point, not the full suite.
"""

import pytest


class TestPolicyLifecycleTransitions:
    """docs/tasks.md task 2: every transition, including illegal ones."""

    def test_draft_to_proposed_is_legal(self):
        pytest.skip("TODO: implement once policy/lifecycle.py exists")

    def test_proposed_to_approved_is_legal(self):
        pytest.skip("TODO")

    def test_proposed_to_rejected_is_legal(self):
        pytest.skip("TODO")

    def test_draft_to_active_is_illegal(self):
        """Cannot skip the approval gate -- see docs/philosophy.md."""
        pytest.skip("TODO: assert IllegalTransitionError is raised")

    def test_approve_triggers_regression_test(self):
        """approve() must call runtime/regression_test.py -- see docs/conventions.md
        'Testing conventions'. This test should fail loudly if approve() is changed
        to skip regression testing."""
        pytest.skip("TODO")


class TestRuntimeEvaluator:
    """docs/tasks.md task 3: evaluator must agree with simulate.py's ground truth."""

    def test_evaluator_matches_dataset_ground_truth_under_v1(self):
        """
        Load data/insurance_claims.csv, evaluate every row's claim fields against
        POLICY-042-v1 via runtime.evaluator.evaluate(), and assert the result
        matches that row's `ai_initial_decision` column exactly. This is the
        correctness check specified in docs/tasks.md task 3 -- disagreement means
        a bug in evaluator.py, not the data.
        """
        pytest.skip("TODO: implement once runtime/evaluator.py exists")

    def test_requires_human_overrides_action(self):
        pytest.skip("TODO")

    def test_no_matching_policy_falls_through_to_human_review(self):
        pytest.skip("TODO")
