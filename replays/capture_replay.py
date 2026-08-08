"""Run A.4 vs V17.3 head-to-head on seed 42 and save full replay JSON."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kaggle_environments import make
from submission_v17_3 import KaggricultureAgentV17 as V3
from submission_v17_3_a4 import KaggricultureAgentV17 as A4

SEED = 42
env = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": SEED})
ag_v3 = V3()
ag_a4 = A4()
steps = env.run([lambda o: ag_v3(o), lambda o: ag_a4(o)])

replay = {
    "seed": SEED,
    "v3_score": steps[-1][0].get("reward", 0),
    "a4_score": steps[-1][1].get("reward", 0),
    "steps": []
}

ANIMAL_INTERVAL = {"COW": 2, "SHEEP": 3, "GOOSE": 1}

for si, step in enumerate(steps):
    v3_a = step[0].get("action", {})
    a4_a = step[1].get("action", {})
    v3_o = step[0].get("observation", {})
    a4_o = step[1].get("observation", {})
    
    # Extract action summaries
    def action_summary(action_dict):
        if not isinstance(action_dict, dict): return {"farmer": "PASS", "hands": []}
        farmer = action_dict.get("farmer", ["PASS"])
        hands = action_dict.get("hands", [])
        market = action_dict.get("market", [])
        return {
            "farmer": farmer[0] if farmer else "PASS",
            "hands": [h[0] if h else "PASS" for h in hands],
            "market_ops": [m[0] for m in market if m],
        }
    
    def eco_summary(obs):
        if not isinstance(obs, dict): return {}
        farms = obs.get("farms", [])
        farm = farms[0] if farms and isinstance(farms[0], dict) else {}
        private = obs.get("private", {}) if obs else {}
        shed = private.get("shed", {}) if isinstance(private, dict) else {}
        seeds = private.get("seeds", {}) if isinstance(private, dict) else {}
        # Count animals and crops
        cows = sheep = goose = pastures = 0
        crops = {}
        for row in farm.get("tiles", []):
            for t in (row if isinstance(row, list) else []):
                if isinstance(t, dict):
                    if t.get("kind") == "PASTURE":
                        pastures += 1
                        a = t.get("animal")
                        if a == "COW": cows += 1
                        elif a == "SHEEP": sheep += 1
                        elif a == "GOOSE": goose += 1
                    elif t.get("kind") == "PLANT":
                        c = t.get("crop", "?")
                        crops[c] = crops.get(c, 0) + 1
        n_hands = len(farm.get("hands", []))
        return {
            "day": obs.get("day", 0), "hour": obs.get("hour", 0),
            "money": farm.get("money", 0), "n_workers": 1 + n_hands,
            "cows": cows, "sheep": sheep,
            "crops": {k: v for k, v in crops.items() if v > 0},
            "shed_wheat": shed.get("WHEAT", 0),
            "seeds": {k: v for k, v in seeds.items() if v > 0},
        }
    
    replay["steps"].append({
        "step": si,
        "v3_action": action_summary(v3_a),
        "a4_action": action_summary(a4_a),
        "v3_eco": eco_summary(v3_o),
        "a4_eco": eco_summary(a4_o),
        "v3_score_at_step": step[0].get("observation", {}).get("farms", [{}])[0].get("money", 0) if step[0].get("observation", {}).get("farms") else 0,
        "a4_score_at_step": step[1].get("observation", {}).get("farms", [{}])[0].get("money", 0) if step[1].get("observation", {}).get("farms") else 0,
    })

with open("replays/a4_vs_v3_seed42_replay.json", "w") as f:
    json.dump(replay, f)

score_v3 = steps[-1][0].get("reward", 0)
score_a4 = steps[-1][1].get("reward", 0)
print(f"V17.3: {score_v3:.0f} | A.4: {score_a4:.0f} | Delta: {score_a4 - score_v3:+.0f}")
print(f"Replay saved: replays/a4_vs_v3_seed42_replay.json ({len(steps)} steps)")

# Action count comparison
from collections import Counter
v3_acts = Counter()
a4_acts = Counter()
for s in replay["steps"]:
    v3_acts[s["v3_action"]["farmer"]] += 1
    a4_acts[s["a4_action"]["farmer"]] += 1
    for h in s["v3_action"]["hands"]: v3_acts[h] += 1
    for h in s["a4_action"]["hands"]: a4_acts[h] += 1

print("\nAction counts:")
for act in ["FEED", "CARE", "WATER", "HARVEST", "PLANT", "PASS", "PICKUP", "DROP", "COLLECT_FERTILIZER"]:
    v = v3_acts.get(act, 0)
    a = a4_acts.get(act, 0)
    print(f"  {act:<20}: V3={v:>5} A4={a:>5} {'A4 MORE' if a > v else 'A4 LESS' if a < v else 'equal'} ({a-v:+d})")
