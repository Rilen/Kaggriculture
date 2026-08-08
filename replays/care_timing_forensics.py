"""
CARE Timing Causal Forensics — Gates 0-10.
Per-CARE extraction, animal lifecycle reconstruction, matched analysis, placebo test.
"""
import json, os, glob, statistics, csv
from collections import defaultdict

PRODUCT_PRICES = {"MILK": 160, "WOOL": 200, "EGG": 50}
ANIMAL_PRODUCT = {"COW": "MILK", "SHEEP": "WOOL", "GOOSE": "EGG"}

def analyze_care_forensics(filepath):
    with open(filepath) as f: data = json.load(f)
    steps = data["steps"]
    info = data.get("info", {})
    eid = info.get("EpisodeId", os.path.basename(filepath))
    teams = info.get("TeamNames", [f"A{i}" for i in range(2)])
    results = []
    for ai in range(len(steps[0])):
        rev_ts = [0.0] * len(steps); cum = 0.0
        care_log = []
        # Animal lifecycle tracking: (x, y) -> {events: [(step, type, state_before)], ...}
        animal_tracker = defaultdict(lambda: {"events": [], "placed_step": None})
        
        for si, step in enumerate(steps):
            a = step[ai]; act = a.get("action", {}); obs = a.get("observation", {})
            prev_obs = steps[si - 1][ai].get("observation", {}) if si > 0 else obs
            
            # Revenue
            prices = obs.get("market", {}).get("prices", {}) if obs else {}
            if isinstance(act, dict):
                for m in act.get("market", []):
                    if m and m[0] == "SELL" and len(m) >= 3:
                        cum += m[2] * prices.get(m[1], 0)
            rev_ts[si] = cum
            
            # Pre-action state for tile lookup
            prev_farms = prev_obs.get("farms", [])
            prev_farm = prev_farms[ai] if prev_farms and ai < len(prev_farms) and isinstance(prev_farms[ai], dict) else {}
            prev_tiles = prev_farm.get("tiles", [])
            day = prev_obs.get("day", 0)
            hour = prev_obs.get("hour", 0)
            
            if not isinstance(act, dict): continue
            
            # Worker actions: farmer + hands
            farmer_act = act.get("farmer", ["PASS"])
            hands_acts = act.get("hands", [])
            worker_positions = [prev_farm.get("farmer", [0, 0])] + prev_farm.get("hands", [])
            all_wa = [(f"F", farmer_act, worker_positions[0] if worker_positions else [0,0])]
            for hi, ha in enumerate(hands_acts):
                pos = worker_positions[hi + 1] if hi + 1 < len(worker_positions) else [0, 0]
                all_wa.append((f"H{hi}", ha, pos))
            
            for wid, wa, wpos in all_wa:
                if not wa or wa[0] != "CARE": continue
                wx, wy = wpos[0], wpos[1]
                
                # Animal state BEFORE CARE
                pre_tile = None
                if 0 <= wy < len(prev_tiles) and isinstance(prev_tiles[wy], list) and 0 <= wx < len(prev_tiles[wy]):
                    pre_tile = prev_tiles[wy][wx]
                
                if not isinstance(pre_tile, dict) or "animal" not in pre_tile:
                    continue
                
                animal = pre_tile["animal"]
                pre_fed = pre_tile.get("fed_today", False)
                pre_cared = pre_tile.get("cared_today", False)
                pre_yield = pre_tile.get("yield_units", 0)
                
                # Animal state AFTER CARE
                post_tile = None
                post_farms = obs.get("farms", [])
                post_farm = post_farms[ai] if post_farms and ai < len(post_farms) and isinstance(post_farms[ai], dict) else {}
                post_tiles = post_farm.get("tiles", [])
                if 0 <= wy < len(post_tiles) and isinstance(post_tiles[wy], list) and 0 <= wx < len(post_tiles[wy]):
                    post_tile = post_tiles[wy][wx]
                
                post_yield = post_tile.get("yield_units", 0) if isinstance(post_tile, dict) else 0
                
                # Time since last CARE on this animal
                animal_key = (wx, wy)
                tracker = animal_tracker[animal_key]
                prev_cares = [e for e in tracker["events"] if e[1] == "CARE"]
                time_since_last_care = si - prev_cares[-1][0] if prev_cares else 999
                time_since_last_feed = si - max([e[0] for e in tracker["events"] if e[1] == "FEED"], default=0) if any(e[1] == "FEED" for e in tracker["events"]) else 999
                
                # Time to next yield: find when yield_units increases after this CARE
                time_to_next_yield = 999
                for fs in range(si + 1, min(si + 200, len(steps))):
                    fs_obs = steps[fs][ai].get("observation", {})
                    fs_farms = fs_obs.get("farms", [])
                    fs_farm = fs_farms[ai] if fs_farms and ai < len(fs_farms) and isinstance(fs_farms[ai], dict) else {}
                    fs_tiles = fs_farm.get("tiles", [])
                    if 0 <= wy < len(fs_tiles) and isinstance(fs_tiles[wy], list) and 0 <= wx < len(fs_tiles[wy]):
                        fs_tile = fs_tiles[wy][wx]
                        if isinstance(fs_tile, dict) and fs_tile.get("yield_units", 0) > post_yield:
                            time_to_next_yield = fs - si
                            break
                        # If animal disappears (harvested/sold), stop looking
                        if not isinstance(fs_tile, dict) or "animal" not in fs_tile:
                            time_to_next_yield = fs - si
                            break
                
                # Yield after CARE (how many units produced)
                yield_after = 0
                for fs in range(si + 1, min(si + 200, len(steps))):
                    fs_obs = steps[fs][ai].get("observation", {})
                    fs_farms = fs_obs.get("farms", [])
                    fs_farm = fs_farms[ai] if fs_farms and ai < len(fs_farms) and isinstance(fs_farms[ai], dict) else {}
                    fs_tiles = fs_farm.get("tiles", [])
                    if 0 <= wy < len(fs_tiles) and isinstance(fs_tiles[wy], list) and 0 <= wx < len(fs_tiles[wy]):
                        fs_tile = fs_tiles[wy][wx]
                        if isinstance(fs_tile, dict) and "animal" in fs_tile:
                            yield_after = max(yield_after, fs_tile.get("yield_units", 0))
                        else:
                            break
                    else:
                        break
                
                # Record event (DS computed in second pass)
                care_record = {
                    "step": si, "day": day, "hour": hour, "worker": wid,
                    "animal": animal, "pos": f"{wx},{wy}",
                    "pre_fed": pre_fed, "pre_cared": pre_cared, "pre_yield": pre_yield,
                    "post_yield": post_yield,
                    "time_since_last_care": time_since_last_care,
                    "time_since_last_feed": time_since_last_feed,
                    "time_to_next_yield": time_to_next_yield,
                    "yield_after": yield_after,
                }
                care_log.append(care_record)
                tracker["events"].append((si, "CARE", care_record))
            
            # Also track FEED events for animal lifecycle
            for wid, wa, wpos in all_wa:
                if not wa or wa[0] != "FEED": continue
                wx, wy = wpos[0], wpos[1]
                if 0 <= wy < len(prev_tiles) and isinstance(prev_tiles[wy], list) and 0 <= wx < len(prev_tiles[wy]):
                    pre_tile = prev_tiles[wy][wx]
                    if isinstance(pre_tile, dict) and "animal" in pre_tile:
                        animal_tracker[(wx, wy)]["events"].append((si, "FEED", None))
                        if animal_tracker[(wx, wy)]["placed_step"] is None and si < 50:
                            animal_tracker[(wx, wy)]["placed_step"] = si
        
        final_score = steps[-1][ai].get("reward", 0)
        
        # Second pass: compute DS after rev_ts fully populated
        for cr in care_log:
            si = cr["step"]; n = len(steps)
            cr["ds5"] = rev_ts[min(si + 5, n - 1)] - rev_ts[si]
            cr["ds10"] = rev_ts[min(si + 10, n - 1)] - rev_ts[si]
            cr["ds20"] = rev_ts[min(si + 20, n - 1)] - rev_ts[si]
        
        results.append({
            "eid": eid, "team": teams[ai] if ai < len(teams) else f"A{ai}",
            "ai": ai, "score": final_score, "care_log": care_log,
            "n_cares": len(care_log),
        })
    return results, eid, teams


def run():
    files = list(set(glob.glob("replays/ep_*.json") + glob.glob("replays/sample_episode.json")))
    files = [f for f in files if os.path.exists(f) and "manifest" not in f and "dataset" not in f]
    print(f"Files: {len(files)}")
    
    all_wins, all_loss = [], []
    all_cares = []  # flattened
    
    for fp in sorted(files):
        try:
            r, eid, teams = analyze_care_forensics(fp)
            if len(r) == 2:
                if r[0]["score"] > r[1]["score"]:
                    w, l = r[0], r[1]
                else:
                    w, l = r[1], r[0]
                all_wins.append(w); all_loss.append(l)
                for care in w["care_log"]:
                    care["is_winner"] = True; care["eid"] = eid; care["team"] = teams[r.index(w)]
                    all_cares.append(care)
                for care in l["care_log"]:
                    care["is_winner"] = False; care["eid"] = eid; care["team"] = teams[r.index(l)]
                    all_cares.append(care)
            print(f"  {os.path.basename(fp)}: W={w['n_cares']} cares L={l['n_cares']} cares")
        except Exception as e:
            print(f"  {os.path.basename(fp)}: ERROR {e}")
    
    n_ep = len(all_wins)
    w_cares = [c for c in all_cares if c["is_winner"]]
    l_cares = [c for c in all_cares if not c["is_winner"]]
    print(f"\nTotal: {len(w_cares)} winner CAREs, {len(l_cares)} loser CAREs ({n_ep} episodes)")
    
    def m(xs): return statistics.mean(xs) if xs else 0
    def med(xs): return statistics.median(xs) if xs else 0
    
    # === GATE 1/3: Basic stats ===
    print(f"\n=== GATE 1/3: CARE DOWNSTREAM VALUE ===")
    metrics = ["ds5", "ds10", "ds20", "time_to_next_yield", "yield_after", "time_since_last_care", "time_since_last_feed"]
    print(f"{'Metric':<22} {'W Mean':>10} {'L Mean':>10} {'W Med':>10} {'L Med':>10} {'W/L':>8}")
    for met in metrics:
        wv = [c[met] for c in w_cares]
        lv = [c[met] for c in l_cares]
        ratio = m(wv) / max(m(lv), 0.01)
        print(f"{met:<22} {m(wv):>10.1f} {m(lv):>10.1f} {med(wv):>10.1f} {med(lv):>10.1f} {ratio:>7.2f}x")
    
    # === GATE 4: Matched CARE analysis ===
    print(f"\n=== GATE 4: MATCHED CARE ANALYSIS ===")
    # Match by: same animal type, similar day (±5), similar pre_yield (±1)
    matched_pairs = []
    for wc in w_cares:
        for lc in l_cares:
            if wc["animal"] != lc["animal"]: continue
            if abs(wc["day"] - lc["day"]) > 5: continue
            if abs(wc.get("pre_yield", 0) - lc.get("pre_yield", 0)) > 1: continue
            matched_pairs.append((wc, lc))
            break
    
    print(f"  Matched pairs: {len(matched_pairs)}")
    if matched_pairs:
        w_ds5 = [p[0]["ds5"] for p in matched_pairs]
        l_ds5 = [p[1]["ds5"] for p in matched_pairs]
        w_ttn = [p[0]["time_to_next_yield"] for p in matched_pairs]
        l_ttn = [p[1]["time_to_next_yield"] for p in matched_pairs]
        print(f"  Matched DS5:  W={m(w_ds5):.0f} L={m(l_ds5):.0f} delta={m(w_ds5)-m(l_ds5):+.0f}")
        print(f"  Matched TTY:  W={m(w_ttn):.1f} L={m(l_ttn):.1f} delta={m(w_ttn)-m(l_ttn):+.1f}")
        
        # Save matched CSV
        with open("replays/care_timing_matched.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["w_ds5","l_ds5","w_ttn","l_ttn","w_tslc","l_tslc","animal","day"])
            for wc, lc in matched_pairs:
                w.writerow([wc["ds5"], lc["ds5"], wc["time_to_next_yield"], lc["time_to_next_yield"],
                           wc["time_since_last_care"], lc["time_since_last_care"], wc["animal"], wc["day"]])
    
    # === GATE 5: Yield cycle hypothesis ===
    print(f"\n=== GATE 5: YIELD CYCLE HYPOTHESIS ===")
    # Group by time_to_next_yield (quantiles)
    all_ttn = sorted([c["time_to_next_yield"] for c in all_cares if c["time_to_next_yield"] < 900])
    if all_ttn:
        q1 = all_ttn[len(all_ttn)//3]
        q2 = all_ttn[2*len(all_ttn)//3]
        buckets = {"NEAR (fast yield)": (0, q1), "MID": (q1, q2), "FAR (slow yield)": (q2, 9999)}
        
        for bname, (lo, hi) in buckets.items():
            b_cares = [c for c in all_cares if lo <= c["time_to_next_yield"] < hi]
            w_in = [c for c in b_cares if c["is_winner"]]
            l_in = [c for c in b_cares if not c["is_winner"]]
            print(f"  {bname} (<{hi:.0f}): n={len(b_cares)} W_n={len(w_in)} L_n={len(l_in)}")
            print(f"    W DS5={m([c['ds5'] for c in w_in]):.0f} TTY={m([c['time_to_next_yield'] for c in w_in]):.1f}")
            print(f"    L DS5={m([c['ds5'] for c in l_in]):.0f} TTY={m([c['time_to_next_yield'] for c in l_in]):.1f}")
    
    # === GATE 6: candidate_score ===
    print(f"\n=== GATE 6: CANDIDATE SCORE CORRELATION ===")
    # Compute: time_since_last_care × (1/time_to_next_yield) as proxy for urgency
    for care in all_cares:
        tslc = care.get("time_since_last_care", 999)
        tty = care.get("time_to_next_yield", 999)
        care["urgency_score"] = tslc / max(tty, 1)  # higher = more urgent
    
    w_urg = [c["urgency_score"] for c in w_cares]
    l_urg = [c["urgency_score"] for c in l_cares]
    w_ds = [c["ds5"] for c in w_cares]
    l_ds = [c["ds5"] for c in l_cares]
    
    def pearson(xs, ys):
        n = len(xs); mx = m(xs); my = m(ys)
        sx = statistics.stdev(xs) if len(xs)>1 else 1
        sy = statistics.stdev(ys) if len(ys)>1 else 1
        if sx == 0 or sy == 0: return 0
        return sum((x-mx)*(y-my) for x,y in zip(xs,ys))/(n-1)/sx/sy
    
    print(f"  Urgency vs DS5 (W): r={pearson(w_urg, w_ds):+.3f}")
    print(f"  Urgency vs DS5 (L): r={pearson(l_urg, l_ds):+.3f}")
    print(f"  W urgency mean={m(w_urg):.2f} L urgency mean={m(l_urg):.2f}")
    
    # === GATE 8: Placebo test ===
    print(f"\n=== GATE 8: PLACEBO TEST ===")
    import random
    rng = random.Random(42)
    placebo_cares_w = list(w_cares)
    placebo_cares_l = list(l_cares)
    for c in placebo_cares_w: c["placebo"] = rng.random()
    for c in placebo_cares_l: c["placebo"] = rng.random()
    p_w = [c["placebo"] for c in placebo_cares_w]
    p_l = [c["placebo"] for c in placebo_cares_l]
    print(f"  Placebo vs DS5 (W): r={pearson(p_w, w_ds):+.3f}")
    print(f"  Placebo vs DS5 (L): r={pearson(p_l, l_ds):+.3f}")
    print(f"  Urgency r={abs(pearson(w_urg, w_ds)):.3f} vs Placebo r={abs(pearson(p_w, w_ds)):.3f}")
    
    # === GATE 7: Control for confounding ===
    print(f"\n=== GATE 7: CONTROL FOR CONFOUNDING ===")
    # Compare only CAREs with same pre_yield and same animal type
    for animal in ["COW", "SHEEP"]:
        for py in [0, 1, 2]:
            w_sub = [c for c in w_cares if c["animal"] == animal and c.get("pre_yield", -1) == py]
            l_sub = [c for c in l_cares if c["animal"] == animal and c.get("pre_yield", -1) == py]
            if len(w_sub) > 10 and len(l_sub) > 10:
                print(f"  {animal} pre_yield={py}: W_n={len(w_sub)} L_n={len(l_sub)}")
                print(f"    W DS5={m([c['ds5'] for c in w_sub]):.0f} L DS5={m([c['ds5'] for c in l_sub]):.0f}")
                print(f"    W TTY={m([c['time_to_next_yield'] for c in w_sub]):.1f} L TTY={m([c['time_to_next_yield'] for c in l_sub]):.1f}")
    
    # === Effect sizes CSV ===
    with open("replays/care_timing_effects.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "w_mean", "l_mean", "w_median", "l_median", "ratio"])
        for met in metrics:
            wv = [c[met] for c in w_cares]; lv = [c[met] for c in l_cares]
            w.writerow([met, round(m(wv), 1), round(m(lv), 1), round(med(wv), 1), round(med(lv), 1), round(m(wv)/max(m(lv), 0.01), 2)])
    
    # Save dataset
    dataset = {
        "n_episodes": n_ep, "n_winner_cares": len(w_cares), "n_loser_cares": len(l_cares),
        "winner_ds5_mean": m([c["ds5"] for c in w_cares]),
        "loser_ds5_mean": m([c["ds5"] for c in l_cares]),
        "matched_pairs": len(matched_pairs),
        "matched_winner_ds5": m([p[0]["ds5"] for p in matched_pairs]) if matched_pairs else 0,
        "matched_loser_ds5": m([p[1]["ds5"] for p in matched_pairs]) if matched_pairs else 0,
    }
    with open("replays/care_timing_dataset.json", "w") as f:
        json.dump(dataset, f, indent=2)
    
    print(f"\n=== OUTPUTS SAVED ===")
    print(f"  care_timing_matched.csv ({len(matched_pairs)} pairs)")
    print(f"  care_timing_effects.csv")
    print(f"  care_timing_dataset.json")


if __name__ == "__main__":
    run()
