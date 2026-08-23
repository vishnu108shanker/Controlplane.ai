import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N = 20000

customer_tier = rng.choice(['standard', 'silver', 'premium'], size=N, p=[0.55, 0.30, 0.15])
incident_type = rng.choice(
    ['airline_fault', 'weather', 'mechanical', 'theft', 'medical', 'other'],
    size=N, p=[0.18, 0.15, 0.20, 0.12, 0.15, 0.20]
)
documents_verified = rng.choice([True, False], size=N, p=[0.72, 0.28])
prior_claims_count = rng.poisson(0.8, size=N).clip(0, 6)
policy_tenure_years = np.round(rng.gamma(3, 1.5, size=N), 1)
days_since_incident = rng.integers(0, 45, size=N)
region = rng.choice(['north', 'south', 'east', 'west'], size=N)
channel = rng.choice(['app', 'agent', 'call_center'], size=N, p=[0.5, 0.3, 0.2])

claim_amount = np.round(rng.lognormal(mean=10.2, sigma=0.9, size=N), -2)
claim_amount = np.clip(claim_amount, 500, 500000)

# ---- latent true risk (NEVER exposed to the discovery engine directly) ----
risk = np.zeros(N)
risk += (customer_tier == 'standard') * 0.15
risk += (customer_tier == 'silver') * 0.08
risk += (customer_tier == 'premium') * 0.02
risk += (~documents_verified) * 0.30
risk += (incident_type == 'theft') * 0.20
risk += (incident_type == 'other') * 0.10
risk += (incident_type == 'airline_fault') * -0.05
risk += (prior_claims_count >= 3) * 0.18
risk += (channel == 'call_center') * (prior_claims_count >= 3) * 0.15  # confounder, decoy-adjacent
risk += np.clip((claim_amount - 30000) / 300000, 0, 0.25)
risk += rng.normal(0, 0.05, size=N)
risk = np.clip(risk, 0.01, 0.95)

fraud_score = np.clip(risk + rng.normal(0, 0.08, size=N), 0, 1).round(3)

# ---- CURRENT (dumb) policy ----
ai_initial_decision = np.where(claim_amount < 50000, 'AUTO_PROCESS', 'HUMAN_REVIEW')
ai_initial_decision = np.where(fraud_score > 0.75, 'HUMAN_REVIEW', ai_initial_decision)

# ---- human adjuster behaviour (imperfect, not ground truth) ----
adjuster_error = rng.random(N) < 0.08
true_bad = rng.random(N) < risk
human_would_approve = np.where(adjuster_error, true_bad, ~true_bad)

human_final_decision = np.array(['N/A'] * N, dtype=object)
mask_review = ai_initial_decision == 'HUMAN_REVIEW'
human_final_decision[mask_review] = np.where(
    human_would_approve[mask_review], 'APPROVE', 'REJECT'
)

# ---- downstream outcome (ground truth, latent-risk driven) ----
outcome_bad = rng.random(N) < risk
outcome = np.array(['SUCCESSFUL'] * N, dtype=object)
bad_idx = np.where(outcome_bad)[0]
outcome[bad_idx] = rng.choice(
    ['DISPUTED', 'FRAUD_CONFIRMED', 'REOPENED', 'CUSTOMER_COMPLAINT'],
    size=len(bad_idx), p=[0.35, 0.25, 0.20, 0.20]
)
rejected_idx = np.where((ai_initial_decision == 'HUMAN_REVIEW') & (human_final_decision == 'REJECT'))[0]
outcome[rejected_idx] = np.where(
    rng.random(len(rejected_idx)) < 0.6, 'FRAUD_CONFIRMED', 'CUSTOMER_COMPLAINT'
)

processing_cost = np.where(
    ai_initial_decision == 'AUTO_PROCESS',
    40 + fraud_score * 20,
    250 + rng.normal(0, 30, N)
).clip(min=10)
processing_time_hours = np.where(
    ai_initial_decision == 'AUTO_PROCESS',
    rng.uniform(0.05, 0.3, N),
    rng.uniform(6, 72, N)
)

df = pd.DataFrame(dict(
    claim_id=[f'CLM{100000+i}' for i in range(N)],
    customer_tier=customer_tier,
    incident_type=incident_type,
    claim_amount=claim_amount,
    documents_verified=documents_verified,
    prior_claims_count=prior_claims_count,
    policy_tenure_years=policy_tenure_years,
    days_since_incident=days_since_incident,
    region=region,
    channel=channel,
    fraud_score=fraud_score,
    ai_initial_decision=ai_initial_decision,
    human_final_decision=human_final_decision,
    processing_cost=np.round(processing_cost, 2),
    processing_time_hours=np.round(processing_time_hours, 2),
    outcome=outcome,
    successful_outcome=(outcome == 'SUCCESSFUL').astype(int),
))

df.to_csv('insurance_claims.csv', index=False)
print("shape:", df.shape)
print("\nrouting under current policy:\n", df['ai_initial_decision'].value_counts())
print("\noutcome distribution:\n", df['outcome'].value_counts())
print("\noverall successful_outcome rate:", df['successful_outcome'].mean().round(4))
