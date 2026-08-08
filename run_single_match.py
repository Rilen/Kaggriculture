import sys
import json
from kaggle_environments import make

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

def get_completed_cycles(steps):
    cycles = 0
    for step in steps:
        p_action = step[0].get("action", {})
        if isinstance(p_action, dict):
            # Harvests
            farmer = p_action.get("farmer", ["PASS"])[0]
            if farmer == "HARVEST": cycles += 1
            for h in p_action.get("hands", []):
                if isinstance(h, list) and len(h) > 0 and h[0] == "HARVEST":
                    cycles += 1
            # Sales
            for m_act in p_action.get("market", []):
                if m_act and m_act[0] == "SELL":
                    cycles += 1
    return cycles

def run_match(agent_file, seed):
    env = make('kaggriculture', configuration={'episodeSteps': 3000, 'randomSeed': seed})
    steps = env.run([agent_file, 'submission.py'])
    
    score = steps[-1][0].get('reward', 0)
    rev = get_revenue(steps)
    prod = get_productive(steps)
    cycles = get_completed_cycles(steps)
    
    tce = cycles / prod if prod > 0 else 0
    rpa = rev / prod if prod > 0 else 0
    
    # Try to extract telemetry if it's A.3
    # In python, we can't easily get the agent instance from env.run if we pass strings.
    # But since we just want score, rev, prod, it's fine. We can print it out.
    print(json.dumps({"score": score, "rev": rev, "prod": prod, "tce": tce, "rpa": rpa}))

if __name__ == "__main__":
    agent = sys.argv[1]
    seed = int(sys.argv[2])
    run_match(agent, seed)
