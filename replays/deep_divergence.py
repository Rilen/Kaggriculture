"""Deep divergence analysis — find first material advantage point in perdi/ matches."""
import json
from collections import Counter, defaultdict

def analyze_divergence(fp):
    f = open(fp); d = json.load(f); f.close()
    steps = d["steps"]
    info = d["info"]
    teams = info.get("TeamNames", ["?", "?"])
    eid = info["EpisodeId"]
    
    our_ai = 0 if "Rilen" in (teams[0] if len(teams)>0 else "") else 1
    opp_ai = 1 - our_ai
    
    # Cumulative revenue tracking
    rev_opp = [0.0] * len(steps); rev_us = [0.0] * len(steps)
    cum_o = 0.0; cum_u = 0.0
    
    # Per-step action tracking
    actions_opp = []; actions_us = []
    
    # First events
    first_plant_opp = None; first_plant_us = None
    first_water_opp = None; first_water_us = None
    first_harvest_opp = None; first_harvest_us = None
    first_sell_opp = None; first_sell_us = None
    first_hire_opp = None; first_hire_us = None
    first_straw_opp = None; first_straw_us = None
    
    for si, step in enumerate(steps):
        day = step[0].get("observation", {}).get("day", 0)
        hour = step[0].get("observation", {}).get("hour", 0)
        
        for ai, cum_ref, rev_arr, firsts in [(opp_ai, "opp", rev_opp, None), (our_ai, "us", rev_us, None)]:
            a = step[ai].get("action", {})
            obs = step[ai].get("observation", {})
            prices = obs.get("market", {}).get("prices", {}) if obs else {}
            
            if isinstance(a, dict):
                # Revenue
                for m in a.get("market", []):
                    if m and m[0] == "SELL" and len(m) >= 3:
                        rev = m[2] * prices.get(m[1], 0)
                        if ai == opp_ai: cum_o += rev
                        else: cum_u += rev
                        if ai == opp_ai and first_sell_opp is None:
                            first_sell_opp = (si, day, hour, m[1], m[2], rev)
                        if ai == our_ai and first_sell_us is None:
                            first_sell_us = (si, day, hour, m[1], m[2], rev)
                
                # Worker actions
                for wa in [a.get("farmer", [])] + a.get("hands", []):
                    if not wa: continue
                    op = wa[0]; detail = wa[1] if len(wa) > 1 else ""
                    if ai == opp_ai:
                        actions_opp.append((si, day, hour, op, detail))
                    else:
                        actions_us.append((si, day, hour, op, detail))
                    
                    if ai == opp_ai and first_plant_opp is None and op == "PLANT":
                        first_plant_opp = (si, day, hour, detail)
                    if ai == our_ai and first_plant_us is None and op == "PLANT":
                        first_plant_us = (si, day, hour, detail)
                    if ai == opp_ai and first_water_opp is None and op == "WATER":
                        first_water_opp = (si, day, hour)
                    if ai == our_ai and first_water_us is None and op == "WATER":
                        first_water_us = (si, day, hour)
                    if ai == opp_ai and first_harvest_opp is None and op == "HARVEST":
                        first_harvest_opp = (si, day, hour)
                    if ai == our_ai and first_harvest_us is None and op == "HARVEST":
                        first_harvest_us = (si, day, hour)
                
                # Hires
                for m in a.get("market", []):
                    if m and m[0] == "HIRE":
                        if ai == opp_ai and first_hire_opp is None:
                            first_hire_opp = (si, day, hour)
                        if ai == our_ai and first_hire_us is None:
                            first_hire_us = (si, day, hour)
                    if m and m[0] == "SELL" and m[1] == "STRAWBERRY":
                        if ai == opp_ai and first_straw_opp is None:
                            first_straw_opp = (si, day, hour, m[2])
                        if ai == our_ai and first_straw_us is None:
                            first_straw_us = (si, day, hour, m[2])
        
        rev_opp[si] = cum_o
        rev_us[si] = cum_u
    
    # Find divergence: when gap first exceeds thresholds
    diverge_1k = diverge_5k = diverge_20k = None
    for si in range(len(steps)):
        gap = rev_opp[si] - rev_us[si]
        day = steps[si][0].get("observation", {}).get("day", 0)
        hour = steps[si][0].get("observation", {}).get("hour", 0)
        if diverge_1k is None and gap >= 1000:
            diverge_1k = (si, day, hour, gap, rev_opp[si], rev_us[si])
        if diverge_5k is None and gap >= 5000:
            diverge_5k = (si, day, hour, gap, rev_opp[si], rev_us[si])
        if diverge_20k is None and gap >= 20000:
            diverge_20k = (si, day, hour, gap, rev_opp[si], rev_us[si])
    
    # Water actions per day
    water_by_day_opp = defaultdict(int)
    water_by_day_us = defaultdict(int)
    for step_idx, day, hour, op, detail in actions_opp:
        if op == "WATER": water_by_day_opp[day] += 1
    for step_idx, day, hour, op, detail in actions_us:
        if op == "WATER": water_by_day_us[day] += 1
    
    # Plant composition
    plants_opp = Counter(); plants_us = Counter()
    for step_idx, day, hour, op, detail in actions_opp:
        if op == "PLANT": plants_opp[detail] += 1
    for step_idx, day, hour, op, detail in actions_us:
        if op == "PLANT": plants_us[detail] += 1
    
    return {
        "eid": eid, "teams": teams,
        "final_opp": steps[-1][opp_ai].get("reward", 0),
        "final_us": steps[-1][our_ai].get("reward", 0),
        "rev_opp": rev_opp[-1], "rev_us": rev_us[-1],
        "diverge_1k": diverge_1k, "diverge_5k": diverge_5k, "diverge_20k": diverge_20k,
        "first_events": {
            "opp_plant": first_plant_opp, "us_plant": first_plant_us,
            "opp_water": first_water_opp, "us_water": first_water_us,
            "opp_harvest": first_harvest_opp, "us_harvest": first_harvest_us,
            "opp_sell": first_sell_opp, "us_sell": first_sell_us,
            "opp_hire": first_hire_opp, "us_hire": first_hire_us,
            "opp_straw": first_straw_opp, "us_straw": first_straw_us,
        },
        "water_by_day_opp": dict(water_by_day_opp),
        "water_by_day_us": dict(water_by_day_us),
        "plants_opp": dict(plants_opp), "plants_us": dict(plants_us),
    }

# Analyze all 3 loss episodes
files = [
    r"C:\Users\rtl\Documents\Github\Kaggriculture\perdi\91078768.json",
    r"C:\Users\rtl\Documents\Github\Kaggriculture\perdi\91080527.json",
    r"C:\Users\rtl\Documents\Github\Kaggriculture\perdi\91081413.json",
]

for fp in files:
    r = analyze_divergence(fp)
    print(f"\n=== Episode {r['eid']} ===")
    print(f"  {r['teams'][0]} (opp) vs {r['teams'][1]} (us)")
    print(f"  Final: Opp={r['final_opp']:.0f} Us={r['final_us']:.0f} Ratio={r['final_opp']/max(r['final_us'],1):.1f}x")
    print(f"  Revenue: Opp={r['rev_opp']:.0f} Us={r['rev_us']:.0f}")
    
    # First events
    fe = r["first_events"]
    print(f"\n  FIRST EVENTS:")
    print(f"    PLANT:     Opp D{fe['opp_plant'][1]}H{fe['opp_plant'][2]} ({fe['opp_plant'][3]}) | Us D{fe['us_plant'][1]}H{fe['us_plant'][2]} ({fe['us_plant'][3]})")
    print(f"    WATER:     Opp D{fe['opp_water'][1]}H{fe['opp_water'][2]} | Us D{fe['us_water'][1]}H{fe['us_water'][2]}")
    print(f"    HARVEST:   Opp D{fe['opp_harvest'][1]}H{fe['opp_harvest'][2]} | Us D{fe['us_harvest'][1]}H{fe['us_harvest'][2]}")
    print(f"    SELL:      Opp D{fe['opp_sell'][1]}H{fe['opp_sell'][2]} ({fe['opp_sell'][3]}) | Us D{fe['us_sell'][1]}H{fe['us_sell'][2]} ({fe['us_sell'][3]})")
    print(f"    HIRE:      Opp D{fe['opp_hire'][1]}H{fe['opp_hire'][2]} | Us D{fe['us_hire'][1]}H{fe['us_hire'][2]}")
    if fe["opp_straw"]: print(f"    STRAWBERRY: Opp D{fe['opp_straw'][1]}H{fe['opp_straw'][2]} qty={fe['opp_straw'][3]}")
    if fe["us_straw"]: print(f"    STRAWBERRY: Us D{fe['us_straw'][1]}H{fe['us_straw'][2]} qty={fe['us_straw'][3]}")
    
    # Divergence points
    print(f"\n  DIVERGENCE POINTS:")
    if r["diverge_1k"]:
        si, d, h, gap, rev_o, rev_u = r["diverge_1k"]
        print(f"    Gap > 1k at Step {si} (D{d}H{h}): Opp={rev_o:.0f} Us={rev_u:.0f} Gap={gap:.0f}")
    if r["diverge_5k"]:
        si, d, h, gap, rev_o, rev_u = r["diverge_5k"]
        print(f"    Gap > 5k at Step {si} (D{d}H{h}): Opp={rev_o:.0f} Us={rev_u:.0f} Gap={gap:.0f}")
    if r["diverge_20k"]:
        si, d, h, gap, rev_o, rev_u = r["diverge_20k"]
        print(f"    Gap > 20k at Step {si} (D{d}H{h}): Opp={rev_o:.0f} Us={rev_u:.0f} Gap={gap:.0f}")
    
    # Water per day
    print(f"\n  WATER PER DAY:")
    all_days = sorted(set(list(r["water_by_day_opp"].keys()) + list(r["water_by_day_us"].keys())))
    print(f"    Day: " + " ".join(f"{d:>4}" for d in all_days[:10]))
    print(f"    Opp: " + " ".join(f"{r['water_by_day_opp'].get(d,0):>4}" for d in all_days[:10]))
    print(f"    Us:  " + " ".join(f"{r['water_by_day_us'].get(d,0):>4}" for d in all_days[:10]))
    
    # Plant composition
    print(f"\n  PLANT COMPOSITION:")
    print(f"    Opp: {r['plants_opp']}")
    print(f"    Us:  {r['plants_us']}")
