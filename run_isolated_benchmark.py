import subprocess
import json
import statistics

SEEDS = list(range(42, 62))

def run_isolated(agent, seed):
    cmd = ["python", "run_single_match.py", agent, str(seed)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    for line in reversed(res.stdout.splitlines()):
        if line.startswith('{'):
            return json.loads(line)
    return {"score": 0, "rev": 0, "prod": 0}

print("Running isolated benchmark for 20 seeds...")

v3_scores, a2_scores = [], []
v3_revs, a2_revs = [], []
v3_prods, a2_prods = [], []

for seed in SEEDS:
    print(f"\n--- SEED {seed} ---")
    
    res_v3 = run_isolated("submission_v17_3.py", seed)
    print(f"v17.3     | Score: {res_v3['score']:8.1f} | Rev: {res_v3['rev']:8.1f} | Prod: {res_v3['prod']}")
    
    res_a2 = run_isolated("submission_v17_3_a2.py", seed)
    print(f"v17.3-A.2 | Score: {res_a2['score']:8.1f} | Rev: {res_a2['rev']:8.1f} | Prod: {res_a2['prod']}")
    
    v3_scores.append(res_v3['score'])
    v3_revs.append(res_v3['rev'])
    v3_prods.append(res_v3['prod'])
    
    a2_scores.append(res_a2['score'])
    a2_revs.append(res_a2['rev'])
    a2_prods.append(res_a2['prod'])

print("\n=========================================")
print(f"AVERAGE (20 Seeds)")
print(f"v17.3 Score: {statistics.mean(v3_scores):.1f}")
print(f"  A.2 Score: {statistics.mean(a2_scores):.1f}")
print(f"v17.3 Rev:   {statistics.mean(v3_revs):.1f}")
print(f"  A.2 Rev:   {statistics.mean(a2_revs):.1f}")
print(f"v17.3 Prod:  {statistics.mean(v3_prods):.1f}")
print(f"  A.2 Prod:  {statistics.mean(a2_prods):.1f}")

wins = sum(1 for v, a in zip(v3_scores, a2_scores) if a > v)
print(f"A.2 Win Rate: {wins}/20")
print("=========================================")
