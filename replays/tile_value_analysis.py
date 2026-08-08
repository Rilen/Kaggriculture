"""
Tile-Value Forensics: Compare which tile instances winners vs losers select
for the same action types. Tests H6: winners pick higher-value instances.
"""
import json, os, glob, statistics, math
from collections import defaultdict

CROPS = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250}

class TileValueAnalyzer:
    def __init__(self, filepath):
        with open(filepath) as f:
            self.data = json.load(f)
        self.steps = self.data["steps"]
        self.info = self.data.get("info", {})
        self.fp = filepath
    
    def analyze(self):
        results = []
        for ai in range(len(self.steps[0])):
            r = self._analyze_agent(ai)
            results.append(r)
        return results
    
    def _tile_at(self, farm, x, y):
        if not farm: return None
        tiles = farm.get("tiles", [])
        if not (0 <= y < len(tiles)): return None
        row = tiles[y]
        if not isinstance(row, list) or not (0 <= x < len(row)): return None
        return row[x]
    
    def _eligible_feed(self, farm, shed, winv, day):
        candidates = []
        for y, row in enumerate(farm.get("tiles", [])):
            for x, t in enumerate(row if isinstance(row, list) else []):
                if not isinstance(t, dict): continue
                if t.get("kind") == "PASTURE" and t.get("animal") and not t.get("fed_today", True):
                    if shed.get("WHEAT", 0) > 0 or winv.get("WHEAT", 0) > 0:
                        # Value: product price × expected yield contribution
                        animal = t["animal"]
                        product = {"COW": "MILK", "SHEEP": "WOOL", "GOOSE": "EGG"}.get(animal, "MILK")
                        price = 160 if animal == "COW" else (200 if animal == "SHEEP" else 50)
                        yield_u = t.get("yield_units", 0)
                        candidates.append((x, y, t, price, yield_u))
        return candidates
    
    def _eligible_care(self, farm):
        candidates = []
        for y, row in enumerate(farm.get("tiles", [])):
            for x, t in enumerate(row if isinstance(row, list) else []):
                if not isinstance(t, dict): continue
                if t.get("kind") == "PASTURE" and t.get("animal") and not t.get("cared_today", True):
                    animal = t["animal"]
                    price = 160 if animal == "COW" else (200 if animal == "SHEEP" else 50)
                    yield_u = t.get("yield_units", 0)
                    cared_bonus = t.get("pending_care_bonus", 0)
                    candidates.append((x, y, t, price, yield_u + cared_bonus * price))
        return candidates
    
    def _eligible_water(self, farm):
        candidates = []
        for y, row in enumerate(farm.get("tiles", [])):
            for x, t in enumerate(row if isinstance(row, list) else []):
                if not isinstance(t, dict): continue
                if t.get("kind") == "PLANT" and not t.get("watered_today", True):
                    crop = t.get("crop", "")
                    price = CROPS.get(crop, 25)
                    yield_u = t.get("yield_units", 0)
                    # Fertilized gives 2x water bonus
                    day = t.get("planted_day", 0)
                    fertilized = t.get("fertilized_until_day", -1) >= 0
                    # Higher value for crops in growth window
                    candidates.append((x, y, t, price, yield_u, fertilized))
        return candidates
    
    def _eligible_plant(self, farm, seeds, day, hour):
        if hour > 20: return []
        candidates = []
        for y, row in enumerate(farm.get("tiles", [])):
            for x, t in enumerate(row if isinstance(row, list) else []):
                if t is not None: continue
                for crop, price in [("STRAWBERRY", 120), ("MELON", 250), ("TOMATO", 60), ("CARROT", 35), ("WHEAT", 25)]:
                    if seeds.get(crop, 0) > 0:
                        candidates.append((x, y, crop, price))
                        break  # One entry per tile, best crop first
        return candidates
    
    def _eligible_harvest(self, farm):
        candidates = []
        for y, row in enumerate(farm.get("tiles", [])):
            for x, t in enumerate(row if isinstance(row, list) else []):
                if not isinstance(t, dict): continue
                yu = t.get("yield_units", 0)
                if yu <= 0: continue
                if t.get("kind") == "PLANT":
                    crop = t.get("crop", "")
                    price = CROPS.get(crop, 25)
                    candidates.append((x, y, t, price * yu, crop))
                elif "animal" in t:
                    animal = t["animal"]
                    product = {"COW": "MILK", "SHEEP": "WOOL", "GOOSE": "EGG"}.get(animal, "MILK")
                    price = 160 if animal == "COW" else (200 if animal == "SHEEP" else 50)
                    candidates.append((x, y, t, price * yu, animal))
        return candidates
    
    def _analyze_agent(self, ai):
        steps = self.steps
        action_instances = []
        revenue_ts = [0.0] * len(steps)
        cum = 0.0
        debug_n = 0
        
        for si, step in enumerate(steps):
            a = step[ai]
            act = a.get("action", {})
            # Use PREVIOUS step's observation for eligibility (before this step's actions)
            prev_step = steps[si - 1] if si > 0 else step
            prev_a = prev_step[ai]
            prev_obs = prev_a.get("observation", {})
            obs = a.get("observation", {})
            
            prices = obs.get("market", {}).get("prices", {}) if obs else {}
            farms = prev_obs.get("farms", [])
            farm = farms[ai] if farms and ai < len(farms) and isinstance(farms[ai], dict) else None
            prev_farms = prev_obs.get("farms", [])
            prev_farm = prev_farms[ai] if prev_farms and ai < len(prev_farms) and isinstance(prev_farms[ai], dict) else farm
            private = prev_obs.get("private", {}) if prev_obs else {}
            shed = (private.get("shed", {}) or {}) if isinstance(private, dict) else {}
            seeds = (private.get("seeds", {}) or {}) if isinstance(private, dict) else {}
            invs = (private.get("inventories", []) or [])
            day = prev_obs.get("day", 0)
            hour = prev_obs.get("hour", 0)
            
            if isinstance(act, dict):
                for m in act.get("market", []):
                    if m and m[0] == "SELL" and len(m) >= 3:
                        cum += m[2] * prices.get(m[1], 0)
            
            revenue_ts[si] = cum
            
            if not farm: continue
            
            workers = [(["farmer", 0, 0], prev_farm.get("farmer", [0, 0]))]
            for hi, hp in enumerate(prev_farm.get("hands", [])):
                workers.append((["hands", hi + 1, hi], hp))
            
            worker_actions = [act.get("farmer", ["PASS"])] + act.get("hands", [])
            
            for wi, (wkey, wpos) in enumerate(workers):
                if wi >= len(worker_actions): continue
                wa = worker_actions[wi]
                if not wa: continue
                op = wa[0]
                w_inv = invs[wi] if wi < len(invs) else {}
                
                wx, wy = wpos[0], wpos[1]
                tile = self._tile_at(prev_farm, wx, wy)
                
                # Find eligible candidates for this action type
                candidates = []
                if op == "FEED":
                    candidates = self._eligible_feed(prev_farm, shed, w_inv, day)
                elif op == "CARE":
                    candidates = self._eligible_care(prev_farm)
                elif op == "WATER":
                    candidates = self._eligible_water(prev_farm)
                elif op == "PLANT":
                    candidates = self._eligible_plant(prev_farm, seeds, day, hour)
                elif op == "HARVEST":
                    candidates = self._eligible_harvest(prev_farm)
                
                if candidates and tile:
                    # Rank candidates by value
                    ranked = sorted(candidates, key=lambda c: c[3] if len(c) > 3 else 0, reverse=True)
                    selected_rank = None
                    selected_value = 0
                    best_value = ranked[0][3] if len(ranked[0]) > 3 else 0
                    
                    for rank, c in enumerate(ranked):
                        if c[0] == wx and c[1] == wy:
                            selected_rank = rank + 1  # 1-indexed
                            selected_value = c[3] if len(c) > 3 else 0
                            break
                    
                    # Tile features
                    tile_features = {}
                    if isinstance(tile, dict):
                        if "animal" in tile:
                            tile_features = {
                                "animal": tile.get("animal"),
                                "yield_units": tile.get("yield_units", 0),
                                "fed_today": tile.get("fed_today", False),
                                "cared_today": tile.get("cared_today", False),
                                "fertilizer_available": tile.get("fertilizer_available", False),
                            }
                        elif tile.get("kind") == "PLANT":
                            tile_features = {
                                "crop": tile.get("crop"),
                                "yield_units": tile.get("yield_units", 0),
                                "watered_today": tile.get("watered_today", False),
                                "planted_day": tile.get("planted_day", 0),
                                "fertilized_until_day": tile.get("fertilized_until_day", -1),
                                "age_days": day - tile.get("planted_day", day),
                            }
                    
                    # Distance to shed
                    shed_positions = [(4, 4), (4, 5), (5, 4), (5, 5)]
                    dist_to_shed = min(abs(wx - sx) + abs(wy - sy) for sx, sy in shed_positions)
                    
                    # Distance to nearest other eligible tile (task density)
                    nearest_other = 99
                    for c in candidates:
                        if c[0] != wx or c[1] != wy:
                            d = abs(wx - c[0]) + abs(wy - c[1])
                            nearest_other = min(nearest_other, d)
                    
                    inst = {
                        "step": si,
                        "day": day,
                        "hour": hour,
                        "action": op,
                        "worker": wi,
                        "pos": (wx, wy),
                        "tile_features": tile_features,
                        "n_candidates": len(candidates),
                        "selected_rank": selected_rank,
                        "selected_value": selected_value,
                        "best_value": best_value,
                        "value_ratio": selected_value / best_value if best_value else 1.0,
                        "chose_best": selected_rank == 1 if selected_rank else False,
                        "dist_to_shed": dist_to_shed,
                        "nearest_other": nearest_other,
                    }
                    action_instances.append(inst)
        
        # Second pass: compute downstream revenue (revenue_ts now fully populated)
        for inst in action_instances:
            si = inst["step"]
            n = len(steps)
            ds5 = revenue_ts[min(si + 5, n - 1)] - revenue_ts[si]
            ds20 = revenue_ts[min(si + 20, n - 1)] - revenue_ts[si]
            inst["ds5"] = ds5
            inst["ds20"] = ds20
        
        if not action_instances:
            return {"error": "no_action_instances"}
        
        # Aggregate statistics per action type
        by_action = defaultdict(list)
        for inst in action_instances:
            by_action[inst["action"]].append(inst)
        
        action_stats = {}
        for op, instances in by_action.items():
            if not instances: continue
            n = len(instances)
            ranks = [i["selected_rank"] for i in instances if i["selected_rank"] is not None]
            action_stats[op] = {
                "count": n,
                "chose_best_pct": sum(1 for i in instances if i["chose_best"]) / n * 100,
                "avg_rank": statistics.mean(ranks) if ranks else 0,
                "avg_ds5": statistics.mean([i["ds5"] for i in instances]),
                "avg_ds20": statistics.mean([i["ds20"] for i in instances]),
                "avg_value_ratio": statistics.mean([i["value_ratio"] for i in instances if i["value_ratio"] is not None]),
                "avg_candidates": statistics.mean([i["n_candidates"] for i in instances]),
            }
        
        return {
            "episode_id": self.info.get("EpisodeId", os.path.basename(self.fp)),
            "team": (self.info.get("TeamNames", []) or [f"A{ai}"])[ai] if ai < len(self.info.get("TeamNames", [])) else f"Agent_{ai}",
            "agent_idx": ai,
            "score": steps[-1][ai].get("reward", 0),
            "action_stats": action_stats,
            "total_instances": len(action_instances),
        }


def run_tile_forensics(file_pattern="replays/ep_*.json", sample_pattern="replays/sample_episode.json"):
    files = glob.glob(file_pattern) + glob.glob(sample_pattern)
    files = list(set(f for f in files if os.path.exists(f) and f.endswith(".json") and "manifest" not in f))
    
    print(f"Processing {len(files)} episode files for tile-value analysis...")
    all_agents = []
    
    for fp in files:
        fname = os.path.basename(fp)
        if "dataset" in fname or "bulk" in fname: continue
        try:
            analyzer = TileValueAnalyzer(fp)
            results = analyzer.analyze()
            for r in results:
                if "error" not in r:
                    all_agents.append(r)
            scores = [f'{r.get("score",0):.0f}' for r in results]
            print(f"  {fname}: {len(results)} agents, scores={scores}")
        except Exception as e:
            print(f"  {fname}: ERROR {e.__class__.__name__}: {e}")
    
    # Split winners/losers
    episodes = defaultdict(list)
    for r in all_agents:
        episodes[r["episode_id"]].append(r)
    
    wins, loss = [], []
    for eid, ags in episodes.items():
        if len(ags) == 2:
            if ags[0]["score"] > ags[1]["score"]:
                wins.append(ags[0]); loss.append(ags[1])
            else:
                wins.append(ags[1]); loss.append(ags[0])
    
    print(f"\nWinners: {len(wins)}, Losers: {len(loss)}")
    
    # Compare per-action tile selection
    actions = ["FEED", "CARE", "WATER", "PLANT", "HARVEST"]
    
    print(f"\n{'='*90}")
    print(f"TILE SELECTION QUALITY: Winners vs Losers (per action type)")
    print(f"{'='*90}")
    
    print(f"\n{'Action':<10} {'Agent':<8} {'N':>6} {'ChoseBest%':>11} {'AvgRank':>8} {'AvgDS5':>9} {'AvgDS20':>9} {'N_Cand':>7}")
    print(f"{'-'*10} {'-'*8} {'-'*6} {'-'*11} {'-'*8} {'-'*9} {'-'*9} {'-'*7}")
    
    for op in actions:
        w_stats = [r["action_stats"].get(op) for r in wins if r.get("action_stats", {}).get(op)]
        l_stats = [r["action_stats"].get(op) for r in loss if r.get("action_stats", {}).get(op)]
        
        w_vals = [s.get("chose_best_pct", 0) for s in w_stats]
        l_vals = [s.get("chose_best_pct", 0) for s in l_stats]
        w_ct = sum(s.get("count", 0) for s in w_stats)
        l_ct = sum(s.get("count", 0) for s in l_stats)
        
        w_best = statistics.mean(w_vals) if w_vals else 0
        l_best = statistics.mean(l_vals) if l_vals else 0
        w_ds5 = statistics.mean([s.get("avg_ds5", 0) for s in w_stats]) if w_stats else 0
        l_ds5 = statistics.mean([s.get("avg_ds5", 0) for s in l_stats]) if l_stats else 0
        w_cand = statistics.mean([s.get("avg_candidates", 0) for s in w_stats]) if w_stats else 0
        l_cand = statistics.mean([s.get("avg_candidates", 0) for s in l_stats]) if l_stats else 0
        w_ds20 = statistics.mean([s.get("avg_ds20", 0) for s in w_stats]) if w_stats else 0
        l_ds20 = statistics.mean([s.get("avg_ds20", 0) for s in l_stats]) if l_stats else 0
        
        print(f"{op:<10} {'Winners':<8} {w_ct:>6} {w_best:>10.1f}% {w_ds5:>9.0f} {w_ds20:>9.0f} {w_cand:>7.1f}")
        print(f"{'':10} {'Losers':<8} {l_ct:>6} {l_best:>10.1f}% {l_ds5:>9.0f} {l_ds20:>9.0f} {l_cand:>7.1f}")
        diff = w_best - l_best
        print(f"{'':10} {'Diff':<8} {'':>6} {diff:>+10.1f}pp")
    
    # Summary: are winners choosing best more often?
    print(f"\n{'='*90}")
    print("H6 TEST: Winners select highest-value instance more often")
    print(f"{'='*90}")
    
    w_chose = [r["action_stats"].get("FEED", {}).get("chose_best_pct", 0) for r in wins]
    l_chose = [r["action_stats"].get("FEED", {}).get("chose_best_pct", 0) for r in loss]
    
    all_w_best = []
    all_l_best = []
    for op in actions:
        all_w_best.extend([r["action_stats"].get(op, {}).get("chose_best_pct", 0) for r in wins if op in r.get("action_stats", {})])
        all_l_best.extend([r["action_stats"].get(op, {}).get("chose_best_pct", 0) for r in loss if op in r.get("action_stats", {})])
    
    if all_w_best and all_l_best:
        wm = statistics.mean(all_w_best)
        lm = statistics.mean(all_l_best)
        print(f"  Winners chose-best avg: {wm:.1f}%")
        print(f"  Losers  chose-best avg: {lm:.1f}%")
        print(f"  Difference: {wm-lm:+.1f}pp")
        
        # Effect size
        d = (wm - lm)
        ps = ((statistics.stdev(all_w_best)**2 + statistics.stdev(all_l_best)**2) / 2) ** 0.5 if len(all_w_best) > 1 and len(all_l_best) > 1 else 1e-9
        if ps:
            print(f"  Cohen's d: {d/ps:+.2f}")
    
    print(f"\nSamples: {len(all_w_best)} winner action-types, {len(all_l_best)} loser action-types")
    
    # Save dataset
    dataset = {
        "n_episodes": len(episodes),
        "winners": [{k: str(v) if isinstance(v, dict) else v for k, v in r.items()} for r in wins],
        "losers": [{k: str(v) if isinstance(v, dict) else v for k, v in r.items()} for r in loss],
    }
    with open("replays/tile_value_dataset.json", "w") as f:
        json.dump(dataset, f, indent=2, default=str)
    print(f"\nSaved to replays/tile_value_dataset.json")


if __name__ == "__main__":
    run_tile_forensics()
