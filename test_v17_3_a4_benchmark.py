"""V17.3 A.4 — 20-seed isolated benchmark with paired statistics."""
import subprocess
import json
import sys
import statistics
import math

SEEDS = list(range(42, 62))
MATCH_SCRIPT = "run_single_match.py"

def run_isolated(agent_file, seed):
    cmd = ["python", MATCH_SCRIPT, agent_file, str(seed)]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    for line in reversed(res.stdout.splitlines()):
        line = line.strip()
        if line.startswith('{'):
            data = json.loads(line)
            return data
    return {"score": 0, "rev": 0, "prod": 0, "tce": 0, "rpa": 0}

print(f"V17.3 A.4 — 20-seed isolated benchmark")
print(f"Seeds: {SEEDS[0]}-{SEEDS[-1]}")
print(f"Agents: submission_v17_3.py vs submission_v17_3_a4.py")
print(f"Opponent: submission.py")
print(f"Method: subprocess isolation (python run_single_match.py)\n")

v3_scores, v3_revs, v3_prods = [], [], []
a4_scores, a4_revs, a4_prods = [], [], []

for seed in SEEDS:
    print(f"Seed {seed}...", end=" ", flush=True)
    
    res_v3 = run_isolated("submission_v17_3.py", seed)
    print(f"V17.3:{res_v3['score']:.0f}", end=" | ", flush=True)
    
    res_a4 = run_isolated("submission_v17_3_a4.py", seed)
    print(f"A.4:{res_a4['score']:.0f}", flush=True)
    
    v3_scores.append(res_v3['score'])
    v3_revs.append(res_v3['rev'])
    v3_prods.append(res_v3['prod'])
    a4_scores.append(res_a4['score'])
    a4_revs.append(res_a4['rev'])
    a4_prods.append(res_a4['prod'])

diffs = [a - v for a, v in zip(a4_scores, v3_scores)]
diffs_rev = [a - v for a, v in zip(a4_revs, v3_revs)]
diffs_prod = [a - v for a, v in zip(a4_prods, v3_prods)]

def mean(xs): return statistics.mean(xs)
def median(xs): return statistics.median(xs)
def stdev(xs): return statistics.stdev(xs) if len(xs) > 1 else 0
def cohens_d(xs, ys):
    paired_diffs = [x - y for x, y in zip(xs, ys)]
    md = mean(paired_diffs)
    sd = stdev(paired_diffs)
    return md / sd if sd else 0

# Paired t-test 95% CI
def paired_ci(diffs, confidence=0.95):
    n = len(diffs)
    md = mean(diffs)
    sd = stdev(diffs)
    if sd == 0 or n < 2:
        return (md, md)
    se = sd / math.sqrt(n)
    t_val = 2.093  # t-distribution for n=20, df=19, 95%
    return (md - t_val * se, md + t_val * se)

print(f"\n{'='*70}")
print(f"BENCHMARK RESULTS (20 seeds, subprocess isolation)")
print(f"{'='*70}")

print(f"\n{'Metric':<20} {'V17.3 Mean':>12} {'A.4 Mean':>12} {'Delta':>12} {'95% CI':>16} {'d':>8}")
print(f"{'-'*20} {'-'*12} {'-'*12} {'-'*12} {'-'*16} {'-'*8}")

ci_scores = paired_ci(diffs)
ci_revs = paired_ci(diffs_rev)
ci_prods = paired_ci(diffs_prod)

print(f"{'Score':<20} {mean(v3_scores):>12.1f} {mean(a4_scores):>12.1f} {mean(diffs):>+12.1f} {'[' + f'{ci_scores[0]:.0f},{ci_scores[1]:.0f}' + ']':>16} {cohens_d(a4_scores, v3_scores):>+8.2f}")
print(f"{'Revenue':<20} {mean(v3_revs):>12.1f} {mean(a4_revs):>12.1f} {mean(diffs_rev):>+12.1f} {'[' + f'{ci_revs[0]:.0f},{ci_revs[1]:.0f}' + ']':>16} {cohens_d(a4_revs, v3_revs):>+8.2f}")
print(f"{'Productive Acts':<20} {mean(v3_prods):>12.1f} {mean(a4_prods):>12.1f} {mean(diffs_prod):>+12.1f} {'[' + f'{ci_prods[0]:.0f},{ci_prods[1]:.0f}' + ']':>16} {cohens_d(a4_prods, v3_prods):>+8.2f}")

rpa_v3 = [r / p if p else 0 for r, p in zip(v3_revs, v3_prods)]
rpa_a4 = [r / p if p else 0 for r, p in zip(a4_revs, a4_prods)]
print(f"{'RPA':<20} {mean(rpa_v3):>12.2f} {mean(rpa_a4):>12.2f} {mean([a-v for a,v in zip(rpa_a4,rpa_v3)]):>+12.2f}")

print(f"\n{'='*70}")
print(f"DISTRIBUTION")
print(f"{'='*70}")

print(f"\n{'Metric':<20} {'V17.3 Med':>12} {'A.4 Med':>12} {'V17.3 Std':>12} {'A.4 Std':>12}")
print(f"{'-'*20} {'-'*12} {'-'*12} {'-'*12} {'-'*12}")
print(f"{'Score':<20} {median(v3_scores):>12.1f} {median(a4_scores):>12.1f} {stdev(v3_scores):>12.1f} {stdev(a4_scores):>12.1f}")
print(f"{'Revenue':<20} {median(v3_revs):>12.1f} {median(a4_revs):>12.1f} {stdev(v3_revs):>12.1f} {stdev(a4_revs):>12.1f}")

wins = sum(1 for d in diffs if d > 0)
losses = sum(1 for d in diffs if d < 0)
ties = sum(1 for d in diffs if d == 0)
print(f"\nWin/Loss/Tie: {wins}/{losses}/{ties}")
print(f"Win Rate: {wins/len(SEEDS)*100:.1f}%")

# Per-seed table
print(f"\n{'='*70}")
print(f"PER-SEED DETAIL")
print(f"{'='*70}")
print(f"{'Seed':<6} {'V17.3 Score':>12} {'A.4 Score':>12} {'Delta':>10} {'Win':>6}")
for i, seed in enumerate(SEEDS):
    w = "YES" if diffs[i] > 0 else ("TIE" if diffs[i] == 0 else "NO")
    print(f"{seed:<6} {v3_scores[i]:>12.1f} {a4_scores[i]:>12.1f} {diffs[i]:>+10.1f} {w:>6}")

# Save JSON
output = {
    "seeds": SEEDS,
    "v3_scores": v3_scores,
    "v3_revs": v3_revs,
    "v3_prods": v3_prods,
    "a4_scores": a4_scores,
    "a4_revs": a4_revs,
    "a4_prods": a4_prods,
    "mean_score_v3": mean(v3_scores),
    "mean_score_a4": mean(a4_scores),
    "mean_delta_score": mean(diffs),
    "win_rate": wins / len(SEEDS),
    "cohens_d_score": cohens_d(a4_scores, v3_scores),
    "paired_ci_95": list(ci_scores),
}
with open("a4_benchmark_results.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\nResults saved to a4_benchmark_results.json")
