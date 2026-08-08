import json
from collections import Counter
f = open(r"C:\Users\rtl\Documents\Github\Kaggriculture\perdi\91124143.json")
d = json.load(f); f.close()
steps = d["steps"]; info = d["info"]
teams = info["TeamNames"]
our_ai = 0 if "Rilen" in (teams[0] if len(teams) > 0 else "") else 1
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

def farm_snap(ai):
    obs = steps[-1][ai].get("observation", {})
    farms = obs.get("farms", [])
    farm = farms[ai] if farms and ai < len(farms) and isinstance(farms[ai], dict) else {}
    cows = sheep = 0
    crops = Counter()
    for row in farm.get("tiles", []):
        for t in (row if isinstance(row, list) else []):
            if isinstance(t, dict):
                if t.get("kind") == "PASTURE":
                    a = t.get("animal")
                    if a == "COW": cows += 1
                    elif a == "SHEEP": sheep += 1
                elif t.get("kind") == "PLANT":
                    crops[t.get("crop", "?")] += 1
    return dict(cows=cows, sheep=sheep, hands=len(farm.get("hands", [])), crops=dict(crops), money=farm.get("money", 0))

print(f"Episode: {info['EpisodeId']} | Seed: {info.get('seed')}")
print(f"OPP: {teams[opp_ai]} vs US: {teams[our_ai]}")
print(f"Score: OPP={s_opp:.0f} | US={s_us:.0f} | Ratio={s_opp/max(s_us,1):.1f}x")
print(f"Revenue: OPP={rev_opp:.0f} | US={rev_us:.0f}")
print(f"Cost: OPP={rev_opp-s_opp:.0f} ({(rev_opp-s_opp)/rev_opp*100:.0f}%) | US={rev_us-s_us:.0f} ({(rev_us-s_us)/max(rev_us,1)*100:.0f}%)")
print(f"HIRE: OPP={hire_opp} | US={hire_us}")

print(f"\n=== ACTIONS ===")
for op in ["WATER", "PLANT", "FEED", "CARE", "HARVEST", "FERTILIZE", "PASS", "PICKUP", "DROP", "COLLECT_FERTILIZER"]:
    o = act_opp.get(op, 0); u = act_us.get(op, 0)
    print(f"  {op:<18}: OPP={o:>5} US={u:>5}")

wp_opp = act_opp.get("WATER", 0) / max(act_opp.get("PLANT", 0), 1)
wp_us = act_us.get("WATER", 0) / max(act_us.get("PLANT", 0), 1)
print(f"  Water/plant: OPP={wp_opp:.1f} US={wp_us:.1f}")

print(f"\n=== SELLS ===")
print(f"  OPP: {dict(sell_opp.most_common(6))}")
print(f"  US:  {dict(sell_us.most_common(6))}")

fs_opp = farm_snap(opp_ai); fs_us = farm_snap(our_ai)
print(f"\n=== FINAL FARM ===")
print(f"  OPP: cows={fs_opp['cows']} sheep={fs_opp['sheep']} hands={fs_opp['hands']} money={fs_opp['money']:.0f} crops={fs_opp['crops']}")
print(f"  US:  cows={fs_us['cows']} sheep={fs_us['sheep']} hands={fs_us['hands']} money={fs_us['money']:.0f} crops={fs_us['crops']}")

# Early game comparison
print(f"\n=== EARLY GAME (Day 0-2) ===")
for day in range(3):
    for hour in [0, 6, 12, 18]:
        si = day * 24 + hour
        if si >= len(steps): break
        step = steps[si]
        farms = step[0].get("observation", {}).get("farms", [])
        if farms and isinstance(farms[0], dict):
            opp_f = farms[opp_ai] if opp_ai < len(farms) and isinstance(farms[opp_ai], dict) else {}
            us_f = farms[our_ai] if our_ai < len(farms) and isinstance(farms[our_ai], dict) else {}
            print(f"  D{day}H{hour:>2}: OPP money={opp_f.get('money',0):>6} hands={len(opp_f.get('hands',[]))} | US money={us_f.get('money',0):>6} hands={len(us_f.get('hands',[]))}")
