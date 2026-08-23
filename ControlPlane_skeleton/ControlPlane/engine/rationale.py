"""
engine/rationale.py

Architecture component: Policy rationale / diff text (architecture.md §3, LLM-generative).

THE ONLY LLM CALL PERMITTED IN THIS ARCHITECTURE'S DECISION PATH LIVES IN THIS FILE,
AND IT MAY ONLY WRITE TO A `rationale` STRING FIELD. See docs/conventions.md
"LLM usage boundary (non-negotiable)". This module must never be imported by
runtime/evaluator.py.

STATUS: stub. See docs/tasks.md task 5 for the definition of done.
"""

from __future__ import annotations
import os
from policy.schema import Evidence


def generate_rationale(evidence: Evidence, conditions_summary: str, old_policy_summary: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("[rationale] WARNING: No GROQ_API_KEY set — using MOCK rationale, not live LLM.")
        return "MOCK RATIONALE (No GROQ_API_KEY): The data shows this new rule significantly improves success rates compared to the baseline, so it is proposed for auto-processing."
        
    import groq
    client = groq.Groq(api_key=api_key)
    prompt = f"""
You are an AI assistant explaining a newly discovered insurance claim policy rule.

Old Policy: {old_policy_summary}
New Rule Conditions: {conditions_summary}

Evidence from historical backtesting:
- Train Support: {evidence.train_support}
- Held-out Support (Test set): {evidence.held_out_support}
- Held-out Success Rate: {evidence.held_out_success_rate:.2%}
- Baseline Success Rate in this zone: {evidence.held_out_baseline_success_rate:.2%}

Write a short (2-3 sentences) human-readable explanation a non-technical reviewer could understand, explaining why this new rule is being proposed based on the evidence.
"""
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}]
    )
    print(f"[rationale] Live LLM response received from Groq (model: openai/gpt-oss-20b).")
    return response.choices[0].message.content


def generate_diff_description(old_policy_summary: str, new_conditions_summary: str) -> str:
    return f"Previously, {old_policy_summary}. The data shows a pattern, so this proposes auto-processing claims that match: {new_conditions_summary}."
