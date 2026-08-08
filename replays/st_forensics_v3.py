"""
Strategic/Tactical Forensics v3 — Winner vs Loser analysis.
Gates 1-10: farm composition, capital, timing, cycles, RPA, trajectory.
"""
import json, os, glob, statistics, math, csv
from collections import defaultdict

CROPS = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250}
PRODUCTIVE = {"HARVEST", "PLANT", "WATER", "FEED", "CARE", "PLACE", "COLLECT_FERTILIZER", "BUILD_PASTURE"}

def analyze_one(filepath):
    with open(filepath) as f: data = json.load(f)
    steps = data["steps"]
    info = data.get("info", {})
    eid = info.get("EpisodeId", os.path.basename(filepath))
    teams = info.get("TeamNames", [f"A{i}" for i in range(2)])
    results = []
    for ai in range(len(steps[0])):
        rev_ts = [0.0] * len(steps)
        cum = 0.0
        action_log = []
        sell_events = []
        buy_events = []
        daily = []
        seen_days = set()
        
        for si, step in enumerate(steps):
            a = step[ai]
            act = a.get("action", {})
            obs = a.get("observation", {})
            prev_obs = steps[si - 1][ai].get("observation", {}) if si > 0 else obs
            day = obs.get("day", 0)
            hour = obs.get("hour", 0)
            prices = obs.get("market", {}).get("prices", {}) if obs else {}
            
            # Revenue
            if isinstance(act, dict):
                for m in act.get("market", []):
                    if m and m[0] == "SELL" and len(m) >= 3:
                        rev = m[2] * prices.get(m[1], 0)
                        cum += rev
                        sell_events.append((si, day, hour, m[1], m[2], rev, prices.get(m[1], 0)))
                    elif m and m[0] in ("BUY_ANIMAL", "BUY_SEED", "BUY_PRODUCT", "BUY_LAND", "HIRE"):
                        if m[0] == "HIRE": buy_events.append((si, day, "HIRE", "HIRE", 1))
                        elif m[0] == "BUY_LAND": buy_events.append((si, day, "LAND", "LAND", 1))
                        elif len(m) >= 3: buy_events.append((si, day, m[0], m[1], m[2]))
            
            rev_ts[si] = cum
            
            # Worker actions
            if isinstance(act, dict):
                for wa in [act.get("farmer", ["PASS"])] + act.get("hands", []):
                    if wa and wa[0] in PRODUCTIVE | {"SELL", "PICKUP", "DROP"}:
                        action_log.append({"step": si, "action": wa[0]})
            
            # Daily snapshot at hour 23 (end of prev day) or hour 0 (start)
            if hour == 23 and day not in seen_days:
                seen_days.add(day)
                prev_farms = prev_obs.get("farms", [])
                prev_farm = prev_farms[ai] if prev_farms and ai < len(prev_farms) and isinstance(prev_farms[ai], dict) else {}
                prev_private = prev_obs.get("private", {}) if prev_obs else {}
                
                # Count animals
                cows = sheep = goose = pastures = 0
                crops = defaultdict(int)
                for row in prev_farm.get("tiles", []):
                    for t in (row if isinstance(row, list) else []):
                        if isinstance(t, dict):
                            if t.get("kind") == "PASTURE":
                                pastures += 1
                                a = t.get("animal")
                                if a == "COW": cows += 1
                                elif a == "SHEEP": sheep += 1
                                elif a == "GOOSE": goose += 1
                            elif t.get("kind") == "PLANT":
                                crops[t.get("crop", "?")] += 1
                
                daily.append({
                    "day": day, "step": si,
                    "cows": cows, "sheep": sheep, "goose": goose, "pastures": pastures,
                    "crops": dict(crops),
                    "money": prev_farm.get("money", 0),
                    "hands": len(prev_farm.get("hands", [])),
                    "cumulative_rev": cum,
                })
        
        # Second pass: compute DS for each action
        for a in action_log:
            si = a["step"]; n = len(steps)
            a["ds5"] = rev_ts[min(si + 5, n - 1)] - rev_ts[si]
            a["ds20"] = rev_ts[min(si + 20, n - 1)] - rev_ts[si]
        
        final_score = steps[-1][ai].get("reward", 0)
        final_rev = rev_ts[-1]
        
        # Action breakdown
        by_act = defaultdict(lambda: {"n": 0, "ds5": [], "ds20": []})
        for a in action_log:
            by_act[a["action"]]["n"] += 1
            by_act[a["action"]]["ds5"].append(a["ds5"])
            by_act[a["action"]]["ds20"].append(a["ds20"])
        
        action_ds = {}
        for op, d in by_act.items():
            if d["n"] > 0:
                action_ds[op] = {"count": d["n"], "avg_ds5": statistics.mean(d["ds5"]), "avg_ds20": statistics.mean(d["ds20"])}
        
        prod = sum(v["n"] for op, v in by_act.items() if op in PRODUCTIVE)
        rpa = final_rev / prod if prod else 0
        
        # Animal vs crop revenue
        anim_rev = sum(s[5] for s in sell_events if s[3] in ("MILK", "WOOL", "EGG"))
        crop_rev = sum(s[5] for s in sell_events if s[3] in CROPS)
        
        results.append({
            "eid": eid, "team": teams[ai] if ai < len(teams) else f"A{ai}",
            "ai": ai, "seed": info.get("seed", 0),
            "score": final_score, "revenue": final_rev, "rpa": rpa,
            "prod": prod, "total_actions": len(action_log),
            "sells": len(sell_events), "buys": len(buy_events),
            "anim_rev": anim_rev, "crop_rev": crop_rev,
            "anim_pct": anim_rev / final_rev * 100 if final_rev else 0,
            "action_ds": action_ds, "daily": daily,
            "sell_events": sell_events, "buy_events": buy_events,
        })
    return results

def run():
    files = list(set(glob.glob("replays/ep_*.json") + glob.glob("replays/sample_episode.json")))
    files = [f for f in files if os.path.exists(f) and "manifest" not in f and "dataset" not in f]
    print(f"Files: {len(files)}")
    
    wins, loss = [], []
    for fp in sorted(files):
        try:
            r = analyze_one(fp)
            if len(r) == 2:
                if r[0]["score"] > r[1]["score"]: wins.append(r[0]); loss.append(r[1])
                else: wins.append(r[1]); loss.append(r[0])
            print(f"  {os.path.basename(fp)}: [{r[0]['team'][:15]}={r[0]['score']:.0f}, {r[1]['team'][:15]}={r[1]['score']:.0f}]")
        except Exception as e:
            print(f"  {os.path.basename(fp)}: ERROR {e}")
    
    n = len(wins)
    if n == 0: print("No data"); return
    def mn(xs): return statistics.mean(xs) if xs else 0
    
    # === Composition ===
    print(f"\nGATE 1: FARM COMPOSITION (n={n})")
    for day_tgt in [0, 5, 10, 15, 20, 25, 29]:
        wc = mn([next((d["cows"] for d in r["daily"] if d["day"] >= day_tgt), r["daily"][-1]["cows"] if r["daily"] else 0) for r in wins])
        ws = mn([next((d["sheep"] for d in r["daily"] if d["day"] >= day_tgt), r["daily"][-1]["sheep"] if r["daily"] else 0) for r in wins])
        wm = mn([next((d["money"] for d in r["daily"] if d["day"] >= day_tgt), r["daily"][-1]["money"] if r["daily"] else 0) for r in wins])
        lc = mn([next((d["cows"] for d in r["daily"] if d["day"] >= day_tgt), r["daily"][-1]["cows"] if r["daily"] else 0) for r in loss])
        ls = mn([next((d["sheep"] for d in r["daily"] if d["day"] >= day_tgt), r["daily"][-1]["sheep"] if r["daily"] else 0) for r in loss])
        lm = mn([next((d["money"] for d in r["daily"] if d["day"] >= day_tgt), r["daily"][-1]["money"] if r["daily"] else 0) for r in loss])
        print(f"  D{day_tgt:>2}: W cows={wc:.0f} sheep={ws:.0f} money={wm:.0f} | L cows={lc:.0f} sheep={ls:.0f} money={lm:.0f}")
    
    # Save composition CSV
    with open("replays/composition_delta_by_day.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["day","w_cows","w_sheep","w_money","l_cows","l_sheep","l_money"])
        for dt in range(0, 30):
            wc = mn([next((d["cows"] for d in r["daily"] if d["day"] >= dt), r["daily"][-1]["cows"] if r["daily"] else 0) for r in wins])
            ws = mn([next((d["sheep"] for d in r["daily"] if d["day"] >= dt), r["daily"][-1]["sheep"] if r["daily"] else 0) for r in wins])
            wm = mn([next((d["money"] for d in r["daily"] if d["day"] >= dt), r["daily"][-1]["money"] if r["daily"] else 0) for r in wins])
            lc = mn([next((d["cows"] for d in r["daily"] if d["day"] >= dt), r["daily"][-1]["cows"] if r["daily"] else 0) for r in loss])
            ls = mn([next((d["sheep"] for d in r["daily"] if d["day"] >= dt), r["daily"][-1]["sheep"] if r["daily"] else 0) for r in loss])
            lm = mn([next((d["money"] for d in r["daily"] if d["day"] >= dt), r["daily"][-1]["money"] if r["daily"] else 0) for r in loss])
            w.writerow([dt, round(wc, 1), round(ws, 1), round(wm, 0), round(lc, 1), round(ls, 1), round(lm, 0)])
    
    # === Capital ===
    print(f"\nGATE 2: CAPITAL ALLOCATION")
    for lbl, grp in [("W", wins), ("L", loss)]:
        cows = sum(1 for r in grp for b in r["buy_events"] if b[2] == "BUY_ANIMAL" and b[3] == "COW")
        sheep = sum(1 for r in grp for b in r["buy_events"] if b[2] == "BUY_ANIMAL" and b[3] == "SHEEP")
        hires = sum(1 for r in grp for b in r["buy_events"] if b[2] == "HIRE")
        land = sum(1 for r in grp for b in r["buy_events"] if b[2] == "LAND")
        print(f"  {lbl}: cows={cows} sheep={sheep} hires={hires} land={land}")
    
    # === Timing ===
    print(f"\nGATE 3: TACTICAL TIMING — Per-Action DS5")
    ops = ["FEED", "CARE", "WATER", "PLANT", "HARVEST", "PICKUP", "DROP"]
    for op in ops:
        wv = [r["action_ds"][op]["avg_ds5"] for r in wins if op in r["action_ds"]]
        lv = [r["action_ds"][op]["avg_ds5"] for r in loss if op in r["action_ds"]]
        wct = sum(r["action_ds"].get(op, {}).get("count", 0) for r in wins)
        lct = sum(r["action_ds"].get(op, {}).get("count", 0) for r in loss)
        if wv and lv:
            print(f"  {op:<8}: W={mn(wv):.0f} L={mn(lv):.0f} ratio={mn(wv)/max(mn(lv),0.1):.2f} (W:{wct} L:{lct})")
    
    # === Cycles ===
    print(f"\nGATE 4: ECONOMIC CYCLES")
    for lbl, grp in [("W", wins), ("L", loss)]:
        s = mn([r["sells"] for r in grp])
        r = mn([r["revenue"] / max(r["sells"], 1) for r in grp])
        print(f"  {lbl}: sells={s:.0f} rev/sell={r:.0f}")
    
    # === RPA ===
    print(f"\nGATE 6: RPA DECOMPOSITION")
    print(f"  OVERALL: W={mn([r['rpa'] for r in wins]):.1f} L={mn([r['rpa'] for r in loss]):.1f}")
    for op in ops:
        wv = [r["action_ds"][op]["avg_ds20"] for r in wins if op in r["action_ds"]]
        lv = [r["action_ds"][op]["avg_ds20"] for r in loss if op in r["action_ds"]]
        if wv and lv: print(f"  {op:<8}: W={mn(wv):.0f} L={mn(lv):.0f}")
    
    # === Trajectory ===
    print(f"\nGATE 8: REVENUE TRAJECTORY")
    for dt in [0, 5, 10, 15, 20, 25, 29]:
        wv = mn([next((d["cumulative_rev"] for d in r["daily"] if d["day"] >= dt), r["daily"][-1]["cumulative_rev"] if r["daily"] else 0) for r in wins])
        lv = mn([next((d["cumulative_rev"] for d in r["daily"] if d["day"] >= dt), r["daily"][-1]["cumulative_rev"] if r["daily"] else 0) for r in loss])
        print(f"  D{dt:>2}: W={wv:.0f} L={lv:.0f} delta={wv-lv:+.0f}")
    
    # === Animal vs Crop ===
    print(f"\nGATE 9: ANIMAL vs CROP REVENUE")
    for lbl, grp in [("W", wins), ("L", loss)]:
        ap = mn([r["anim_pct"] for r in grp])
        print(f"  {lbl}: animal={ap:.1f}%")
    
    # === GATE 10: Minimum Experiment ===
    print(f"\nGATE 10: MINIMUM NEXT EXPERIMENT")
    gaps = {}
    for op in ops:
        wv = [r["action_ds"][op]["avg_ds5"] for r in wins if op in r["action_ds"]]
        lv = [r["action_ds"][op]["avg_ds5"] for r in loss if op in r["action_ds"]]
        if wv and lv: gaps[op] = mn(wv) - mn(lv)
    best = max(gaps, key=lambda k: abs(gaps[k])) if gaps else "N/A"
    print(f"  Largest DS5 gap: {best} ({gaps.get(best, 0):.0f})")
    print(f"  HYPOTHESIS: {best} timing/selection drives winner edge")
    
    # Save action CSV
    with open("replays/action_downstream_value.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["team","action","count","avg_ds5","avg_ds20"])
        for r in wins: 
            for op, d in r["action_ds"].items(): w.writerow([r["team"][:20], op, d["count"], d["avg_ds5"], d["avg_ds20"]])
        for r in loss: 
            for op, d in r["action_ds"].items(): w.writerow([r["team"][:20], op, d["count"], d["avg_ds5"], d["avg_ds20"]])
    
    # Save cycles CSV
    with open("replays/economic_cycles.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["team","sells","revenue","rev_per_sell","prod","rpa"])
        for r in wins: w.writerow([r["team"][:20], r["sells"], r["revenue"], r["revenue"]/max(r["sells"],1), r["prod"], r["rpa"]])
        for r in loss: w.writerow([r["team"][:20], r["sells"], r["revenue"], r["revenue"]/max(r["sells"],1), r["prod"], r["rpa"]])
    
    # Save dataset
    with open("replays/strategic_tactical_dataset.json", "w") as f:
        json.dump({"n": n, "winners": [{k: v for k, v in r.items() if k not in ("daily","sell_events","buy_events","action_ds")} for r in wins], "losers": [{k: v for k, v in r.items() if k not in ("daily","sell_events","buy_events","action_ds")} for r in loss]}, f, indent=2, default=str)
    
    print(f"\nOutputs saved.")

if __name__ == "__main__":
    run()
