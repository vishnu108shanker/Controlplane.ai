"""
policy/schema.py

Architecture component: Policy compilation (architecture.md §3, deterministic).

Typed representation of the policy JSON object defined in architecture.md §6.
This is the single source of truth for what a "policy" is in this codebase --
runtime/evaluator.py, engine/discover.py's output, and api/main.py should all
import and use these types rather than passing around raw dicts.

STATUS: stub. Fields and shape are fixed by architecture.md §6 -- do not redesign
the schema, only implement the validation/(de)serialization behavior.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class Operator(str, Enum):
    EQ = "=="
    NEQ = "!="
    LTE = "<="
    GTE = ">="
    LT = "<"
    GT = ">"
    IN = "in"


class Action(str, Enum):
    AUTO_PROCESS = "AUTO_PROCESS"
    HUMAN_REVIEW = "HUMAN_REVIEW"


class PolicyStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    SUPERSEDED = "superseded"


@dataclass
class Condition:
    field: str
    operator: Operator
    value: Any

    def evaluate(self, claim: dict) -> bool:
        if self.field not in claim:
            return False
        claim_val = claim[self.field]
        if self.operator == Operator.EQ:
            return claim_val == self.value
        elif self.operator == Operator.NEQ:
            return claim_val != self.value
        elif self.operator == Operator.LTE:
            return claim_val <= self.value
        elif self.operator == Operator.GTE:
            return claim_val >= self.value
        elif self.operator == Operator.LT:
            return claim_val < self.value
        elif self.operator == Operator.GT:
            return claim_val > self.value
        elif self.operator == Operator.IN:
            return claim_val in self.value
        return False


@dataclass
class Evidence:
    train_support: int
    train_success_rate: float
    train_lift: float
    train_p_value: float
    held_out_support: int
    held_out_success_rate: float
    held_out_baseline_success_rate: float
    naive_threshold_success_rate: float


@dataclass
class Policy:
    policy_id: str
    supersedes: str | None
    condition_groups: list[list[Condition]]
    action: Action
    requires_human: bool
    evidence: Evidence | None  # None only allowed for hand-authored baseline (v1)
    rationale: str
    status: PolicyStatus

    def matches(self, claim: dict) -> bool:
        if not self.condition_groups:
            return True
        return any(
            all(cond.evaluate(claim) for cond in group) 
            for group in self.condition_groups
        )

    @classmethod
    def from_json_file(cls, path: str) -> "Policy":
        import json
        with open(path, 'r') as f:
            data = json.load(f)
        
        condition_groups = []
        for group in data.get("condition_groups", []):
            parsed_group = [Condition(field=c["field"], operator=Operator(c["operator"]), value=c["value"]) for c in group]
            condition_groups.append(parsed_group)
            
        action = Action(data["action"])
        evidence_data = data.get("evidence")
        evidence = Evidence(**evidence_data) if evidence_data else None
        status = PolicyStatus(data.get("status", PolicyStatus.ACTIVE))
        
        return cls(
            policy_id=data["policy_id"],
            supersedes=data.get("supersedes"),
            condition_groups=condition_groups,
            action=action,
            requires_human=data.get("requires_human", False),
            evidence=evidence,
            rationale=data.get("rationale", ""),
            status=status
        )

    def to_json_file(self, path: str) -> None:
        import os, json
        if os.path.exists(path):
            raise FileExistsError(f"File {path} already exists. Never overwrite an existing version file.")
        
        from dataclasses import asdict
        data = asdict(self)
        for group in data['condition_groups']:
            for cond in group:
                cond['operator'] = cond['operator'].value
        data['action'] = data['action'].value
        data['status'] = data['status'].value
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
