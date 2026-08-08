"""
A.4 CARE TTY Counterfactual Forensics — Gates 0-10.
Tests: "What if CARE was only allowed when TTY < threshold?"
Zero agent changes. Pure observational simulation.
"""
import json, os, glob, statistics, csv
from collections import defaultdict

PRODUCTIVE = {"HARVEST", "PLANT", "WATER", "FEED", "CARE", "PLACE", "COLLECT_FERTILIZER", "BUILD_PASTURE"}
ANIMALS = {"COW": "MILK", "SHEEP": "WOOL", "GOOSE": "EGG"}
PRODUCT_PRICES = {"MILK": 160, "WOOL": 200, "EGG": 50}
CROPS = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250}

def extract_all(filepath):
    """Extract CARE events + full farm state snapshots for counterfactual analysis."""
    with open(filepath) as f: data = json.load(f)
    steps = data["steps"]
    info = data.get("info", {})
    eid = info.get("EpisodeId", os.path.basename(filepath))
    teams = info.get("TeamNames", [f"A{i}" for i in range(2)])
    results = []
    for ai in range(len(steps[0])):
        rev_ts = [0.0] * len(steps); cum = 0.0
        care_log = []
        animal_tracker = defaultdict(lambda: {"events": [], "start_step": None})
        step_snapshots = []  # Per-step snapshot of eligible tasks
        
        for si, step in enumerate(steps):
            a = step[ai]; act = a.get("action", {}); obs = a.get("observation", {})
            prev_obs = steps[si - 1][ai].get("observation", {}) if si > 0 else obs
            
            prices = obs.get("market", {}).get("prices", {}) if obs else {}
            if isinstance(act, dict):
                for m in act.get("market", []):
                    if m and m[0] == "SELL" and len(m) >= 3:
                        cum += m[2] * prices.get(m[1], 0)
            rev_ts[si] = cum
            
            prev_farms = prev_obs.get("farms", [])
            prev_farm = prev_farms[ai] if prev_farms and ai < len(prev_farms) and isinstance(prev_farms[ai], dict) else {}
            prev_tiles = prev_farm.get("tiles", [])
            prev_private = prev_obs.get("private", {}) if prev_obs else {}
            prev_shed = prev_private.get("shed", {}) if isinstance(prev_private, dict) else {}
            prev_seeds = prev_private.get("seeds", {}) if isinstance(prev_private, dict) else {}
            day = prev_obs.get("day", 0); hour = prev_obs.get("hour", 0)
            
            # Worker positions (pre-action)
            worker_positions = [prev_farm.get("farmer", [0, 0])] + (prev_farm.get("hands", []) or [])
            
            # Count eligible tasks at this step (for opportunity analysis)
            task_counts = {"FEED": 0, "CARE": 0, "HARVEST": 0, "WATER": 0, "PLANT": 0}
            for y, row in enumerate(prev_tiles if isinstance(prev_tiles, list) else []):
                if not isinstance(row, list): continue
                for x, t in enumerate(row):
                    if not isinstance(t, dict): continue
                    k = t.get("kind")
                    if k == "PASTURE" and t.get("animal"):
                        if not t.get("fed_today", True) and (prev_shed.get("WHEAT", 0) > 0):
                            task_counts["FEED"] += 1
                        if not t.get("cared_today", True):
                            task_counts["CARE"] += 1
                        if t.get("yield_units", 0) > 0:
                            task_counts["HARVEST"] += 1
                    elif k == "PLANT":
                        if not t.get("watered_today", True):
                            task_counts["WATER"] += 1
                        if t.get("yield_units", 0) > 0 or (day - t.get("planted_day", day)) >= {"WHEAT": 4, "CARROT": 3, "TOMATO": 11, "STRAWBERRY": 16, "MELON": 10}.get(t.get("crop", ""), 99):
                            task_counts["HARVEST"] += 1
                # Empty tiles for PLANT
                if t is None and any(prev_seeds.get(c, 0) > 0 for c in CROPS) and hour <= 20:
                    task_counts["PLANT"] += 1
            
            step_snapshots.append({
                "step": si, "day": day, "hour": hour,
                "task_counts": task_counts,
                "n_workers": 1 + len(prev_farm.get("hands", [])),
            })
            
            if not isinstance(act, dict): continue
            farmer_act = act.get("farmer", ["PASS"]); hands_acts = act.get("hands", [])
            all_wa = [(f"F", farmer_act, worker_positions[0] if worker_positions else [0,0])]
            for hi, ha in enumerate(hands_acts):
                pos = worker_positions[hi + 1] if hi + 1 < len(worker_positions) else [0, 0]
                all_wa.append((f"H{hi}", ha, pos))
            
            for wid, wa, wpos in all_wa:
                if not wa or wa[0] != "CARE": continue
                wx, wy = wpos[0], wpos[1]
                pre_tile = None
                if 0 <= wy < len(prev_tiles) and isinstance(prev_tiles[wy], list) and 0 <= wx < len(prev_tiles[wy]):
                    pre_tile = prev_tiles[wy][wx]
                if not isinstance(pre_tile, dict) or "animal" not in pre_tile: continue
                
                animal = pre_tile["animal"]
                pre_yield = pre_tile.get("yield_units", 0)
                
                # Post-action yield for TTY calculation
                post_tile = None
                post_farms = obs.get("farms", [])
                post_farm = post_farms[ai] if post_farms and ai < len(post_farms) and isinstance(post_farms[ai], dict) else {}
                post_tiles = post_farm.get("tiles", [])
                if 0 <= wy < len(post_tiles) and isinstance(post_tiles[wy], list) and 0 <= wx < len(post_tiles[wy]):
                    post_tile = post_tiles[wy][wx]
                post_yield = post_tile.get("yield_units", 0) if isinstance(post_tile, dict) else 0
                
                # Time to next yield
                tty = 999
                yield_after = 0
                for fs in range(si + 1, min(si + 300, len(steps))):
                    fs_obs = steps[fs][ai].get("observation", {})
                    fs_f = fs_obs.get("farms", [])
                    fs_farm = fs_f[ai] if fs_f and ai < len(fs_f) and isinstance(fs_f[ai], dict) else {}
                    fs_t = fs_farm.get("tiles", [])
                    if 0 <= wy < len(fs_t) and isinstance(fs_t[wy], list) and 0 <= wx < len(fs_t[wy]):
                        ft = fs_t[wy][wx]
                        if isinstance(ft, dict) and ft.get("yield_units", 0) > post_yield:
                            tty = fs - si; yield_after = ft.get("yield_units", 0)
                            break
                        if not isinstance(ft, dict) or "animal" not in ft:
                            tty = fs - si; break
                
                # Track animal lifecycle
                tracker = animal_tracker[(wx, wy)]
                prev_care_steps = [e[0] for e in tracker["events"] if e[1] == "CARE"]
                prev_feed_steps = [e[0] for e in tracker["events"] if e[1] == "FEED"]
                tslc = si - prev_care_steps[-1] if prev_care_steps else 999
                tslf = si - prev_feed_steps[-1] if prev_feed_steps else 999
                
                care_log.append({
                    "step": si, "day": day, "hour": hour, "worker": wid,
                    "animal": animal, "pos": f"{wx},{wy}",
                    "pre_yield": pre_yield, "post_yield": post_yield,
                    "tty": tty, "yield_after": yield_after,
                    "tslc": tslc, "tslf": tslf,
                    "task_counts": task_counts.copy(),
                })
                tracker["events"].append((si, "CARE", None))
            
            # Track FEED for lifecycle
            for wid, wa, wpos in all_wa:
                if not wa or wa[0] != "FEED": continue
                wx, wy = wpos[0], wpos[1]
                if 0 <= wy < len(prev_tiles) and isinstance(prev_tiles[wy], list) and 0 <= wx < len(prev_tiles[wy]):
                    pt = prev_tiles[wy][wx]
                    if isinstance(pt, dict) and "animal" in pt:
                        animal_tracker[(wx, wy)]["events"].append((si, "FEED", None))
        
        # Second pass: DS5/DS20
        for cr in care_log:
            si = cr["step"]; n = len(steps)
            cr["ds5"] = rev_ts[min(si + 5, n - 1)] - rev_ts[si]
            cr["ds10"] = rev_ts[min(si + 10, n - 1)] - rev_ts[si]
            cr["ds20"] = rev_ts[min(si + 20, n - 1)] - rev_ts[si]
            cr["ds1"] = rev_ts[min(si + 1, n - 1)] - rev_ts[si]
            cr["ds3"] = rev_ts[min(si + 3, n - 1)] - rev_ts[si]
        
        final_score = steps[-1][ai].get("reward", 0)
        results.append({
            "eid": eid, "team": teams[ai] if ai < len(teams) else f"A{ai}",
            "ai": ai, "score": final_score,
            "care_log": care_log, "step_snapshots": step_snapshots,
        })
    return results, eid, teams


def run_counterfactual():
    files = list(set(glob.glob("replays/ep_*.json") + glob.glob("replays/sample_episode.json")))
    files = [f for f in files if os.path.exists(f) and "manifest" not in f and "dataset" not in f]
    print(f"Processing {len(files)} episodes...")
    
    all_wins, all_loss = [], []
    all_cares = []
    
    for fp in sorted(files):
        try:
            r, eid, teams = extract_all(fp)
            if len(r) == 2:
                if r[0]["score"] > r[1]["score"]: w, l = r[0], r[1]
                else: w, l = r[1], r[0]
                all_wins.append(w); all_loss.append(l)
                for care in w["care_log"]:
                    care["is_winner"] = True; all_cares.append(care)
                for care in l["care_log"]:
                    care["is_winner"] = False; all_cares.append(care)
            print(f"  {os.path.basename(fp)}: W={len(r[0]['care_log'])} L={len(r[1]['care_log'])} cares")
        except Exception as e:
            print(f"  {os.path.basename(fp)}: ERROR {e}")
    
    w_cares = [c for c in all_cares if c["is_winner"]]
    l_cares = [c for c in all_cares if not c["is_winner"]]
    print(f"\nTotal: {len(w_cares)}W + {len(l_cares)}L = {len(all_cares)} CAREs")
    
    def m(xs): return statistics.mean(xs) if xs else 0
    
    # === GATE 1/2: Classify ALLOW vs BLOCK at TTY=57 ===
    THRESH = 57
    for c in all_cares:
        c["allowed"] = c["tty"] < THRESH
    allow = [c for c in all_cares if c["allowed"]]
    block = [c for c in all_cares if not c["allowed"]]
    
    print(f"\n=== GATE 1/2: TTY < {THRESH} CLASSIFICATION ===")
    print(f"  ALLOW: {len(allow)} ({len(allow)/len(all_cares)*100:.1f}%)")
    print(f"  BLOCK: {len(block)} ({len(block)/len(all_cares)*100:.1f}%)")
    
    w_allow = [c for c in w_cares if c["allowed"]]
    w_block = [c for c in w_cares if not c["allowed"]]
    l_allow = [c for c in l_cares if c["allowed"]]
    l_block = [c for c in l_cares if not c["allowed"]]
    print(f"  W ALLOW: {len(w_allow)} ({len(w_allow)/len(w_cares)*100:.1f}%)")
    print(f"  W BLOCK: {len(w_block)} ({len(w_block)/len(w_cares)*100:.1f}%)")
    print(f"  L ALLOW: {len(l_allow)} ({len(l_allow)/len(l_cares)*100:.1f}%)")
    print(f"  L BLOCK: {len(l_block)} ({len(l_block)/len(l_cares)*100:.1f}%)")
    
    # === GATE 3: Value of BLOCKED vs ALLOWED ===
    print(f"\n=== GATE 3: ALLOW vs BLOCK DS5 ===")
    for label, grp in [("ALLOW", allow), ("BLOCK", block)]:
        print(f"  {label}: DS5={m([c['ds5'] for c in grp]):.0f} DS10={m([c['ds10'] for c in grp]):.0f} DS20={m([c['ds20'] for c in grp]):.0f} TTY={m([c['tty'] for c in grp]):.0f}")
    
    # === GATE 4/5: Replacement opportunities for BLOCKED CAREs ===
    print(f"\n=== GATE 4/5: REPLACEMENT OPPORTUNITIES ===")
    replacements = []
    for c in block:
        tc = c.get("task_counts", {})
        alt = {"FEED": tc.get("FEED", 0), "HARVEST": tc.get("HARVEST", 0),
               "WATER": tc.get("WATER", 0), "PLANT": tc.get("PLANT", 0)}
        has_alt = alt["FEED"] > 0 or alt["HARVEST"] > 0 or alt["WATER"] > 0 or alt["PLANT"] > 0
        best_alt_val = max(alt.values()) if has_alt else 0
        c["has_replacement"] = has_alt
        c["replacement_count"] = sum(alt.values())
        c["best_alt"] = max(alt, key=lambda k: alt[k]) if has_alt else "NONE"
        replacements.append(c)
    
    has_rep = [c for c in replacements if c["has_replacement"]]
    no_rep = [c for c in replacements if not c["has_replacement"]]
    print(f"  BLOCKED CAREs: {len(replacements)}")
    print(f"    With replacement: {len(has_rep)} ({len(has_rep)/len(replacements)*100:.1f}%)")
    print(f"    No replacement:   {len(no_rep)} ({len(no_rep)/len(replacements)*100:.1f}%)")
    print(f"    Avg replacements per blocked: {m([c['replacement_count'] for c in replacements]):.1f}")
    
    if no_rep:
        print(f"    NO_REPLACEMENT DS5: {m([c['ds5'] for c in no_rep]):.0f}")
    if has_rep:
        print(f"    HAS_REPLACEMENT DS5: {m([c['ds5'] for c in has_rep]):.0f}")
    
    # Best alternative distribution
    alt_dist = defaultdict(int)
    for c in replacements: alt_dist[c["best_alt"]] += 1
    print(f"    Best alternatives: {dict(sorted(alt_dist.items(), key=lambda x: -x[1]))}")
    
    # === GATE 7: Threshold sensitivity ===
    print(f"\n=== GATE 7: THRESHOLD SENSITIVITY ===")
    sensitivity = []
    for thresh in [19, 38, 57, 76, 95, 150, 250]:
        blk = [c for c in all_cares if c["tty"] >= thresh]
        blk_pct = len(blk) / len(all_cares) * 100
        has = [c for c in blk if c.get("has_replacement", False)]
        no = [c for c in blk if not c.get("has_replacement", False)]
        blk_ds5 = m([c["ds5"] for c in blk])
        has_ds5 = m([c["ds5"] for c in has]) if has else 0
        no_ds5 = m([c["ds5"] for c in no]) if no else 0
        
        # For blocked CAREs, classify ALLOWED would-be DS5
        w_blk = [c for c in blk if c["is_winner"]]
        l_blk = [c for c in blk if not c["is_winner"]]
        
        print(f"  TTY<{thresh:>3}: blocked={len(blk)}({blk_pct:.0f}%) has_alt={len(has)}({len(has)/max(len(blk),1)*100:.0f}%) no_alt={len(no)}({len(no)/max(len(blk),1)*100:.0f}%) blk_ds5={blk_ds5:.0f}")
        sensitivity.append({"threshold": thresh, "blocked": len(blk), "blocked_pct": blk_pct,
                           "has_alt": len(has), "no_alt": len(no), "blk_ds5": blk_ds5,
                           "w_blocked": len(w_blk), "l_blocked": len(l_blk)})
    
    with open("replays/a4_threshold_sensitivity.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=sensitivity[0].keys())
        w.writeheader(); w.writerows(sensitivity)
    
    # === GATE 8: Winner/Loser Asymmetry ===
    print(f"\n=== GATE 8: WINNER/LOSER ASYMMETRY ===")
    for label, wl_cares in [("Winners", w_cares), ("Losers", l_cares)]:
        blk = [c for c in wl_cares if not c["allowed"]]
        allw = [c for c in wl_cares if c["allowed"]]
        print(f"  {label}: ALLOW_DS5={m([c['ds5'] for c in allw]):.0f} BLOCK_DS5={m([c['ds5'] for c in blk]):.0f}")
        print(f"          ALLOW_TTY={m([c['tty'] for c in allw]):.0f} BLOCK_TTY={m([c['tty'] for c in blk]):.0f}")
        print(f"          Blocked {len(blk)}/{len(wl_cares)} ({len(blk)/len(wl_cares)*100:.1f}%)")
    
    # === GATE 9: Safety Assessment ===
    print(f"\n=== GATE 9: SAFETY ASSESSMENT ===")
    # Criteria:
    # 1. BLOCKED DS5 < ALLOWED DS5? 
    allow_ds5 = m([c["ds5"] for c in allow])
    block_ds5 = m([c["ds5"] for c in block])
    ds5_ratio = block_ds5 / allow_ds5 if allow_ds5 else 1
    
    # 2. Replacement availability
    rep_pct = len(has_rep) / len(replacements) * 100 if replacements else 0
    
    # 3. No-replacement DS5 (PASS risk)
    no_rep_ds5 = m([c["ds5"] for c in no_rep]) if no_rep else 0
    
    # 4. Winner impact
    w_block_pct = len(w_block) / len(w_cares) * 100 if w_cares else 0
    l_block_pct = len(l_block) / len(l_cares) * 100 if l_cares else 0
    
    print(f"  DS5 ratio (blocked/allowed): {ds5_ratio:.2f}")
    print(f"  Replacement availability: {rep_pct:.1f}%")
    print(f"  No-replacement DS5: {no_rep_ds5:.0f}")
    print(f"  Winner blocked%: {w_block_pct:.1f}%")
    print(f"  Loser blocked%: {l_block_pct:.1f}%")
    
    # Verdict
    if ds5_ratio < 0.5 and rep_pct > 30:
        verdict = "SAFE_TO_IMPLEMENT"
        reason = "BLOCKED CARE has significantly lower DS5 and most have productive alternatives"
    elif ds5_ratio < 0.5 and rep_pct > 15:
        verdict = "PROMISING_BUT_UNSAFE"
        reason = "BLOCKED CARE has low DS5 but many have no replacement (PASS risk)"
    elif ds5_ratio < 0.7:
        verdict = "PROMISING_BUT_UNSAFE"
        reason = "DS5 gap exists but may not be large enough to justify filter"
    else:
        verdict = "REJECT"
        reason = "BLOCKED CARE has similar DS5 to ALLOWED — filter would not help"
    
    print(f"\n  VERDICT: {verdict}")
    print(f"  REASON: {reason}")
    
    # Save replacement CSV
    with open("replays/a4_replacement_opportunities.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["step","day","worker","animal","tty","ds5","ds20","has_replacement",
                     "replacement_count","best_alt","is_winner"])
        for c in replacements:
            w.writerow([c["step"], c["day"], c["worker"], c["animal"], c["tty"],
                       round(c["ds5"], 0), round(c["ds20"], 0),
                       c["has_replacement"], c.get("replacement_count", 0),
                       c.get("best_alt", "NONE"), c["is_winner"]])
    
    # Save counterfactual dataset
    dataset = {
        "threshold": THRESH, "total_cares": len(all_cares),
        "allowed": len(allow), "blocked": len(block),
        "allow_ds5": round(allow_ds5, 1), "block_ds5": round(block_ds5, 1),
        "replacement_pct": round(rep_pct, 1),
        "verdict": verdict, "reason": reason,
        "sensitivity": sensitivity,
    }
    with open("replays/a4_tty_counterfactual.json", "w") as f:
        json.dump(dataset, f, indent=2)
    
    print(f"\nOutputs: a4_tty_counterfactual.json, a4_threshold_sensitivity.csv, a4_replacement_opportunities.csv")
    return verdict, reason, dataset


if __name__ == "__main__":
    run_counterfactual()
