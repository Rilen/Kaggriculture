from kaggle_environments import make
from submission_v17_3_a2 import KaggricultureAgentV17 as A2Agent
from submission_v17_3 import KaggricultureAgentV17 as V3Agent
from submission import KaggricultureAgentV17 as OpponentAgent

SEEDS = list(range(42, 62))

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

def get_productive(steps):
    prod = 0
    for step in steps:
        p_action = step[0].get("action", {})
        if isinstance(p_action, dict):
            farmer = p_action.get("farmer", ["PASS"])[0]
            if farmer in ["HARVEST", "PLANT", "WATER", "FEED", "CARE", "PLACE", "COLLECT_FERTILIZER", "BUILD_PASTURE", "PICKUP"]:
                prod += 1
            for h in p_action.get("hands", []):
                if isinstance(h, list) and len(h) > 0:
                    if h[0] in ["HARVEST", "PLANT", "WATER", "FEED", "CARE", "PLACE", "COLLECT_FERTILIZER", "BUILD_PASTURE", "PICKUP"]:
                        prod += 1
    return prod

def run_benchmark():
    v3_total = 0
    a2_total = 0
    v3_rev_total = 0
    a2_rev_total = 0
    a2_prod_total = 0
    
    for seed in SEEDS:
        print(f"\n--- SEED {seed} ---")
        
        # v17.3
        env = make('kaggriculture', configuration={'episodeSteps': 3000, 'randomSeed': seed})
        ag_v3 = V3Agent()
        op_v3 = OpponentAgent()
        steps_v3 = env.run([lambda o: ag_v3(o), lambda o: op_v3(o)])
        score_v3 = steps_v3[-1][0].get('reward', 0)
        rev_v3 = get_revenue(steps_v3)
        v3_total += score_v3
        v3_rev_total += rev_v3
        print(f"v17.3     | Score: {score_v3:8.1f} | Rev: {rev_v3:8.1f}")

        # A.2
        env = make('kaggriculture', configuration={'episodeSteps': 3000, 'randomSeed': seed})
        ag_a2 = A2Agent()
        op_a2 = OpponentAgent()
        steps_a2 = env.run([lambda o: ag_a2(o), lambda o: op_a2(o)])
        score_a2 = steps_a2[-1][0].get('reward', 0)
        rev_a2 = get_revenue(steps_a2)
        prod_a2 = get_productive(steps_a2)
        tel_a2 = ag_a2.telemetry
        
        a2_total += score_a2
        a2_rev_total += rev_a2
        a2_prod_total += prod_a2
        
        print(f"v17.3-A.2 | Score: {score_a2:8.1f} | Rev: {rev_a2:8.1f} | Prod: {prod_a2}")
        print(f"  Telemetry Resupply:")
        print(f"    - RESUPPLY_CLAIMS: {tel_a2.get('RESUPPLY_CLAIMS')}")
        print(f"    - RESUPPLY_COMPLETED: {tel_a2.get('RESUPPLY_COMPLETED')}")
        print(f"    - RESUPPLY_ABORTED: {tel_a2.get('RESUPPLY_ABORTED')}")
        print(f"    - RESUPPLY_DUPLICATED: {tel_a2.get('RESUPPLY_DUPLICATED')}")
        print(f"    - RESUPPLY_LOOP_TURNS: {tel_a2.get('RESUPPLY_LOOP_TURNS')}")
        print(f"    - MAX_CONSECUTIVE_RESUPPLY_TURNS: {tel_a2.get('MAX_CONSECUTIVE_RESUPPLY_TURNS')}")
        
    print(f"\n=========================================")
    print(f"AVERAGE (20 Seeds)")
    print(f"v17.3 Score: {v3_total/20:.1f}")
    print(f"  A.2 Score: {a2_total/20:.1f}")
    print(f"v17.3 Rev:   {v3_rev_total/20:.1f}")
    print(f"  A.2 Rev:   {a2_rev_total/20:.1f}")
    print(f"  A.2 Prod:  {a2_prod_total/20:.1f}")
    print(f"=========================================")

if __name__ == '__main__':
    run_benchmark()
