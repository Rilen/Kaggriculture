"""
V2 Expanded Economic Scheduler Forensics.
Per-action downstream value, causal chains, animal vs crop, hypothesis tests.
Processes multiple episode JSONs, extracts fine-grained metrics.
"""
import json
import os
import glob
import statistics
import math
from collections import defaultdict

PRODUCTIVE_OPS = {"HARVEST", "PLANT", "WATER", "FEED", "CARE", "PLACE", "PICKUP", "COLLECT_FERTILIZER", "BUILD_PASTURE"}
ANIMAL_OPS = {"FEED", "CARE", "PLACE", "COLLECT_FERTILIZER"}
CROP_OPS = {"PLANT", "WATER"}
MARKET_OPS = {"SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL", "BUY_LAND", "HIRE"}

class EpisodeAnalyzer:
    def __init__(self, filepath):
        with open(filepath) as f:
            self.data = json.load(f)
        self.steps = self.data["steps"]
        self.n_steps = len(self.steps)
        self.n_agents = len(self.steps[0])
        self.info = self.data.get("info", {})
        self.fp = filepath

    def analyze(self):
        results = []
        for ai in range(self.n_agents):
            r = self._analyze_agent(ai)
            results.append(r)
        return results

    def _analyze_agent(self, ai):
        steps = self.steps
        # Per-step action/revenue tracking
        step_actions = []  # (step, action_type, action_detail, immediate_rev, tile_info)
        sell_events = []   # (step, product, units, revenue, price)
        revenue_ts = [0.0] * self.n_steps  # cumulative revenue at each step
        cum_rev = 0.0

        # Tile tracking for causal chains
        tile_planted = {}   # (x, y) -> step planted
        tile_harvested = {} # (x, y) -> [harvest steps]
        animal_placed = {}  # (x, y) -> step placed
        
        action_counts = defaultdict(int)
        action_ds_rev = defaultdict(lambda: defaultdict(list))  # action -> window -> [revenues]

        for step_idx, step in enumerate(steps):
            a = step[ai]
            act = a.get("action", {})
            obs = a.get("observation", {})
            
            prices = obs.get("market", {}).get("prices", {}) if obs else {}
            farms = obs.get("farms", [])
            farm = farms[ai] if farms and ai < len(farms) and isinstance(farms[ai], dict) else None
            
            step_rev = 0.0
            
            if isinstance(act, dict):
                # Market actions
                for m in act.get("market", []):
                    if not m: continue
                    op = m[0]
                    action_counts[f"MARKET_{op}"] += 1
                    if op == "SELL" and len(m) >= 3:
                        rev = m[2] * prices.get(m[1], 0)
                        step_rev += rev
                        sell_events.append((step_idx, m[1], m[2], rev, prices.get(m[1], 0)))

                # Worker actions (farmer + hands)
                worker_actions = [act.get("farmer", ["PASS"])] + act.get("hands", [])
                for wa in worker_actions:
                    if not wa: continue
                    op = wa[0]
                    detail = wa[1] if len(wa) >= 2 else ""
                    action_counts[op] += 1

                    # Record action with immediate revenue
                    act_rec = {
                        "step": step_idx,
                        "op": op,
                        "detail": detail,
                        "imm_rev": step_rev if op == "SELL" else 0,
                    }
                    
                    # Classify by pipeline
                    if op in ANIMAL_OPS:
                        pipeline = "ANIMAL"
                    elif op in CROP_OPS:
                        pipeline = "CROP"
                    elif op == "HARVEST":
                        # Determine if harvest was animal or crop
                        pipeline = "UNKNOWN"  # Will be resolved below
                    elif op == "PLACE":
                        pipeline = "ANIMAL"
                        animal_placed[None] = step_idx  # approximate
                    else:
                        pipeline = "OTHER"
                    
                    # Tile state info for causal chains
                    if farm:
                        fx, fy = farm.get("farmer", [0, 0])
                        tile = farm.get("tiles", [[]])[fy][fx] if fy < len(farm.get("tiles", [])) else None
                        if isinstance(tile, dict):
                            if op == "PLANT":
                                tile_planted[(fx, fy)] = step_idx
                            if op == "HARVEST":
                                tile_harvested.setdefault((fx, fy), []).append(step_idx)
                                # Determine if animal or crop harvest
                                if "animal" in tile:
                                    pipeline = "ANIMAL_HARVEST"
                                elif tile.get("kind") == "PLANT":
                                    pipeline = "CROP_HARVEST"

                    act_rec["pipeline"] = pipeline
                    step_actions.append(act_rec)

            cum_rev += step_rev
            revenue_ts[step_idx] = cum_rev

        # Compute downstream revenue for each action at various windows
        for i, act_rec in enumerate(step_actions):
            start = act_rec["step"]
            for window in (1, 3, 5, 10, 20):
                end = min(start + window, self.n_steps - 1)
                if end > start:
                    ds_rev = revenue_ts[end] - revenue_ts[start]
                    action_ds_rev[act_rec["op"]][window].append(ds_rev)

        # Summary stats
        total_actions = sum(action_counts.values())
        pass_count = action_counts.get("PASS", 0)
        prod_count = sum(action_counts.get(op, 0) for op in PRODUCTIVE_OPS)
        
        final_rev = revenue_ts[-1] if revenue_ts else 0
        final_score = steps[-1][ai].get("reward", 0)
        cost = final_rev - final_score
        
        # RPA
        rpa = final_rev / prod_count if prod_count else 0
        
        # Per-action RPA (immediate + downstream)
        per_action_stats = {}
        for op in PRODUCTIVE_OPS | {"PASS", "PICKUP", "DROP", "DIG"}:
            count = action_counts.get(op, 0)
            if count == 0:
                per_action_stats[op] = {"count": 0, "rpa_imm": 0, "rpa_ds5": 0, "rpa_ds20": 0}
                continue
            ds5 = statistics.mean(action_ds_rev[op][5]) if action_ds_rev[op].get(5) else 0
            ds20 = statistics.mean(action_ds_rev[op][20]) if action_ds_rev[op].get(20) else 0
            per_action_stats[op] = {
                "count": count,
                "rpa_imm": 0,  # immediate revenue from this specific action (hard to attribute)
                "rpa_ds5": ds5,
                "rpa_ds20": ds20,
            }

        # Animal vs Crop pipeline
        animal_actions = sum(action_counts.get(op, 0) for op in ANIMAL_OPS)
        crop_actions = sum(action_counts.get(op, 0) for op in CROP_OPS)
        
        animal_rev_actions = [a for a in step_actions if a["pipeline"] in ("ANIMAL", "ANIMAL_HARVEST")]
        crop_rev_actions = [a for a in step_actions if a["pipeline"] in ("CROP", "CROP_HARVEST")]

        # Max workers
        max_workers = 0
        for step in steps:
            obs = step[ai].get("observation", {})
            farms = obs.get("farms", [])
            if farms and ai < len(farms) and isinstance(farms[ai], dict):
                n = 1 + len(farms[ai].get("hands", []))
                max_workers = max(max_workers, n)

        # Worker steps (movement)
        worker_steps = sum(action_counts.get(d, 0) for d in ("NORTH", "SOUTH", "EAST", "WEST"))
        rws = final_rev / worker_steps if worker_steps else 0

        return {
            "episode_id": self.info.get("EpisodeId", os.path.basename(self.fp)),
            "seed": self.info.get("seed", 0),
            "team": (self.info.get("TeamNames", []) or [f"A{ai}"])[ai] if ai < len(self.info.get("TeamNames", [])) else f"Agent_{ai}",
            "agent_idx": ai,
            "score": final_score,
            "revenue": final_rev,
            "cost": cost,
            "cost_pct": cost / final_rev * 100 if final_rev else 0,
            "rpa": rpa,
            "rws": rws,
            "pass_pct": pass_count / total_actions * 100 if total_actions else 0,
            "prod_actions": prod_count,
            "total_actions": total_actions,
            "worker_steps": worker_steps,
            "max_workers": max_workers,
            "action_counts": dict(action_counts),
            "per_action": per_action_stats,
            "animal_action_count": animal_actions,
            "crop_action_count": crop_actions,
            "n_sells": len(sell_events),
            "n_sell_rev": sum(s[3] for s in sell_events),
        }


def run_full_analysis(file_pattern="replays/ep_*.json", sample_pattern="replays/sample_episode.json"):
    files = glob.glob(file_pattern) + glob.glob(sample_pattern)
    files = [f for f in files if os.path.basename(f) not in ("manifest.csv", "economic_scheduler_dataset.json", "economic_scheduler_dataset_v2.json")]
    files = list(set(files))  # deduplicate
    
    print(f"Processing {len(files)} episode files...")
    all_results = []
    
    for fp in files:
        fname = os.path.basename(fp)
        try:
            analyzer = EpisodeAnalyzer(fp)
            results = analyzer.analyze()
            for r in results:
                all_results.append(r)
            print(f"  {fname}: {len(results)} agents, seeds={results[0]['seed']}, scores={[f'{x['score']:.0f}' for x in results]}")
        except Exception as e:
            print(f"  {fname}: ERROR {e}")
    
    if len(all_results) < 2:
        print("Not enough data.")
        return
    
    # Split by winner/loser
    episodes = defaultdict(list)
    for r in all_results:
        episodes[r["episode_id"]].append(r)
    
    wins, loss = [], []
    for eid, ags in episodes.items():
        if len(ags) == 2:
            if ags[0]["score"] > ags[1]["score"]:
                wins.append(ags[0]); loss.append(ags[1])
            else:
                wins.append(ags[1]); loss.append(ags[0])
    
    print(f"\nEpisodes: {len(episodes)}, Winners: {len(wins)}, Losers: {len(loss)}")
    
    # === STATISTICS ===
    def mean(xs): return statistics.mean(xs) if xs else 0
    def median(xs): return statistics.median(xs) if xs else 0
    def stdev(xs): return statistics.stdev(xs) if len(xs) > 1 else 0
    def ci95(xs):
        if len(xs) < 2: return (0, 0)
        m = mean(xs); s = stdev(xs); n = len(xs)
        t = 2.093 if n >= 20 else (4.303 if n == 2 else (3.182 if n == 3 else (2.776 if n == 4 else 2.571)))
        se = s / math.sqrt(n)
        return (m - t * se, m + t * se)
    def cohens_d(xs, ys):
        d = mean(xs) - mean(ys)
        ps = ((stdev(xs)**2 + stdev(ys)**2) / 2) ** 0.5 if len(xs) > 1 and len(ys) > 1 else 1e-9
        return d / ps if ps else 0

    # Key metrics
    print(f"\n{'='*80}")
    print(f"WINNERS vs LOSERS (n_w={len(wins)}, n_l={len(loss)})")
    print(f"{'='*80}")
    
    all_metrics = ["score", "revenue", "cost_pct", "rpa", "rws", "pass_pct", "prod_actions", "worker_steps", "max_workers"]
    h = f"{'Metric':<20} {'W Mean':>10} {'L Mean':>10} {'Adv%':>8} {'95% CI':>20} {'d':>6}"
    print(h); print("-" * len(h))
    
    for m in all_metrics:
        wv = [r[m] for r in wins]
        lv = [r[m] for r in loss]
        if not wv or not lv: continue
        wm, lm = mean(wv), mean(lv)
        adv = (wm - lm) / abs(lm) * 100 if lm else 0
        ci = ci95([w - l for w, l in zip(wv, lv)])
        d = cohens_d(wv, lv)
        fmt = f"{m:<20} {wm:>10.1f} {lm:>10.1f} {adv:>+8.1f}% [{ci[0]:.0f},{ci[1]:.0f}] {d:>+6.2f}"
        print(fmt)

    # Per-action comparison
    print(f"\n{'='*80}")
    print("PER-ACTION DOWNSTREAM REVENUE (5-turn window)")
    print(f"{'='*80}")
    ops = ["PASS", "HARVEST", "FEED", "CARE", "WATER", "PLANT", "PICKUP", "COLLECT_FERTILIZER", "PLACE", "BUILD_PASTURE", "DROP"]
    h = f"{'Op':<20} {'W Count':>8} {'L Count':>8} {'W DS5 Rev':>12} {'L DS5 Rev':>12} {'Adv%':>8}"
    print(h); print("-" * len(h))
    for op in ops:
        w_ds5 = [r["per_action"].get(op, {}).get("rpa_ds5", 0) for r in wins]
        l_ds5 = [r["per_action"].get(op, {}).get("rpa_ds5", 0) for r in loss]
        w_ct = sum(r["per_action"].get(op, {}).get("count", 0) for r in wins)
        l_ct = sum(r["per_action"].get(op, {}).get("count", 0) for r in loss)
        if w_ct == 0 and l_ct == 0: continue
        wm, lm = mean(w_ds5), mean(l_ds5)
        adv = (wm - lm) / abs(lm) * 100 if lm else 0
        print(f"{op:<20} {w_ct:>8} {l_ct:>8} {wm:>12.1f} {lm:>12.1f} {adv:>+8.1f}%")

    # Animal vs Crop pipeline
    print(f"\n{'='*80}")
    print("ANIMAL vs CROP PIPELINE")
    print(f"{'='*80}")
    for label, grp in [("Winners", wins), ("Losers", loss)]:
        a_acts = sum(r["animal_action_count"] for r in grp)
        c_acts = sum(r["crop_action_count"] for r in grp)
        a_pct = a_acts / (a_acts + c_acts) * 100 if (a_acts + c_acts) else 0
        print(f"  {label}: Animal={a_acts} Crop={c_acts} Animal%={a_pct:.1f}%")
    
    # FEED vs PLANT ratio
    print(f"\n{'='*80}")
    print("FEED/PLANT RATIO (animal priority indicator)")
    print(f"{'='*80}")
    for label, grp in [("Winners", wins), ("Losers", loss)]:
        feeds = sum(r["action_counts"].get("FEED", 0) for r in grp)
        plants = sum(r["action_counts"].get("PLANT", 0) for r in grp)
        ratio = feeds / plants if plants else 999
        print(f"  {label}: FEED={feeds} PLANT={plants} ratio={ratio:.2f}")

    # PASS downstream value vs HARVEST downstream value
    print(f"\n{'='*80}")
    print("STRATEGIC IDLE vs HARVEST: Downstream Revenue Comparison")
    print(f"{'='*80}")
    for label, grp in [("Winners", wins), ("Losers", loss)]:
        pass_ds5 = mean([r["per_action"].get("PASS", {}).get("rpa_ds5", 0) for r in grp])
        harv_ds5 = mean([r["per_action"].get("HARVEST", {}).get("rpa_ds5", 0) for r in grp])
        print(f"  {label}: PASS_DS5={pass_ds5:.0f} HARVEST_DS5={harv_ds5:.0f} ratio={pass_ds5/harv_ds5:.2f}" if harv_ds5 else f"  {label}: no data")

    # Correlation matrix
    print(f"\n{'='*80}")
    print("CORRELATIONS (all agents)")
    print(f"{'='*80}")
    def pearson(xs, ys):
        n = len(xs); mx, my = mean(xs), mean(ys)
        sx, sy = stdev(xs), stdev(ys)
        if not sx or not sy: return 0
        return sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / (n-1) / sx / sy
    
    all_rpa = [r["rpa"] for r in all_results]
    all_score = [r["score"] for r in all_results]
    all_pass = [r["pass_pct"] for r in all_results]
    all_cost = [r["cost_pct"] for r in all_results]
    
    for label, ys in [("Score", all_score), ("Cost%", all_cost), ("PASS%", all_pass)]:
        r_val = pearson(all_rpa, ys)
        sig = "*" if abs(r_val) > 0.5 else ""
        print(f"  RPA vs {label}: r={r_val:+.3f} {sig}")
    
    # Save dataset
    output = {
        "n_episodes": len(episodes),
        "n_winners": len(wins),
        "n_losers": len(loss),
        "winners": [{k: v for k, v in r.items() if k != "per_action"} for r in wins],
        "losers": [{k: v for k, v in r.items() if k != "per_action"} for r in loss],
    }
    with open("replays/economic_scheduler_dataset_v2.json", "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nSaved to replays/economic_scheduler_dataset_v2.json")

if __name__ == "__main__":
    run_full_analysis()
