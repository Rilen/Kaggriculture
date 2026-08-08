import os
import json
import statistics
import time
from collections import defaultdict
from kaggle_environments import make

from submission import KaggricultureAgentV17
from submission_v18a import KaggricultureAgentV18A
from submission_v18b import KaggricultureAgentV18B
from submission_v18c import KaggricultureAgentV18C


SEEDS = [
    42, 100, 256, 1337, 2024, 777, 999, 1234, 5555, 8888,
    314, 271, 1618, 9876, 5432, 1111, 2222, 3333, 4444, 7777
]

def analyze_match(steps, player_id, telemetry_data):
    stats = {
        "score": steps[-1][player_id].get("reward", 0) if steps else 0,
        "actions": defaultdict(int),
        "buys_anim": defaultdict(int),
        "buys_seed": defaultdict(int),
        "sells": defaultdict(int),
        "sell_revenue": defaultdict(float),
        "total_revenue": 0.0,
        "total_cost": 0.0,
        "plants": defaultdict(int),
        "distance_travelled": 0,
        "worker_positions": {},
        "final_cows": 0,
        "final_sheep": 0,
        "animal_deaths": 0,
        "pass_count": 0,
        "telemetry": telemetry_data
    }
    
    for step_idx, step in enumerate(steps):
        if step_idx == 0: continue
        obs = step[0].get("observation", {})
        
        p_action = step[player_id].get("action", {})
        if isinstance(p_action, dict):
            # Farmer
            f_act = p_action.get("farmer", [])
            if f_act:
                act_name = f_act[0]
                stats["actions"][act_name] += 1
                if act_name == "PASS": stats["pass_count"] += 1
                if act_name == "PLANT" and len(f_act) > 1: stats["plants"][f_act[1]] += 1
            
            # Hands
            for h_act in p_action.get("hands", []):
                if h_act:
                    act_name = h_act[0]
                    stats["actions"][act_name] += 1
                    if act_name == "PASS": stats["pass_count"] += 1
                    if act_name == "PLANT" and len(h_act) > 1: stats["plants"][h_act[1]] += 1
            
            # Market
            for m_act in p_action.get("market", []):
                if not m_act: continue
                cmd = m_act[0]
                stats["actions"][cmd] += 1
                if cmd == "SELL" and len(m_act) >= 3:
                    prod, qty = m_act[1], m_act[2]
                    stats["sells"][prod] += qty
                    price = obs.get("market", {}).get("prices", {}).get(prod, 0) if obs else 0
                    rev = qty * price
                    stats["sell_revenue"][prod] += rev
                    stats["total_revenue"] += rev
                elif cmd == "BUY_ANIMAL" and len(m_act) >= 3:
                    stats["buys_anim"][m_act[1]] += m_act[2]
                    stats["total_cost"] += (400 if m_act[1] == "COW" else 500) * m_act[2]
                elif cmd == "BUY_SEED" and len(m_act) >= 3:
                    stats["buys_seed"][m_act[1]] += m_act[2]
                    cost = {"WHEAT": 10, "MELON": 80, "STRAWBERRY": 100, "CARROT": 20, "TOMATO": 50}.get(m_act[1], 0)
                    stats["total_cost"] += cost * m_act[2]

        if "farms" in obs and len(obs["farms"]) > player_id:
            farm = obs["farms"][player_id]
            cows = sheep = 0
            for row in farm.get("tiles", []):
                for t in (row if isinstance(row, list) else []):
                    if isinstance(t, dict) and t.get("kind") == "PASTURE":
                        if t.get("animal") == "COW": cows += 1
                        elif t.get("animal") == "SHEEP": sheep += 1

            def get_dist(p1, p2): return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1])
            farmer_pos = farm.get("farmer", [0, 0])
            last_f_pos = stats["worker_positions"].get(0)
            if last_f_pos and farmer_pos != last_f_pos: stats["distance_travelled"] += get_dist(last_f_pos, farmer_pos)
            stats["worker_positions"][0] = farmer_pos
            
            for i, hpos in enumerate(farm.get("hands", [])):
                wid = i + 1
                last_h_pos = stats["worker_positions"].get(wid)
                if last_h_pos and hpos != last_h_pos: stats["distance_travelled"] += get_dist(last_h_pos, hpos)
                stats["worker_positions"][wid] = hpos
            
            stats["final_cows"], stats["final_sheep"] = cows, sheep
    
    stats["profit"] = stats["total_revenue"] - stats["total_cost"]
    return stats

def run_experiment():
    variants = {
        "v17.2": KaggricultureAgentV17,
        "v18A": KaggricultureAgentV18A,
        "v18B": KaggricultureAgentV18B,
        "v18C": KaggricultureAgentV18C
    }
    
    results = {k: [] for k in variants}
    
    for seed in SEEDS:
        print(f"Running Seed {seed}...")
        for name, agent_cls in variants.items():
            env = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": seed})
            
            # Instance state
            agent_inst = agent_cls()
            def wrap_agent(obs):
                return agent_inst(obs)
                
            steps = env.run([wrap_agent, "random"])
            
            telemetry = getattr(agent_inst, "telemetry", {})
            stats = analyze_match(steps, 0, telemetry)
            stats["seed"] = seed
            
            results[name].append(stats)
            print(f"  {name} Score: {stats['score']}")

    with open("replays/v18_forensics_20seeds.json", "w") as f:
        json.dump(results, f)
        
    generate_markdown(results)

def generate_markdown(results):
    lines = ["# Kaggriculture — Laboratório v18 (20 Seeds Benchmark)\n"]
    
    for name, run_data in results.items():
        scores = [r["score"] for r in run_data]
        revs = [r["total_revenue"] for r in run_data]
        dists = [r["distance_travelled"] for r in run_data]
        
        rev_per_dist = [r["total_revenue"] / max(1, r["distance_travelled"]) for r in run_data]
        cb = sum(r["telemetry"].get("circuit_breaker_triggered", 0) for r in run_data)
        pas = sum(r["pass_count"] for r in run_data)
        
        lines.append(f"## Variante: {name}")
        lines.append(f"- **Score Médio:** {statistics.mean(scores):.2f}")
        lines.append(f"- **Score Mediano:** {statistics.median(scores):.2f}")
        lines.append(f"- **Max Score:** {max(scores):.2f}")
        lines.append(f"- **Receita Média:** {statistics.mean(revs):.2f}")
        lines.append(f"- **Distância Média:** {statistics.mean(dists):.2f}")
        lines.append(f"- **Revenue/Movement:** {statistics.mean(rev_per_dist):.2f}")
        lines.append(f"- **Total Circuit Breakers:** {cb}")
        lines.append(f"- **Total Passes:** {pas}")
        lines.append(f"- **Win Rate vs v17.2:** Calcular no diff.")
        lines.append("")
        
    with open("replays/v18_forensics_20seeds.md", "w") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    run_experiment()
