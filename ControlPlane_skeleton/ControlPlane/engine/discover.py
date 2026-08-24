import json
import itertools
import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportions_ztest
import logging
import os

logger = logging.getLogger(__name__)

def run_discovery(data_path: str = None, v1_path: str = None, output_path: str = None) -> str:
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_path = data_path or os.path.join(base_dir, 'data', 'insurance_claims.csv')
    v1_path = v1_path or os.path.join(base_dir, 'policy', 'versions', 'POLICY-042-v1.json')
    output_path = output_path or os.path.join(base_dir, 'policy', 'versions', 'POLICY-042-v2.json')
    
    df = pd.read_csv(data_path)
    df['documents_verified'] = df['documents_verified'].astype(bool)

    rng = np.random.default_rng(7)
    idx = rng.permutation(len(df))
    split = int(len(df) * 0.7)
    train, test = df.iloc[idx[:split]].copy(), df.iloc[idx[split:]].copy()

    def zone(d):
        return d[(d['ai_initial_decision'] == 'HUMAN_REVIEW') &
                  (d['claim_amount'] >= 50000) & (d['claim_amount'] <= 100000)]

    train_zone = zone(train)
    test_zone = zone(test)
    baseline_rate_train = train_zone['successful_outcome'].mean()
    logger.debug(f"Train zone size: {len(train_zone)}, baseline success rate: {baseline_rate_train:.3f}")

    atoms = {
        'tier_premium':   lambda d: d['customer_tier'] == 'premium',
        'tier_prem_or_silver': lambda d: d['customer_tier'].isin(['premium', 'silver']),
        'airline_fault':  lambda d: d['incident_type'] == 'airline_fault',
        'docs_verified':  lambda d: d['documents_verified'] == True,
        'low_prior_claims': lambda d: d['prior_claims_count'] <= 1,
        'low_fraud_score': lambda d: d['fraud_score'] <= 0.3,
        'region_north':   lambda d: d['region'] == 'north',
        'channel_app':    lambda d: d['channel'] == 'app',
    }
    amount_thresholds = [60000, 65000, 70000, 75000, 80000, 85000]

    candidates = []
    atom_names = list(atoms.keys())
    for r in range(1, 4):
        for combo in itertools.combinations(atom_names, r):
            for thr in amount_thresholds:
                candidates.append(combo + (thr,))

    results = []
    for cand in candidates:
        *conds, thr = cand
        mask = train_zone['claim_amount'] <= thr
        for c in conds:
            mask &= atoms[c](train_zone)
        support = mask.sum()
        if support < 150:
            continue
        success_rate = train_zone.loc[mask, 'successful_outcome'].mean()
        remainder = train_zone.loc[~mask, 'successful_outcome']
        if len(remainder) < 20:
            continue
        count = np.array([mask.sum() * success_rate, len(remainder) * remainder.mean()])
        nobs = np.array([mask.sum(), len(remainder)])
        try:
            z, p = proportions_ztest(count, nobs, alternative='larger')
        except Exception:
            continue
        lift = success_rate / baseline_rate_train
        results.append(dict(conditions=conds, amount_max=thr, support=int(support),
                             success_rate=success_rate, lift=lift, p_value=p, n_conditions=len(conds)))

    res_df = pd.DataFrame(results)
    res_df = res_df[(res_df['p_value'] < 0.01) & (res_df['lift'] > 1.1)]
    res_df = res_df.sort_values(['n_conditions', 'lift'], ascending=[True, False])

    best_lift = res_df.sort_values('lift', ascending=False).iloc[0]
    near_best = res_df[res_df['lift'] >= best_lift['lift'] * 0.95]
    winner = near_best.sort_values('n_conditions').iloc[0]

    logger.debug("\n=== DISCOVERED RULE (train set) ===")
    logger.debug(f"Conditions: {winner['conditions']}  AND  claim_amount <= {winner['amount_max']}")
    logger.debug(f"Support: {winner['support']}  Success rate: {winner['success_rate']:.3f}  "
          f"Lift: {winner['lift']:.2f}x  p-value: {winner['p_value']:.2e}")

    mask_test = test_zone['claim_amount'] <= winner['amount_max']
    for c in winner['conditions']:
        mask_test &= atoms[c](test_zone)
    test_support = mask_test.sum()
    test_success_rate = test_zone.loc[mask_test, 'successful_outcome'].mean()
    test_baseline = test_zone['successful_outcome'].mean()

    logger.debug("\n=== HELD-OUT VALIDATION (test set, never seen during discovery) ===")
    logger.debug(f"Test zone size: {len(test_zone)}, baseline success rate: {test_baseline:.3f}")
    logger.debug(f"Rule support on test: {test_support}, success rate on test: {test_success_rate:.3f}")

    naive_mask_test = test_zone['claim_amount'] <= winner['amount_max']
    naive_support = naive_mask_test.sum()
    naive_success_rate = test_zone.loc[naive_mask_test, 'successful_outcome'].mean()

    logger.debug("\n=== COMPARISON: naive flat-threshold raise vs discovered multivariate rule ===")
    logger.debug(f"Naive (amount <= {winner['amount_max']} only): support={naive_support}, "
          f"success_rate={naive_success_rate:.3f}")
    logger.debug(f"Discovered multivariate rule:      support={test_support}, "
          f"success_rate={test_success_rate:.3f}")
    logger.debug(f"Precision improvement: {(test_success_rate - naive_success_rate) * 100:.1f} percentage points")

    decoys_used = [c for c in winner['conditions'] if c.startswith('region') or c.startswith('channel')]
    logger.debug(f"\nDecoy conditions used by winning rule: {decoys_used if decoys_used else 'NONE (good)'}")

    cond_map = {
        'tier_premium': {"field": "customer_tier", "operator": "==", "value": "premium"},
        'tier_prem_or_silver': {"field": "customer_tier", "operator": "in", "value": ["premium", "silver"]},
        'airline_fault': {"field": "incident_type", "operator": "==", "value": "airline_fault"},
        'docs_verified': {"field": "documents_verified", "operator": "==", "value": True},
        'low_prior_claims': {"field": "prior_claims_count", "operator": "<=", "value": 1},
        'low_fraud_score': {"field": "fraud_score", "operator": "<=", "value": 0.3},
    }
    with open(v1_path, 'r') as f:
        v1_policy = json.load(f)

    new_group = [cond_map[c] for c in winner['conditions']] + [{"field": "claim_amount", "operator": "<=", "value": int(winner['amount_max'])}]
    condition_groups = v1_policy.get("condition_groups", []) + [new_group]

    policy = {
        "policy_id": "POLICY-042-v2",
        "supersedes": "POLICY-042-v1",
        "condition_groups": condition_groups,
        "action": "AUTO_PROCESS",
        "requires_human": False,
        "evidence": {
            "train_support": int(winner['support']),
            "train_success_rate": round(float(winner['success_rate']), 4),
            "train_lift": round(float(winner['lift']), 3),
            "train_p_value": float(winner['p_value']),
            "held_out_support": int(test_support),
            "held_out_success_rate": round(float(test_success_rate), 4),
            "held_out_baseline_success_rate": round(float(test_baseline), 4),
            "naive_threshold_success_rate": round(float(naive_success_rate), 4)
        }
    }
    with open(output_path, 'w') as f:
        json.dump(policy, f, indent=2)
    logger.debug("\nWrote policy_v2.json")
    return output_path

if __name__ == "__main__":
    run_discovery()
