"""
Bulk episode replay analysis for economic scheduler forensics.
Processes multiple episode JSONs, extracts per-agent metrics, 
and performs temporal PASS analysis.
"""
import json
import statistics
import os
import glob
from collections import defaultdict

PRODUCTIVE_OPS = {"HARVEST", "PLANT", "WATER", "FEED", "CARE", "PLACE", "PICKUP", "COLLECT_FERTILIZER", "BUILD_PASTURE"}

def analyze_episode(filepath):
    with open(filepath) as f:
        data = json.load(f)
    
    steps = data["steps"]
    n_steps = len(steps)
    n_agents = len(steps[0]) if steps else 0
    info = data.get("info", {})
    seed = info.get("seed", 0)
    episode_id = info.get("EpisodeId", "unknown")
    teams = info.get("TeamNames", [f"Agent_{i}" for i in range(n_agents)])
    
    results = []
    for agent_idx in range(n_agents):
        score = steps[-1][agent_idx].get("reward", 0)
        
        action_counts = defaultdict(int)
        revenue = 0
        sell_revenue_ts = []  # Time series
        pass_steps = []
        
        for step_idx, step in enumerate(steps):
            a = step[agent_idx]
            act = a.get("action", {})
            obs = a.get("observation", {})
            prices = obs.get("market", {}).get("prices", {}) if obs else {}
            
            if isinstance(act, dict):
                # Revenue
                for m in act.get("market", []):
                    if m and m[0] == "SELL" and len(m) >= 3:
                        rev = m[2] * prices.get(m[1], 0)
                        revenue += rev
                        sell_revenue_ts.append((step_idx, rev))
                
                # Worker actions
                for alist in [act.get("farmer", [])] + act.get("hands", []):
                    if alist and alist[0]:
                        action_counts[alist[0]] += 1
                    if alist and alist[0] == "PASS":
                        # Record PASS for temporal analysis
                        farmer_pos = obs.get("farms", [{}])[agent_idx].get("farmer", [0,0]) if obs.get("farms") else [0,0]
                        pass_steps.append((step_idx, agent_idx))
        
        # Derived metrics
        total_worker_actions = sum(action_counts.values())
        pass_count = action_counts.get("PASS", 0)
        pass_pct = pass_count / total_worker_actions * 100 if total_worker_actions else 0
        
        prod_actions = sum(action_counts.get(op, 0) for op in PRODUCTIVE_OPS)
        rpa = revenue / prod_actions if prod_actions else 0
        
        # Worker steps (movement)
        worker_steps = sum(action_counts.get(d, 0) for d in ("NORTH", "SOUTH", "EAST", "WEST"))
        rws = revenue / worker_steps if worker_steps else 0
        
        # Cost = Revenue - Score
        cost = revenue - score
        cost_ratio = cost / revenue * 100 if revenue else 0
        
        # Action breakdown
        harvest_count = action_counts.get("HARVEST", 0)
        feed_count = action_counts.get("FEED", 0)
        care_count = action_counts.get("CARE", 0)
        water_count = action_counts.get("WATER", 0)
        plant_count = action_counts.get("PLANT", 0)
        pickup_count = action_counts.get("PICKUP", 0)
        drop_count = action_counts.get("DROP", 0)
        sell_count = action_counts.get("SELL", 0)
        
        # PASS temporal analysis
        pass_forward_rev = defaultdict(list)  # window_size -> [revenue values]
        for p_step, _ in pass_steps:
            for window in (1, 3, 5, 10, 20):
                rev_in_window = 0
                for s, r in sell_revenue_ts:
                    if p_step < s <= p_step + window:
                        rev_in_window += r
                pass_forward_rev[window].append(rev_in_window)
        
        avg_rev_after_pass = {w: statistics.mean(v) if v else 0 for w, v in pass_forward_rev.items()}
        
        # Max workers over time
        max_workers = 0
        for step in steps:
            obs = step[agent_idx].get("observation", {})
            farms = obs.get("farms", [])
            if farms and isinstance(farms[agent_idx], dict):
                n = 1 + len(farms[agent_idx].get("hands", []))
                max_workers = max(max_workers, n)
        
        # Per-day worker count evolution
        worker_counts_by_day = []
        for day_start in range(0, n_steps, 24):
            day_end = min(day_start + 24, n_steps)
            step = steps[day_start]
            obs = step[agent_idx].get("observation", {})
            farms = obs.get("farms", [])
            if farms and isinstance(farms[agent_idx], dict):
                n = 1 + len(farms[agent_idx].get("hands", []))
                worker_counts_by_day.append(n)
        
        # Replay level stats
        r = {
            "episode_id": episode_id,
            "seed": seed,
            "team": teams[agent_idx] if agent_idx < len(teams) else f"Agent_{agent_idx}",
            "agent_idx": agent_idx,
            "score": score,
            "revenue": revenue,
            "cost": cost,
            "cost_ratio": cost_ratio,
            "total_worker_actions": total_worker_actions,
            "prod_actions": prod_actions,
            "pass_count": pass_count,
            "pass_pct": pass_pct,
            "worker_steps": worker_steps,
            "rpa": rpa,
            "rws": rws,
            "harvest": harvest_count,
            "feed": feed_count,
            "care": care_count,
            "water": water_count,
            "plant": plant_count,
            "pickup": pickup_count,
            "drop": drop_count,
            "sell": sell_count,
            "max_workers": max_workers,
            "worker_counts_by_day": worker_counts_by_day,
            "avg_rev_after_pass_1": avg_rev_after_pass.get(1, 0),
            "avg_rev_after_pass_5": avg_rev_after_pass.get(5, 0),
            "avg_rev_after_pass_10": avg_rev_after_pass.get(10, 0),
            "n_steps": n_steps,
        }
        results.append(r)
    
    return results, info


def PASS_temporal_classify(results):
    """
    For each agent, classify PASS turns into:
    A: PRODUCTIVE_PASS — 5-turn forward revenue > median
    B: NEUTRAL_PASS — 5-turn forward revenue near median
    C: WASTEFUL_PASS — 5-turn forward revenue < median
    
    Returns per-agent classification breakdown.
    """
    # This requires per-PASS tracking which we don't have from the bulk results.
    # We approximate using the aggregate avg_rev_after_pass metric.
    classification = []
    for r in results:
        # Use RPA as baseline: if avg rev after PASS > RPA, PASS was productive
        # (waited for high-value action)
        rpa = r["rpa"]
        avg5 = r["avg_rev_after_pass_5"]
        if avg5 > rpa * 1.2:
            cls = "PRODUCTIVE_PASS_dominant"
        elif avg5 < rpa * 0.8:
            cls = "WASTEFUL_PASS_dominant"
        else:
            cls = "NEUTRAL_PASS_dominant"
        
        r["pass_classification"] = cls
        classification.append(r)
    return classification


if __name__ == "__main__":
    import sys
    
    pattern = sys.argv[1] if len(sys.argv) > 1 else "replays/*.json"
    files = glob.glob(pattern)
    print(f"Analyzing {len(files)} replay files:\n")
    
    all_results = []
    for fp in files:
        fname = os.path.basename(fp)
        if fname == "manifest.csv" or fname == "sample_episode.json":
            continue
        if "manifest" in fname:
            continue
        print(f"  {fname}...", end=" ", flush=True)
        try:
            results, info = analyze_episode(fp)
            for r in results:
                all_results.append(r)
            print(f"{len(results)} agents, seed={info.get('seed', '?')}")
        except Exception as e:
            print(f"ERROR: {e}")
    
    if not all_results:
        print("No results found.")
        sys.exit(1)
    
    # Classify PASS
    all_results = PASS_temporal_classify(all_results)
    
    # Split by winner/loser (relative within same episode)
    episodes = defaultdict(list)
    for r in all_results:
        episodes[r["episode_id"]].append(r)
    
    winners = []
    losers = []
    for eid, agents in episodes.items():
        if len(agents) == 2:
            if agents[0]["score"] > agents[1]["score"]:
                winners.append(agents[0])
                losers.append(agents[1])
            elif agents[1]["score"] > agents[0]["score"]:
                winners.append(agents[1])
                losers.append(agents[0])
            else:
                winners.append(agents[0])
                losers.append(agents[1])
        else:
            winners.extend(agents)
    
    # Compute statistics
    def stat(name, values):
        if not values: return f"{name}: N/A"
        return f"{name}: mean={statistics.mean(values):.1f}, median={statistics.median(values):.1f}, std={statistics.stdev(values):.1f}" if len(values) > 1 else f"{name}: {values[0]:.1f}"
    
    print(f"\n{'='*70}")
    print(f"WINNERS vs LOSERS ANALYSIS (n_winners={len(winners)}, n_losers={len(losers)})")
    print(f"{'='*70}")
    
    metrics = ["score", "revenue", "cost", "cost_ratio", "prod_actions", "pass_count", "pass_pct", "rpa", "rws", "harvest", "feed", "care", "water", "plant", "pickup", "drop", "sell", "max_workers", "avg_rev_after_pass_5"]
    
    print(f"\n{'Metric':<25} {'Winners':>25} {'Losers':>25} {'WinnerAdv':>12}")
    print(f"{'-'*25} {'-'*25} {'-'*25} {'-'*12}")
    
    for m in metrics:
        w_vals = [r[m] for r in winners]
        l_vals = [r[m] for r in losers]
        if not w_vals or not l_vals:
            continue
        w_mean = statistics.mean(w_vals)
        l_mean = statistics.mean(l_vals)
        adv = (w_mean - l_mean) / abs(l_mean) * 100 if l_mean else 0
        
        # Format based on metric type
        if m in ("pass_pct", "cost_ratio"):
            fmt = f"{m:<25} {w_mean:>25.1f}% {l_mean:>25.1f}% {adv:>+12.1f}%"
        elif m in ("rpa", "rws", "avg_rev_after_pass_5"):
            fmt = f"{m:<25} {w_mean:>25.2f} {l_mean:>25.2f} {adv:>+12.1f}%"
        else:
            fmt = f"{m:<25} {w_mean:>25.1f} {l_mean:>25.1f} {adv:>+12.1f}%"
        print(fmt)
    
    # Effect sizes (Cohen's d)
    print(f"\n{'='*70}")
    print("EFFECT SIZES (Cohen's d: winner - loser)")
    print(f"{'='*70}")
    
    def cohens_d(xs, ys):
        d = statistics.mean(xs) - statistics.mean(ys)
        pooled_sd = ((statistics.stdev(xs)**2 + statistics.stdev(ys)**2) / 2) ** 0.5 if len(xs)>1 and len(ys)>1 else 1e-9
        return d / pooled_sd if pooled_sd else 0
    
    key_metrics = ["score", "pass_pct", "rpa", "cost_ratio", "prod_actions", "avg_rev_after_pass_5"]
    for m in key_metrics:
        wv = [r[m] for r in winners]
        lv = [r[m] for r in losers]
        if len(wv) > 1 and len(lv) > 1:
            d = cohens_d(wv, lv)
            direction = "winner > loser" if d > 0 else "loser > winner"
            print(f"  {m:<30} d={d:+.2f} ({direction})")
    
    # PASS classification
    print(f"\n{'='*70}")
    print("PASS CLASSIFICATION")
    print(f"{'='*70}")
    for label, group in [("Winners", winners), ("Losers", losers)]:
        productive = sum(1 for r in group if r.get("pass_classification") == "PRODUCTIVE_PASS_dominant")
        neutral = sum(1 for r in group if r.get("pass_classification") == "NEUTRAL_PASS_dominant")
        wasteful = sum(1 for r in group if r.get("pass_classification") == "WASTEFUL_PASS_dominant")
        n = len(group)
        print(f"  {label}: PRODUCTIVE={productive} NEUTRAL={neutral} WASTEFUL={wasteful} (n={n})")
    
    # Correlation: PASS% vs Score
    print(f"\n{'='*70}")
    print("CORRELATION: PASS% vs ECONOMIC METRICS")
    print(f"{'='*70}")
    import math
    def pearson(xs, ys):
        n = len(xs)
        mx, my = statistics.mean(xs), statistics.mean(ys)
        sx, sy = statistics.stdev(xs), statistics.stdev(ys)
        cov = sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / (n-1)
        return cov / (sx * sy) if sx and sy else 0
    
    all_pass = [r["pass_pct"] for r in all_results]
    all_score = [r["score"] for r in all_results]
    all_rpa = [r["rpa"] for r in all_results]
    all_cost = [r["cost_ratio"] for r in all_results]
    
    for label, ys in [("Score", all_score), ("RPA", all_rpa), ("CostRatio", all_cost)]:
        r_val = pearson(all_pass, ys)
        print(f"  PASS% vs {label}: r={r_val:+.3f}")
    
    # Save results
    output = {
        "n_episodes": len(episodes),
        "n_winners": len(winners),
        "n_losers": len(losers),
        "winners": [{k: v for k, v in r.items() if k not in ("worker_counts_by_day",)} for r in winners],
        "losers": [{k: v for k, v in r.items() if k not in ("worker_counts_by_day",)} for r in losers],
        "all": [{k: v for k, v in r.items() if k not in ("worker_counts_by_day",)} for r in all_results],
    }
    
    with open("replays/economic_scheduler_dataset.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nDataset saved to replays/economic_scheduler_dataset.json")
    print(f"Total episodes: {len(episodes)}, Total agents: {len(all_results)}")
