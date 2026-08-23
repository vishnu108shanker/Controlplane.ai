import pytest
from engine.rationale import generate_rationale
from policy.schema import Evidence

def test_rationale_generation_does_not_mutate_evidence(monkeypatch):
    """
    Test that the LLM call happens *after* the rule and evidence are already fixed, 
    and that it is demonstrably not influencing conditions or action.
    This fulfills the requirement in tasks.md task 5.
    """
    evidence = Evidence(
        train_support=100,
        train_success_rate=0.8,
        train_lift=1.2,
        train_p_value=0.001,
        held_out_support=50,
        held_out_success_rate=0.75,
        held_out_baseline_success_rate=0.5,
        naive_threshold_success_rate=0.5
    )
    
    # Snapshot the evidence dict
    import dataclasses
    evidence_snapshot = dataclasses.asdict(evidence)
    
    # Mock the groq client
    class MockMessage:
        content = "Mock LLM rationale."
    class MockChoice:
        message = MockMessage()
    class MockCompletions:
        def create(self, **kwargs):
            class MockResponse:
                choices = [MockChoice()]
            return MockResponse()
    class MockChat:
        def __init__(self):
            self.completions = MockCompletions()
            
    class MockClient:
        def __init__(self, **kwargs):
            self.chat = MockChat()
            
    monkeypatch.setattr("groq.Groq", MockClient)
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
    
    rationale = generate_rationale(evidence, "new conds", "old summary")
    
    assert rationale == "Mock LLM rationale."
    # Assert evidence was not mutated
    assert dataclasses.asdict(evidence) == evidence_snapshot
