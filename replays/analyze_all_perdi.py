"""Bulk analysis of all perdi/ opponent strategies."""
import json, os, glob
from collections import Counter, defaultdict

files = sorted(glob.glob(r"C:\Users\rtl\Documents\Github\Kaggriculture\perdi\*.json"))
print(f"Analyzing {len(files)} loss episodes...\n")

summary = []
for fp in files:
    f = open(fp); d = json.load(f); f.close()
    steps = d["steps"]; info = d["info"]
    eid = info["EpisodeId"]; teams = info.get("TeamNames", ["?", "?"])
    seed = info.get("seed", 0)
    
    our_ai = 0 if "Rilen" in (teams[0] if len(teams)>0 else "") else 1
    opp_ai = 1 - our_ai
    
    rev_opp = 0.0; rev_us = 0.0
    act_opp = Counter(); act_us = Counter()
    sell_opp = Counter(); sell_us = Counter()
    hire_opp = hire_us = 0
    
    for step in steps:
        for ai, ctr, sctr in [(opp_ai, act_opp, sell_opp), (our_ai, act_us, sell_us)]:
            a = step[ai].get("action", {})
            obs = step[ai].get("observation", {})
            prices = obs.get("market", {}).get("prices", {}) if obs else {}
            if isinstance(a, dict):
                for m in a.get("market", []):
                    if m and m[0] == "SELL" and len(m) >= 3:
                        rev = m[2] * prices.get(m[1], 0)
                        if ai == opp_ai: rev_opp += rev
                        else: rev_us += rev
                        sctr[m[1]] += m[2]
                    if m and m[0] == "HIRE":
                        if ai == opp_ai: hire_opp += 1
                        else: hire_us += 1
                for wa in [a.get("farmer", [""])] + a.get("hands", []):
                    if wa: ctr[wa[0]] += 1
    
    s_opp = steps[-1][opp_ai].get("reward", 0)
    s_us = steps[-1][our_ai].get("reward", 0)
    
    water_opp = act_opp.get("WATER", 0); water_us = act_us.get("WATER", 0)
    fert_opp = act_opp.get("FERTILIZE", 0); fert_us = act_us.get("FERTILIZE", 0)
    
    # Final farm
    obs_final = steps[-1][opp_ai].get("observation", {})
    farms = obs_final.get("farms", [])
    farm = farms[opp_ai] if farms and opp_ai < len(farms) and isinstance(farms[opp_ai], dict) else {}
    cows = sheep = goose = 0; crops = Counter()
    for row in farm.get("tiles", []):
        for t in (row if isinstance(row, list) else []):
            if isinstance(t, dict):
                if t.get("kind") == "PASTURE":
                    a = t.get("animal")
                    if a == "COW": cows += 1
                    elif a == "SHEEP": sheep += 1
                elif t.get("kind") == "COOP":
                    if t.get("animal") == "GOOSE": goose += 1
                elif t.get("kind") == "PLANT":
                    crops[t.get("crop", "?")] += 1
    
    summary.append({
        "eid": eid, "seed": seed, "opp": teams[opp_ai],
        "s_opp": s_opp, "s_us": s_us, "ratio": s_opp/max(s_us, 1),
        "rev_opp": rev_opp, "rev_us": rev_us,
        "water_opp": water_opp, "water_us": water_us,
        "fert_opp": fert_opp, "fert_us": fert_us,
        "cows": cows, "sheep": sheep, "goose": goose,
        "crops": dict(crops),
        "hire_opp": hire_opp, "hire_us": hire_us,
        "sells_opp": dict(sell_opp.most_common(5)),
    })

# Print summary table
print(f"{'Ep':<10} {'Opponent':<22} {'Score':>8} {'Our':>8} {'Ratio':>6} {'W_Opp':>6} {'W_Us':>6} {'F_Opp':>5} {'Cows':>5} {'Sheep':>5} {'Goose':>5} {'Top Sells':<35}")
print("-" * 140)
for s in summary:
    w_ratio = s["water_opp"] / max(s["water_us"], 1)
    crops_str = str(s["crops"])[:30]
    print(f"{s['eid']:<10} {s['opp'][:20]:<22} {s['s_opp']:>8.0f} {s['s_us']:>8.0f} {s['ratio']:>5.1f}x {s['water_opp']:>6} {s['water_us']:>6} {s['fert_opp']:>5} {s['cows']:>5} {s['sheep']:>5} {s['goose']:>5} {str(s['sells_opp'])[:35]}")

# Aggregate stats
print(f"\n=== AGGREGATE ({len(summary)} episodes) ===")
import statistics
water_ratios = [s["water_opp"]/max(s["water_us"],1) for s in summary]
score_ratios = [s["ratio"] for s in summary]
print(f"Mean WATER ratio (OPP/US): {statistics.mean(water_ratios):.1f}x")
print(f"Mean SCORE ratio: {statistics.mean(score_ratios):.1f}x")
print(f"Mean OPP WATER: {statistics.mean([s['water_opp'] for s in summary]):.0f}")
print(f"Mean US  WATER: {statistics.mean([s['water_us'] for s in summary]):.0f}")
print(f"Mean OPP FERT: {statistics.mean([s['fert_opp'] for s in summary]):.0f}")
print(f"Mean US  FERT: {statistics.mean([s['fert_us'] for s in summary]):.0f}")

# Opponent frequency
opp_counts = Counter(s["opp"] for s in summary)
print(f"\nMost frequent opponents:")
for opp, cnt in opp_counts.most_common(10):
    s_list = [s for s in summary if s["opp"] == opp]
    avg_water = statistics.mean([s["water_opp"] for s in s_list])
    avg_ratio = statistics.mean([s["ratio"] for s in s_list])
    print(f"  {opp:<25}: {cnt:>2} losses, WATER={avg_water:.0f}, ratio={avg_ratio:.1f}x")
