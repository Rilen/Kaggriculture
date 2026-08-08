import json
import sys
from kaggle_environments import make
from submission_v17_4_a import KaggricultureAgentV17 as V4AAgent

SEED = 48

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

print(f"=== GATE 1 — V17.4-A Claim-Time Eligibility — Seed {SEED} ===\n")

try:
    env = make('kaggriculture', configuration={'episodeSteps': 3000, 'randomSeed': SEED})
    ag = V4AAgent()
    steps = env.run([lambda o: ag(o), 'submission.py'])
    
    score = steps[-1][0].get('reward', 0)
    revenue = get_revenue(steps)
    prod = get_productive(steps)
    wsteps = get_worker_steps(steps)
    idle = get_true_idle(steps)
    rpa = revenue / prod if prod > 0 else 0
    rws = revenue / wsteps if wsteps > 0 else 0
    
    tel = ag.telemetry
    
    print(f"Score:                     {score:.0f}")
    print(f"Revenue:                   {revenue:.0f}")
    print(f"Productive Actions:        {prod}")
    print(f"True Idle Turns:           {idle}")
    print(f"Worker Steps:              {wsteps}")
    print(f"RPA:                       {rpa:.2f}")
    print(f"Revenue / Worker-Step:     {rws:.2f}")
    print()
    print(f"--- V17.4-A Telemetry ---")
    print(f"claims_rejected_ineligible:              {tel.get('claims_rejected_ineligible')}")
    print(f"target_claims:                          {tel.get('target_claims')}")
    print(f"target_releases:                        {tel.get('target_releases')}")
    print(f"target_changes:                         {tel.get('target_changes')}")
    print(f"claims_released_due_to_unreachable_target: {tel.get('claims_released_due_to_unreachable_target')}")
    print(f"claims_released_due_to_invalid_target:  {tel.get('claims_released_due_to_invalid_target')}")
    print(f"claims_released_on_arrival:             {tel.get('claims_released_on_arrival')}")
    print(f"claims_released_after_productive_action: {tel.get('claims_released_after_productive_action')}")
    print(f"replan_count:                           {tel.get('replan_count')}")
    print(f"circuit_breaker_triggered:              {tel.get('circuit_breaker_triggered')}")
    print(f"invalid_action_intercepted:             {tel.get('invalid_action_intercepted')}")
    print(f"target_persistence_turns:               {tel.get('target_persistence_turns')}")
    
    print()
    print("=== GATE 1 PASSED ===")
    
except Exception as e:
    print(f"=== GATE 1 FAILED ===")
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
