import json, os
from collections import Counter

files = [
    r"C:\Users\rtl\Documents\Github\Kaggriculture\perdi\91078768.json",
    r"C:\Users\rtl\Documents\Github\Kaggriculture\perdi\91080527.json",
    r"C:\Users\rtl\Documents\Github\Kaggriculture\perdi\91081413.json",
]

for fp in files:
    f = open(fp); d = json.load(f); f.close()
    steps = d["steps"]; info = d["info"]
    eid = info["EpisodeId"]
    teams = info.get("TeamNames", ["?", "?"])
    
    s0 = steps[-1][0].get("reward", 0)
    s1 = steps[-1][1].get("reward", 0)
    
    # Find us (Rilen T. L.) — could be agent 0 or 1
    our_ai = 0 if "Rilen" in (teams[0] if len(teams)>0 else "") else 1
    opp_ai = 1 - our_ai
    
    our_score = steps[-1][our_ai].get("reward", 0)
    opp_score = steps[-1][opp_ai].get("reward", 0)
    
    # Revenue
    rev_opp = 0.0; rev_us = 0.0
    act_opp = Counter(); act_us = Counter()
    sell_opp = Counter(); sell_us = Counter()
    
    for step in steps:
        for ai, counter, sell_ct, rev_ref in [(opp_ai, act_opp, sell_opp, None), (our_ai, act_us, sell_us, None)]:
            a = step[ai].get("action", {})
            obs = step[ai].get("observation", {})
            prices = obs.get("market", {}).get("prices", {}) if obs else {}
            
            if isinstance(a, dict):
                for m in a.get("market", []):
                    if m and m[0] == "SELL" and len(m) >= 3:
                        r = m[2] * prices.get(m[1], 0)
                        if ai == opp_ai: rev_opp += r
                        else: rev_us += r
                        sell_ct[m[1]] += m[2]
                
                for wa in [a.get("farmer", ["PASS"])] + a.get("hands", []):
                    if wa: counter[wa[0]] += 1
    
    # WATER/PLANT/HARVEST
    water_opp = act_opp.get("WATER", 0); water_us = act_us.get("WATER", 0)
    plant_opp = act_opp.get("PLANT", 0); plant_us = act_us.get("PLANT", 0)
    harvest_opp = act_opp.get("HARVEST", 0); harvest_us = act_us.get("HARVEST", 0)
    feed_opp = act_opp.get("FEED", 0); feed_us = act_us.get("FEED", 0)
    care_opp = act_opp.get("CARE", 0); care_us = act_us.get("CARE", 0)
    fert_opp = act_opp.get("FERTILIZE", 0); fert_us = act_us.get("FERTILIZE", 0)
    pass_opp = act_opp.get("PASS", 0); pass_us = act_us.get("PASS", 0)
    
    print(f"=== Episode {eid} ===")
    print(f"  Opponent: {teams[opp_ai]} | Us: {teams[our_ai]}")
    print(f"  Score: Opp={opp_score:.0f} Us={our_score:.0f} Ratio={opp_score/max(our_score,1):.1f}x")
    print(f"  Revenue: Opp={rev_opp:.0f} Us={rev_us:.0f}")
    print(f"  Cost: Opp={rev_opp-opp_score:.0f}({100-opp_score/rev_opp*100:.0f}%) Us={rev_us-our_score:.0f}({100-our_score/max(rev_us,1)*100:.0f}%)")
    print(f"  WATER:  Opp={water_opp} Us={water_us} ({water_opp/max(water_us,1):.0f}x)")
    print(f"  PLANT:  Opp={plant_opp} Us={plant_us}")
    print(f"  HARVEST: Opp={harvest_opp} Us={harvest_us}")
    print(f"  FEED:   Opp={feed_opp} Us={feed_us}")
    print(f"  CARE:   Opp={care_opp} Us={care_us}")
    print(f"  FERTILIZE: Opp={fert_opp} Us={fert_us}")
    print(f"  PASS:   Opp={pass_opp} Us={pass_us}")
    print(f"  Water/plant: Opp={water_opp/max(plant_opp,1):.1f} Us={water_us/max(plant_us,1):.1f}")
    
    # Sell breakdown
    print(f"  Opp sells: {dict(sell_opp.most_common(5))}")
    print(f"  Us sells:  {dict(sell_us.most_common(5))}")
    
    # Final farm
    final_step = steps[-1]
    for ai, label in [(opp_ai, "Opp"), (our_ai, "Us")]:
        obs = final_step[ai].get("observation", {})
        farms = obs.get("farms", [])
        farm = farms[ai] if farms and ai < len(farms) and isinstance(farms[ai], dict) else {}
        cows = sheep = 0; crops = Counter()
        for row in farm.get("tiles", []):
            for t in (row if isinstance(row, list) else []):
                if isinstance(t, dict):
                    if t.get("kind") == "PASTURE":
                        a = t.get("animal")
                        if a == "COW": cows += 1
                        elif a == "SHEEP": sheep += 1
                    elif t.get("kind") == "PLANT":
                        crops[t.get("crop", "?")] += 1
        hands = len(farm.get("hands", []))
        print(f"  {label} farm: cows={cows} sheep={sheep} hands={hands} crops={dict(crops)}")
    print()
