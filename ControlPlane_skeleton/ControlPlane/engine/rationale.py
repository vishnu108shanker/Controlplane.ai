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
    """
    Given a discovered rule's evidence and a plain description of the old vs. new
    conditions, produce a short human-readable explanation a non-technical reviewer
    could understand.

    TODO: implement, e.g. via the Anthropic API. Read the API key from the
    ANTHROPIC_API_KEY environment variable -- never hardcode it (see
    docs/prerequisites.md "LLM access").

    IMPORTANT: this function's return value is a string, full stop. It must not
    return or influence anything that ends up in a Policy's `conditions` or
    `action` fields -- those are already fixed by the time this function is called.
    The evidence and conditions passed in here are read-only context, not inputs
    the LLM is being asked to decide.
    """
    raise NotImplementedError


def generate_diff_description(old_policy_summary: str, new_conditions_summary: str) -> str:
    """
    Plain-English "previously X, this proposes Y" description for the approval UI.

    TODO: implement. Can reuse the same LLM call as generate_rationale() or be a
    separate call -- your choice, this is Still Open per docs/philosophy.md.
    """
    raise NotImplementedError
