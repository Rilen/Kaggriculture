"""
Strategic/Tactical Forensics — Comprehensive winner vs loser analysis.
Extracts farm composition, capital allocation, action timing, economic cycles.
Outputs: CSV+JSON+MD report.
"""
import json, os, glob, statistics, math, csv
from collections import defaultdict

CROPS = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250}
ANIMALS = {"COW": 400, "SHEEP": 500, "GOOSE": 300}
ANIMAL_PRODUCTS = {"COW": "MILK", "SHEEP": "WOOL", "GOOSE": "EGG"}
PRODUCT_PRICES = {"MILK": 160, "WOOL": 200, "EGG": 50}
PRODUCTIVE = {"HARVEST", "PLANT", "WATER", "FEED", "CARE", "PLACE", "COLLECT_FERTILIZER", "BUILD_PASTURE"}

def analyze_episode_full(filepath):
    with open(filepath) as f:
        data = json.load(f)
    steps = data["steps"]
    info = data.get("info", {})
    eid = info.get("EpisodeId", os.path.basename(filepath))
    teams = info.get("TeamNames", [f"A{i}" for i in range(2)])
    n_agents = len(steps[0])
    
    results = []
    for ai in range(n_agents):
        # Daily snapshots
        daily = []  # List of per-day dicts
        rev_ts = [0.0] * len(steps)  # cumulative revenue
        cum = 0.0
        action_log = []  # per-action records
        harvest_events = []
        sell_events = []
        purchase_events = []
        
        for si, step in enumerate(steps):
            a = step[ai]
            act = a.get("action", {})
            obs = a.get("observation", {})
            
            # Use PREVIOUS step's observation for pre-action state
            prev_step = steps[si - 1] if si > 0 else step
            prev_obs = prev_step[ai].get("observation", {})
            day = prev_obs.get("day", 0)
            hour = prev_obs.get("hour", 0)
            
            prices = obs.get("market", {}).get("prices", {}) if obs else {}
            prev_prices = prev_obs.get("market", {}).get("prices", {}) if prev_obs else {}
            prev_farms = prev_obs.get("farms", [])
            prev_farm = prev_farms[ai] if prev_farms and ai < len(prev_farms) and isinstance(prev_farms[ai], dict) else {}
            prev_private = prev_obs.get("private", {}) if prev_obs else {}
            prev_shed = prev_private.get("shed", {}) if isinstance(prev_private, dict) else {}
            prev_seeds = prev_private.get("seeds", {}) if isinstance(prev_private, dict) else {}
            prev_invs = prev_private.get("inventories", []) if isinstance(prev_private, dict) else []
            
            # Revenue tracking
            if isinstance(act, dict):
                for m in act.get("market", []):
                    if not m: continue
                    op_m = m[0]
                    if op_m == "SELL" and len(m) >= 3:
                        rev = m[2] * prices.get(m[1], 0)
                        cum += rev
                        sell_events.append((si, day, hour, m[1], m[2], rev))
                    elif op_m in ("BUY_ANIMAL", "BUY_SEED", "BUY_PRODUCT", "BUY_LAND", "HIRE"):
                        if op_m == "HIRE":
                            purchase_events.append((si, day, hour, op_m, "HIRE", 1))
                        elif op_m == "BUY_LAND":
                            purchase_events.append((si, day, hour, op_m, "LAND", 1))
                        elif len(m) >= 3:
                            purchase_events.append((si, day, hour, op_m, m[1], m[2]))
            
            revenue_ts_val = cum
            rev_ts[si] = revenue_ts_val
            
            # Daily snapshot: take state at step 0 (day 0, hour 0) of each day's first observation
            # Use obs (current observation) which shows post-action state
            obs_day = obs.get("day", -1)
            obs_hour = obs.get("hour", -1)
            prev_obs_day = prev_obs.get("day", -1)
            
            if prev_obs_day != obs_day and obs_hour == 0:
                farm_snap = prev_farm  # Use pre-action state at day boundary
            else:
                farm_snap = None
            
            if farm_snap:
                cow_n = sheep_n = goose_n = 0
                pastures = 0
                for row in prev_farm.get("tiles", []):
                    for t in (row if isinstance(row, list) else []):
                        if isinstance(t, dict) and t.get("kind") == "PASTURE":
                            pastures += 1
                            a = t.get("animal")
                            if a == "COW": cow_n += 1
                            elif a == "SHEEP": sheep_n += 1
                            elif a == "GOOSE": goose_n += 1
                
                # Count crops by type
                crop_counts = defaultdict(int)
                crop_ages = defaultdict(list)
                for row in prev_farm.get("tiles", []):
                    for t in (row if isinstance(row, list) else []):
                        if isinstance(t, dict) and t.get("kind") == "PLANT":
                            c = t.get("crop", "")
                            crop_counts[c] += 1
                            crop_ages[c].append(day - t.get("planted_day", day))
                
                # Money
                money = prev_farm.get("money", 0)
                hands = len(prev_farm.get("hands", []))
                unlocked = len(prev_farm.get("unlocked_quadrants", ["NW"]))
                
                # Shed inventory
                shed_wheat = prev_shed.get("WHEAT", 0)
                shed_milk = prev_shed.get("MILK", 0)
                shed_wool = prev_shed.get("WOOL", 0)
                
                snap = {
                    "day": day, "hour": hour, "step": si,
                    "cows": cow_n, "sheep": sheep_n, "goose": goose_n,
                    "pastures": pastures,
                    "crops": dict(crop_counts),
                    "crop_ages": {k: statistics.mean(v) if v else 0 for k, v in crop_ages.items()},
                    "money": money, "hands": hands, "unlocked": unlocked,
                    "shed_wheat": shed_wheat, "shed_milk": shed_milk, "shed_wool": shed_wool,
                    "cumulative_revenue": revenue_ts_val,
                }
                daily.append(snap)
            
            # Per-action records for FEED/CARE/WATER/PLANT/HARVEST
            if isinstance(act, dict):
                farmer_act = act.get("farmer", ["PASS"])
                hands_acts = act.get("hands", [])
                all_worker_acts = [("F", farmer_act)] + [(f"H{hi}", ha) for hi, ha in enumerate(hands_acts)]
                
                for wid_label, wa in all_worker_acts:
                    if not wa: continue
                    op = wa[0]
                    if op in PRODUCTIVE | {"SELL", "PICKUP", "DROP", "DIG"}:
                        action_log.append({
                            "step": si, "day": day, "hour": hour,
                            "action": op, "worker": wid_label,
                        })
        
        # Second pass: compute DS after rev_ts fully populated
        for a in action_log:
            si = a["step"]; n = len(steps)
            a["ds5"] = rev_ts[min(si + 5, n - 1)] - rev_ts[si]
            a["ds20"] = rev_ts[min(si + 20, n - 1)] - rev_ts[si]
        
        # Final score
        final_score = steps[-1][ai].get("reward", 0)
        final_rev = rev_ts[-1]
        
        # Capital metrics
        total_purchases = len(purchase_events)
        
        # Productive actions count
        prod_count = sum(1 for a in action_log if a["action"] in PRODUCTIVE)
        rpa = final_rev / prod_count if prod_count else 0
        
        # Action breakdown with DS
        by_action = defaultdict(lambda: {"count": 0, "ds5": [], "ds20": []})
        for a in action_log:
            op = a["action"]
            by_action[op]["count"] += 1
            by_action[op]["ds5"].append(a["ds5"])
            by_action[op]["ds20"].append(a["ds20"])
        
        action_ds = {}
        for op, d in by_action.items():
            action_ds[op] = {
                "count": d["count"],
                "avg_ds5": statistics.mean(d["ds5"]) if d["ds5"] else 0,
                "avg_ds20": statistics.mean(d["ds20"]) if d["ds20"] else 0,
            }
        
        # Crop vs Animal revenue
        crop_rev = sum(s[5] for s in sell_events if s[3] in CROPS)
        animal_rev = sum(s[5] for s in sell_events if s[3] in ANIMAL_PRODUCTS.values())
        
        # Summary
        r = {
            "episode_id": eid,
            "team": teams[ai] if ai < len(teams) else f"Agent_{ai}",
            "agent_idx": ai,
            "seed": info.get("seed", 0),
            "score": final_score,
            "revenue": final_rev,
            "prod_actions": prod_count,
            "rpa": rpa,
            "crop_rev": crop_rev,
            "animal_rev": animal_rev,
            "animal_rev_pct": animal_rev / final_rev * 100 if final_rev else 0,
            "total_actions": len(action_log),
            "total_sells": len(sell_events),
            "total_purchases": total_purchases,
            "action_ds": action_ds,
            "daily": daily,
            "sell_events": sell_events,
            "purchase_events": purchase_events,
        }
        results.append(r)
    
    return results, eid


def run_full_forensics():
    files = glob.glob("replays/ep_*.json") + glob.glob("replays/sample_episode.json")
    files = list(set(f for f in files if os.path.exists(f) and "manifest" not in f and "dataset" not in f))
    
    print(f"Analyzing {len(files)} episodes...")
    all_winners = []
    all_losers = []
    episodes = []
    
    for fp in sorted(files):
        fname = os.path.basename(fp)
        try:
            ag_results, eid = analyze_episode_full(fp)
            episodes.append((eid, ag_results))
            if len(ag_results) == 2:
                if ag_results[0]["score"] > ag_results[1]["score"]:
                    all_winners.append(ag_results[0]); all_losers.append(ag_results[1])
                else:
                    all_winners.append(ag_results[1]); all_losers.append(ag_results[0])
            print(f"  {fname}: teams={[r['team'][:15] for r in ag_results]}, scores={[r['score'] for r in ag_results]}")
        except Exception as e:
            print(f"  {fname}: ERROR {e}")
    
    n = len(all_winners)
    if n == 0:
        print("No data."); return
    
    def m(xs): return statistics.mean(xs) if xs else 0
    def s(xs): return statistics.stdev(xs) if len(xs)>1 else 0
    
    # ====== GATE 1: Farm Composition ======
    print(f"\n{'='*70}")
    print("GATE 1: FARM COMPOSITION — Day 0, 5, 10, 15, 20, 25, Final")
    print(f"{'='*70}")
    
    composition_rows = []
    for day_target in [0, 5, 10, 15, 20, 25, 29]:
        w_cows, w_sheep, w_money = [], [], []
        l_cows, l_sheep, l_money = [], [], []
        for r in all_winners:
            d = next((x for x in r["daily"] if x["day"] >= day_target), r["daily"][-1] if r["daily"] else None)
            if d:
                w_cows.append(d.get("cows", 0)); w_sheep.append(d.get("sheep", 0)); w_money.append(d.get("money", 0))
        for r in all_losers:
            d = next((x for x in r["daily"] if x["day"] >= day_target), r["daily"][-1] if r["daily"] else None)
            if d:
                l_cows.append(d.get("cows", 0)); l_sheep.append(d.get("sheep", 0)); l_money.append(d.get("money", 0))
        
        row = {
            "day": day_target,
            "w_cows": m(w_cows), "l_cows": m(l_cows),
            "w_sheep": m(w_sheep), "l_sheep": m(l_sheep),
            "w_money": m(w_money), "l_money": m(l_money),
        }
        composition_rows.append(row)
        print(f"  Day {day_target:>2}: W cows={m(w_cows):.0f} sheep={m(w_sheep):.0f} money={m(w_money):.0f} | L cows={m(l_cows):.0f} sheep={m(l_sheep):.0f} money={m(l_money):.0f}")
    
    with open("replays/composition_delta_by_day.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=composition_rows[0].keys())
        w.writeheader(); w.writerows(composition_rows)
    
    # ====== GATE 2: Capital Allocation ======
    print(f"\n{'='*70}")
    print("GATE 2: CAPITAL ALLOCATION")
    print(f"{'='*70}")
    
    w_cow_purchases = sum(1 for r in all_winners for p in r["purchase_events"] if p[3] == "BUY_ANIMAL" and p[4] == "COW")
    l_cow_purchases = sum(1 for r in all_losers for p in r["purchase_events"] if p[3] == "BUY_ANIMAL" and p[4] == "COW")
    w_sheep_purchases = sum(1 for r in all_winners for p in r["purchase_events"] if p[3] == "BUY_ANIMAL" and p[4] == "SHEEP")
    l_sheep_purchases = sum(1 for r in all_losers for p in r["purchase_events"] if p[3] == "BUY_ANIMAL" and p[4] == "SHEEP")
    w_hires = sum(1 for r in all_winners for p in r["purchase_events"] if p[3] == "HIRE")
    l_hires = sum(1 for r in all_losers for p in r["purchase_events"] if p[3] == "HIRE")
    w_land = sum(1 for r in all_winners for p in r["purchase_events"] if p[3] == "BUY_LAND")
    l_land = sum(1 for r in all_losers for p in r["purchase_events"] if p[3] == "BUY_LAND")
    
    print(f"  {'':20} {'Winners':>10} {'Losers':>10}")
    print(f"  {'COW purchases':20} {w_cow_purchases:>10} {l_cow_purchases:>10}")
    print(f"  {'SHEEP purchases':20} {w_sheep_purchases:>10} {l_sheep_purchases:>10}")
    print(f"  {'HIREs':20} {w_hires:>10} {l_hires:>10}")
    print(f"  {'BUY_LAND':20} {w_land:>10} {l_land:>10}")
    
    # ====== GATE 3: Tactical Timing ======
    print(f"\n{'='*70}")
    print("GATE 3: TACTICAL TIMING — Per-Action Downstream Revenue")
    print(f"{'='*70}")
    
    action_types = ["FEED", "CARE", "WATER", "PLANT", "HARVEST", "PICKUP", "DROP", "SELL"]
    print(f"  {'Action':<10} {'W DS5':>10} {'L DS5':>10} {'W N':>6} {'L N':>6} {'W/L':>8}")
    for op in action_types:
        w_ds5 = [r["action_ds"].get(op, {}).get("avg_ds5", 0) for r in all_winners if r["action_ds"].get(op)]
        l_ds5 = [r["action_ds"].get(op, {}).get("avg_ds5", 0) for r in all_losers if r["action_ds"].get(op)]
        w_ct = sum(r["action_ds"].get(op, {}).get("count", 0) for r in all_winners)
        l_ct = sum(r["action_ds"].get(op, {}).get("count", 0) for r in all_losers)
        if not w_ds5 and not l_ds5: continue
        wm, lm = m(w_ds5), m(l_ds5)
        ratio = wm/lm if lm else 1.0
        print(f"  {op:<10} {wm:>10.0f} {lm:>10.0f} {w_ct:>6} {l_ct:>6} {ratio:>7.2f}x")
    
    # ====== GATE 4: Economic Cycles ======
    print(f"\n{'='*70}")
    print("GATE 4: ECONOMIC CYCLES")
    print(f"{'='*70}")
    
    # Approximate cycles: sell events per agent
    for label, grp in [("Winners", all_winners), ("Losers", all_losers)]:
        sell_counts = [r["total_sells"] for r in grp]
        revs = [r["revenue"] for r in grp]
        rev_per_sell = [r/max(s,1) for r,s in zip(revs, sell_counts)]
        print(f"  {label}: avg sells={m(sell_counts):.0f}, rev/sell={m(rev_per_sell):.0f}, prod_acts={m([r['prod_actions'] for r in grp]):.0f}")
    
    with open("replays/economic_cycles.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["team","sells","revenue","rev_per_sell","prod_actions","rpa"])
        for r in all_winners:
            w.writerow([r["team"], r["total_sells"], r["revenue"], r["revenue"]/max(r["total_sells"],1), r["prod_actions"], r["rpa"]])
        for r in all_losers:
            w.writerow([r["team"], r["total_sells"], r["revenue"], r["revenue"]/max(r["total_sells"],1), r["prod_actions"], r["rpa"]])
    
    # ====== GATE 5 & 6: RPA Decomposition ======
    print(f"\n{'='*70}")
    print("GATE 6: RPA DECOMPOSITION")
    print(f"{'='*70}")
    
    rpa_rows = []
    for op in action_types + ["OVERALL"]:
        w_rpas, l_rpas = [], []
        if op == "OVERALL":
            w_rpas = [r["rpa"] for r in all_winners]
            l_rpas = [r["rpa"] for r in all_losers]
        else:
            for r in all_winners:
                d = r["action_ds"].get(op)
                if d and d["count"] > 10:
                    w_rpas.append(d["avg_ds20"])
            for r in all_losers:
                d = r["action_ds"].get(op)
                if d and d["count"] > 10:
                    l_rpas.append(d["avg_ds20"])
        if w_rpas and l_rpas:
            print(f"  {op:<10}: W={m(w_rpas):.0f} L={m(l_rpas):.0f} ratio={m(w_rpas)/max(m(l_rpas),1):.2f}")
            rpa_rows.append({"action": op, "w_rpa": m(w_rpas), "l_rpa": m(l_rpas)})
    
    # ====== GATE 8: Trajectory ======
    print(f"\n{'='*70}")
    print("GATE 8: TRAJECTORY — Revenue and Animal% by Day")
    print(f"{'='*70}")
    
    for day in [0, 5, 10, 15, 20, 25, 29]:
        w_revs = [r["daily"][min(day, len(r["daily"])-1)]["cumulative_revenue"] for r in all_winners if r["daily"]]
        l_revs = [r["daily"][min(day, len(r["daily"])-1)]["cumulative_revenue"] for r in all_losers if r["daily"]]
        if w_revs and l_revs:
            print(f"  Day {day:>2}: W rev={m(w_revs):.0f} L rev={m(l_revs):.0f} delta={m(w_revs)-m(l_revs):+.0f}")
    
    # ====== ANIMAL vs CROP REVENUE ======
    print(f"\n{'='*70}")
    print("ANIMAL vs CROP REVENUE SPLIT")
    print(f"{'='*70}")
    for label, grp in [("Winners", all_winners), ("Losers", all_losers)]:
        animal_pct = m([r["animal_rev_pct"] for r in grp])
        print(f"  {label}: animal={animal_pct:.1f}% of revenue")
    
    # ====== GATE 10: Minimum Next Experiment ======
    print(f"\n{'='*70}")
    print("GATE 10: MINIMUM NEXT EXPERIMENT")
    print(f"{'='*70}")
    
    # Find the action with the LARGEST winner/loser DS5 gap
    gaps = {}
    for op in action_types:
        w_ds5 = [r["action_ds"].get(op, {}).get("avg_ds5", 0) for r in all_winners if r["action_ds"].get(op)]
        l_ds5 = [r["action_ds"].get(op, {}).get("avg_ds5", 0) for r in all_losers if r["action_ds"].get(op)]
        if w_ds5 and l_ds5:
            gaps[op] = m(w_ds5) - m(l_ds5)
    
    biggest_gap_op = max(gaps, key=lambda k: gaps[k]) if gaps else "NONE"
    print(f"  Largest winner/loser DS5 gap: {biggest_gap_op} ({gaps.get(biggest_gap_op, 0):.0f})")
    print(f"  HYPOTHESIS: Tactical timing of {biggest_gap_op} drives winner advantage")
    print(f"  MINIMAL TEST: Modify V17.3 {biggest_gap_op} target selection to prioritize")
    print(f"                highest-yield animals/crops (not just nearest)")
    
    # Save dataset
    dataset = {
        "n_episodes": n,
        "winners": [{k: str(v) if isinstance(v, dict) else v for k, v in r.items() if k not in ("daily", "sell_events", "purchase_events", "action_ds")} for r in all_winners],
        "losers": [{k: str(v) if isinstance(v, dict) else v for k, v in r.items() if k not in ("daily", "sell_events", "purchase_events", "action_ds")} for r in all_losers],
    }
    with open("replays/strategic_tactical_dataset.json", "w") as f:
        json.dump(dataset, f, indent=2, default=str)
    
    # Action downstream CSV
    with open("replays/action_downstream_value.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["episode","team","action","count","avg_ds5","avg_ds20"])
        for r in all_winners + all_losers:
            for op, d in r["action_ds"].items():
                w.writerow([r["episode_id"], r["team"][:20], op, d["count"], d["avg_ds5"], d["avg_ds20"]])
    
    print(f"\nFiles written: composition_delta_by_day.csv, economic_cycles.csv, action_downstream_value.csv, strategic_tactical_dataset.json")
    
    return all_winners, all_losers


if __name__ == "__main__":
    run_full_forensics()
