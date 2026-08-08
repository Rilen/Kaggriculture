"""
Opponent Strategy Deep-Dive — all 19 perdi/ episodes.
Extract farm trajectories, buy/sell timing, worker count evolution,
crop vs animal balance, and strategic timing patterns.
"""
import json, glob, statistics
from collections import Counter, defaultdict

files = sorted(glob.glob(r"C:\Users\rtl\Documents\Github\Kaggriculture\perdi\*.json"))
print(f"=== OPPONENT STRATEGY ANALYSIS ({len(files)} episodes) ===\n")

# Group opponents
opp_groups = defaultdict(list)
for fp in files:
    f = open(fp); d = json.load(f); f.close()
    steps = d["steps"]; info = d["info"]
    teams = info.get("TeamNames", ["?", "?"])
    our_ai = 0 if "Rilen" in teams[0] else 1
    opp_ai = 1 - our_ai
    opp_name = teams[opp_ai]
    eid = info["EpisodeId"]
    
    # Revenue tracking
    rev_ts = [0.0] * len(steps); cum = 0.0
    daily_money = {}
    daily_hands = {}
    daily_cows = {}
    daily_sheep = {}
    daily_crops = {}
    
    act_count = Counter()
    sell_items = Counter()
    sell_rev = 0.0
    buy_events = []
    first_plant = first_water = first_harvest = first_sell = first_care = None
    
    for si, step in enumerate(steps):
        a = step[opp_ai].get("action", {})
        obs = step[opp_ai].get("observation", {})
        prices = obs.get("market", {}).get("prices", {}) if obs else {}
        day = obs.get("day", 0); hour = obs.get("hour", 0)
        farms = obs.get("farms", [])
        farm = farms[opp_ai] if farms and opp_ai < len(farms) and isinstance(farms[opp_ai], dict) else {}
        
        if isinstance(a, dict):
            # Revenue
            for m in a.get("market", []):
                if m and m[0] == "SELL" and len(m) >= 3:
                    rev = m[2] * prices.get(m[1], 0)
                    cum += rev; sell_rev += rev
                    sell_items[m[1]] += m[2]
                if m and m[0] in ("BUY_ANIMAL", "BUY_SEED", "HIRE", "BUY_LAND"):
                    buy_events.append((si, day, hour, m[0], m[1] if len(m) > 1 else "", m[2] if len(m) > 2 else 1))
            
            # Actions
            for wa in [a.get("farmer", [])] + a.get("hands", []):
                if wa: act_count[wa[0]] += 1
            
            # First events
            for wa in [a.get("farmer", [])] + a.get("hands", []):
                if not wa: continue
                if first_plant is None and wa[0] == "PLANT": first_plant = (day, hour, wa[1] if len(wa) > 1 else "")
                if first_water is None and wa[0] == "WATER": first_water = (day, hour)
                if first_harvest is None and wa[0] == "HARVEST": first_harvest = (day, hour)
                if first_care is None and wa[0] == "CARE": first_care = (day, hour)
            for m in a.get("market", []):
                if m and m[0] == "SELL" and first_sell is None: first_sell = (day, hour, m[1] if len(m) > 1 else "")
        
        rev_ts[si] = cum
        
        # Daily snapshot at hour 23
        if hour == 23:
            cows = sheep = goose = 0
            crops = Counter()
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
            daily_money[day] = farm.get("money", 0)
            daily_hands[day] = 1 + len(farm.get("hands", []))
            daily_cows[day] = cows
            daily_sheep[day] = sheep
            daily_crops[day] = dict(crops)
    
    s_opp = steps[-1][opp_ai].get("reward", 0)
    s_us = steps[-1][our_ai].get("reward", 0)
    
    opp_groups[opp_name].append({
        "eid": eid, "score_opp": s_opp, "score_us": s_us,
        "rev": rev_ts[-1], "sell_rev": sell_rev,
        "water": act_count.get("WATER", 0), "plant": act_count.get("PLANT", 0),
        "feed": act_count.get("FEED", 0), "care": act_count.get("CARE", 0),
        "harvest": act_count.get("HARVEST", 0), "fert": act_count.get("FERTILIZE", 0),
        "pass": act_count.get("PASS", 0),
        "sells": dict(sell_items),
        "first_plant": first_plant, "first_water": first_water,
        "first_harvest": first_harvest, "first_sell": first_sell, "first_care": first_care,
        "daily_money": daily_money, "daily_hands": daily_hands,
        "daily_cows": daily_cows, "daily_sheep": daily_sheep, "daily_crops": daily_crops,
    })

# Analyze each opponent
for opp_name, matches in sorted(opp_groups.items(), key=lambda x: -len(x[1])):
    n = len(matches)
    avg_score = statistics.mean([m["score_opp"] for m in matches])
    avg_water = statistics.mean([m["water"] for m in matches])
    avg_plant = statistics.mean([m["plant"] for m in matches])
    avg_feed = statistics.mean([m["feed"] for m in matches])
    avg_care = statistics.mean([m["care"] for m in matches])
    avg_fert = statistics.mean([m["fert"] for m in matches])
    avg_pass = statistics.mean([m["pass"] for m in matches])
    
    # Aggregate sells
    all_sells = Counter()
    for m in matches:
        for item, qty in m["sells"].items():
            all_sells[item] += qty
    
    # First events
    firsts = [(m["first_plant"], m["first_water"], m["first_sell"]) for m in matches if m["first_plant"]]
    
    print(f"\n{'='*70}")
    print(f"OPPONENT: {opp_name} ({n} matches)")
    print(f"{'='*70}")
    print(f"  Avg Score: {avg_score:.0f} | WATER: {avg_water:.0f} | PLANT: {avg_plant:.0f}")
    print(f"  FEED: {avg_feed:.0f} | CARE: {avg_care:.0f} | FERT: {avg_fert:.0f} | PASS: {avg_pass:.0f}")
    print(f"  Sells: {dict(all_sells.most_common(6))}")
    print(f"  First PLANT/WATER/SELL: {firsts}")
    
    # Farm trajectory for first match
    m = matches[0]
    print(f"  Farm trajectory:")
    for d in [0, 5, 10, 15, 20, 25, 29]:
        c = m["daily_cows"].get(d, 0); s = m["daily_sheep"].get(d, 0)
        money = m["daily_money"].get(d, 0); hands = m["daily_hands"].get(d, 0)
        crops = m["daily_crops"].get(d, {})
        print(f"    D{d:>2}: C{c}S{s} H={hands} ${money:.0f} crops={crops}")

# Summary: what strategies beat us most?
print(f"\n{'='*70}")
print(f"STRATEGY CLUSTERS")
print(f"{'='*70}")

# By animal composition
for opp_name, matches in sorted(opp_groups.items(), key=lambda x: -statistics.mean([m["score_opp"] for m in x[1]])):
    avg_cows = statistics.mean([max(m["daily_cows"].values() or [0]) for m in matches])
    avg_sheep = statistics.mean([max(m["daily_sheep"].values() or [0]) for m in matches])
    w = statistics.mean([m["water"] for m in matches])
    p = statistics.mean([m["plant"] for m in matches])
    f = statistics.mean([m["feed"] for m in matches])
    c = statistics.mean([m["care"] for m in matches])
    
    animal_type = "crop-only" if avg_cows + avg_sheep == 0 else "balanced" if avg_cows > 3 and avg_sheep > 3 else "cow-heavy" if avg_cows > avg_sheep * 2 else "sheep-heavy"
    print(f"  {opp_name:<25}: {animal_type:<12} WATER={w:.0f} P/W={w/max(p,1):.1f} FEED={f:.0f} CARE={c:.0f}")
