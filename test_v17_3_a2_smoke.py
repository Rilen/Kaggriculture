from kaggle_environments import make
from submission_v17_3_a2 import KaggricultureAgentV17 as A2Agent
from submission_v17_3 import KaggricultureAgentV17 as V3Agent

SEEDS = [42, 43, 44]

def get_revenue(steps):
    rev = 0
    for step in steps:
        p_action = step[0].get("action", {})
        obs = step[0].get("observation", {})
        prices = obs.get("market", {}).get("prices", {}) if obs else {}
        if isinstance(p_action, dict):
            for m_act in p_action.get("market", []):
                if m_act and m_act[0] == "SELL" and len(m_act) >= 3:
                    rev += m_act[2] * prices.get(m_act[1], 0)
    return rev

def run_smoke():
    for seed in SEEDS:
        print(f"\n--- SEED {seed} ---")
        
        # v17.3
        env = make('kaggriculture', configuration={'episodeSteps': 3000, 'randomSeed': seed})
        ag_v3 = V3Agent()
        steps_v3 = env.run([lambda o: ag_v3(o), 'submission.py'])
        score_v3 = steps_v3[-1][0].get('reward', 0)
        rev_v3 = get_revenue(steps_v3)
        print(f"v17.3     | Score: {score_v3:8.1f} | Rev: {rev_v3:8.1f} | Collisions: N/A")

        # A.2
        env = make('kaggriculture', configuration={'episodeSteps': 3000, 'randomSeed': seed})
        ag_a2 = A2Agent()
        steps_a2 = env.run([lambda o: ag_a2(o), 'submission.py'])
        score_a2 = steps_a2[-1][0].get('reward', 0)
        rev_a2 = get_revenue(steps_a2)
        tel_a2 = ag_a2.telemetry
        
        resupply_claims = tel_a2.get("target_claims", 0) # Note: we don't track resupply claims separately yet, but target claims give a hint
        
        print(f"v17.3-A.2 | Score: {score_a2:8.1f} | Rev: {rev_a2:8.1f}")
        print(f"  Telemetry A.2:")
        print(f"    - claims_released_due_to_unreachable_target: {tel_a2.get('claims_released_due_to_unreachable_target')}")
        print(f"    - claims_released_due_to_invalid_target: {tel_a2.get('claims_released_due_to_invalid_target')}")
        print(f"    - claims_released_after_productive_action: {tel_a2.get('claims_released_after_productive_action')}")
        print(f"    - claims_released_on_arrival: {tel_a2.get('claims_released_on_arrival')}")
        print(f"    - circuit_breaker_triggered: {tel_a2.get('circuit_breaker_triggered')}")
        print(f"    - invalid_action_intercepted: {tel_a2.get('invalid_action_intercepted')}")
        print(f"    - max_consecutive_same_intent: {tel_a2.get('max_consecutive_same_intent')}")

if __name__ == '__main__':
    run_smoke()
