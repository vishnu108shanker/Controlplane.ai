import os
from policy.schema import Policy, PolicyStatus

def get_active_policy(domain_prefix: str = "POLICY-042") -> Policy:
    versions_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "policy", "versions")
    policies = []
    
    for filename in os.listdir(versions_dir):
        if filename.startswith(domain_prefix) and filename.endswith(".json"):
            path = os.path.join(versions_dir, filename)
            pol = Policy.from_json_file(path)
            policies.append(pol)
            
    # A policy only supersedes another if the superseding policy is ACTIVE or SUPERSEDED itself
    superseded_ids = {p.supersedes for p in policies if p.supersedes and p.status in (PolicyStatus.ACTIVE, PolicyStatus.SUPERSEDED)}
    
    active_policies = []
    for pol in policies:
        # It's active if it claims to be active (or defaulted to active) AND is not superseded
        if pol.status == PolicyStatus.ACTIVE and pol.policy_id not in superseded_ids:
            active_policies.append(pol)
                
    if len(active_policies) == 1:
        return active_policies[0]
    elif len(active_policies) == 0:
        raise ValueError(f"No active policy found for domain {domain_prefix}")
    else:
        raise ValueError(f"Multiple active policies found for domain {domain_prefix}: {[p.policy_id for p in active_policies]}")

def save_policy(policy: Policy) -> None:
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "policy", "versions", f"{policy.policy_id}.json")
    policy.to_json_file(path)
