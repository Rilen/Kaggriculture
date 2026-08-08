import sys
from kaggle_environments import make
from submission_v17_4_a import KaggricultureAgentV17 as V4AAgent

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

def get_worker_steps(steps):
    ws = 0
    for step in steps:
        p_action = step[0].get("action", {})
        if isinstance(p_action, dict):
            farmer = p_action.get("farmer", ["PASS"])
            if farmer and farmer[0] in ("NORTH", "SOUTH", "EAST", "WEST"):
                ws += 1
            for h in p_action.get("hands", []):
                if h and h[0] in ("NORTH", "SOUTH", "EAST", "WEST"):
                    ws += 1
    return ws

def get_true_idle(steps):
    idle = 0
    for step in steps:
        p_action = step[0].get("action", {})
        if isinstance(p_action, dict):
            farmer = p_action.get("farmer", ["PASS"])
            if farmer and farmer[0] == "PASS":
                idle += 1
            for h in p_action.get("hands", []):
                if h and h[0] == "PASS":
                    idle += 1
    return idle

for seed in SEEDS:
    env = make('kaggriculture', configuration={'episodeSteps': 3000, 'randomSeed': seed})
    ag = V4AAgent()
    steps = env.run([lambda o: ag(o), 'submission.py'])
    
    score = steps[-1][0].get('reward', 0)
    rev = get_revenue(steps)
    prod = get_productive(steps)
    wsteps = get_worker_steps(steps)
    idle = get_true_idle(steps)
    rpa = rev / prod if prod > 0 else 0
    tel = ag.telemetry
    
    print(f"Seed {seed}: Score={score:.0f} Rev={rev:.0f} Prod={prod} Idle={idle} WSteps={wsteps} RPA={rpa:.2f}")
    print(f"  Rejected: {tel.get('claims_rejected_ineligible')} | Unreachable: {tel.get('claims_released_due_to_unreachable_target')}")
    print(f"  Claims: {tel.get('target_claims')} | Releases: {tel.get('target_releases')} | Changes: {tel.get('target_changes')}")
    print(f"  AfterProd: {tel.get('claims_released_after_productive_action')} | InvalidTarget: {tel.get('claims_released_due_to_invalid_target')}")
    print(f"  Replans: {tel.get('replan_count')} | CircuitBreaker: {tel.get('circuit_breaker_triggered')} | Invalid: {tel.get('invalid_action_intercepted')}")
