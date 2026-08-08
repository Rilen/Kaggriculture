"""Head-to-head: V17.3 vs A.4 on benchmark loss seeds."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kaggle_environments import make
from submission_v17_3 import KaggricultureAgentV17 as V3
from submission_v17_3_a4 import KaggricultureAgentV17 as A4

# Seeds where A.4 LOST in benchmark: 42,45,46,49,50,53,56,57,60
LOSS_SEEDS = [42, 45, 46, 49, 50, 53, 56, 57, 60]
WIN_SEEDS = [43, 44, 47, 48, 51, 52, 54, 55, 58, 59, 61]

results = []
for label, seeds in [("LOSS", LOSS_SEEDS), ("WIN", WIN_SEEDS)]:
    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": seed})
        ag_v3 = V3()
        ag_a4 = A4()
        steps = env.run([lambda o: ag_v3(o), lambda o: ag_a4(o)])
        sv = steps[-1][0].get("reward", 0)
        sa = steps[-1][1].get("reward", 0)
        delta = sa - sv
        results.append((seed, label, sv, sa, delta))
        w = "A4 WINS" if delta > 0 else ("V3 WINS" if delta < 0 else "TIE")
        print(f"  S{seed} [{label}]: V3={sv:.0f} A4={sa:.0f} d={delta:+.0f} {w}")

import statistics
wins = sum(1 for r in results if r[4] > 0)
losses = sum(1 for r in results if r[4] < 0)
ties = sum(1 for r in results if r[4] == 0)
deltas = [r[4] for r in results]
print(f"\nDirect H2H (n={len(results)}):")
print(f"  A4 Wins: {wins}/{len(results)} ({wins/len(results)*100:.0f}%)")
print(f"  Mean delta: {statistics.mean(deltas):.0f}")
print(f"  Mean A4 score: {statistics.mean([r[3] for r in results]):.0f}")
print(f"  Mean V3 score: {statistics.mean([r[2] for r in results]):.0f}")

# Split by benchmark group
loss_deltas = [r[4] for r in results if r[1] == "LOSS"]
win_deltas = [r[4] for r in results if r[1] == "WIN"]
print(f"\nBenchmark LOSS seeds (A4 'lost'): A4 beats V3 {sum(1 for d in loss_deltas if d>0)}/{len(loss_deltas)}, mean delta={statistics.mean(loss_deltas):.0f}")
print(f"Benchmark WIN seeds (A4 'won'):   A4 beats V3 {sum(1 for d in win_deltas if d>0)}/{len(win_deltas)}, mean delta={statistics.mean(win_deltas):.0f}")
