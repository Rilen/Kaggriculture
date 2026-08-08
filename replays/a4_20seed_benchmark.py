"""20-seed A.4 CARE filter benchmark — isolated subprocess, paired comparison."""
import subprocess, json, statistics, math, sys

SEEDS = list(range(42, 62))
MATCH = "run_single_match.py"

def run_one(agent, seed):
    cmd = ["python", MATCH, agent, str(seed)]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    for line in reversed(res.stdout.splitlines()):
        line = line.strip()
        if line.startswith('{'):
            return json.loads(line)
    return {"score": 0, "rev": 0, "prod": 0}

print(f"A.4 CARE Filter — 20-seed benchmark")
print(f"Seeds: {SEEDS[0]}-{SEEDS[-1]} | Agents: v17.3 vs v17.3_a4")
print()

v3_scores, a4_scores = [], []
v3_revs, a4_revs = [], []
v3_prods, a4_prods = [], []

for seed in SEEDS:
    res_v3 = run_one("submission_v17_3.py", seed)
    res_a4 = run_one("submission_v17_3_a4.py", seed)
    
    v3_scores.append(res_v3["score"]); a4_scores.append(res_a4["score"])
    v3_revs.append(res_v3["rev"]); a4_revs.append(res_a4["rev"])
    v3_prods.append(res_v3["prod"]); a4_prods.append(res_a4["prod"])
    
    delta = res_a4["score"] - res_v3["score"]
    w = "WIN" if delta > 0 else ("LOSS" if delta < 0 else "TIE")
    print(f"  S{seed}: V3={res_v3['score']:.0f} A4={res_a4['score']:.0f} d={delta:+.0f} {w}")

def m(xs): return statistics.mean(xs)
def s(xs): return statistics.stdev(xs) if len(xs)>1 else 0
def median(xs): return statistics.median(xs)

diffs_score = [a-v for a,v in zip(a4_scores, v3_scores)]
diffs_rev = [a-v for a,v in zip(a4_revs, v3_revs)]
diffs_prod = [a-v for a,v in zip(a4_prods, v3_prods)]

def ci95(diffs):
    n = len(diffs); md = m(diffs); sd = s(diffs)
    if n < 2 or sd == 0: return (md, md)
    se = sd / math.sqrt(n)
    t = 2.093
    return (md - t*se, md + t*se)

def cohens_d(xs, ys):
    d = m(xs) - m(ys)
    ps = ((s(xs)**2 + s(ys)**2)/2)**0.5 if len(xs)>1 and len(ys)>1 else 1e-9
    return d/ps if ps else 0

print(f"\n=== RESULTS (n={len(SEEDS)}) ===")
ci_s = ci95(diffs_score); ci_r = ci95(diffs_rev); ci_p = ci95(diffs_prod)
print(f"Score:    V3={m(v3_scores):.0f} A4={m(a4_scores):.0f} d={m(diffs_score):+.0f} [{ci_s[0]:.0f},{ci_s[1]:.0f}] d={cohens_d(a4_scores,v3_scores):+.2f}")
print(f"Revenue:  V3={m(v3_revs):.0f} A4={m(a4_revs):.0f} d={m(diffs_rev):+.0f} [{ci_r[0]:.0f},{ci_r[1]:.0f}]")
print(f"ProdActs: V3={m(v3_prods):.0f} A4={m(a4_prods):.0f} d={m(diffs_prod):+.0f} [{ci_p[0]:.0f},{ci_p[1]:.0f}]")

rpa_v3 = [r/p if p else 0 for r,p in zip(v3_revs, v3_prods)]
rpa_a4 = [r/p if p else 0 for r,p in zip(a4_revs, a4_prods)]
print(f"RPA:      V3={m(rpa_v3):.1f} A4={m(rpa_a4):.1f} d={m([a-v for a,v in zip(rpa_a4,rpa_v3)]):+.1f}")

wins = sum(1 for d in diffs_score if d > 0)
losses = sum(1 for d in diffs_score if d < 0)
print(f"Win/Loss: {wins}/{losses} ({wins/len(SEEDS)*100:.0f}% WR)")
print(f"Median:   V3={median(v3_scores):.0f} A4={median(a4_scores):.0f}")

# Save
with open("replays/a4_benchmark_results.json", "w") as f:
    json.dump({
        "seeds": SEEDS, "v3_scores": v3_scores, "a4_scores": a4_scores,
        "v3_revs": v3_revs, "a4_revs": a4_revs, "v3_prods": v3_prods, "a4_prods": a4_prods,
        "mean_delta_score": m(diffs_score), "win_rate": wins/len(SEEDS),
        "cohens_d_score": cohens_d(a4_scores, v3_scores),
        "ci95_score": list(ci_s),
    }, f, indent=2)

print("\nSaved to replays/a4_benchmark_results.json")
