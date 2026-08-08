"""Three-way comparison: V17.3 vs A.4 vs submission.py on seed 42."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kaggle_environments import make, utils
from submission_v17_3 import KaggricultureAgentV17 as V3
from submission_v17_3_a4 import KaggricultureAgentV17 as A4

SEED = 42

def run_match(agent0, agent1, label):
    env = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": SEED})
    steps = env.run([agent0, agent1])
    s0 = steps[-1][0].get("reward", 0)
    s1 = steps[-1][1].get("reward", 0)
    print(f"{label}: A0={s0:.0f} A1={s1:.0f}")
    return s0, s1

# V3 vs A4
print(f"Seed {SEED} direct matches:")
s_v3, s_a4 = run_match(lambda o: V3()(o), lambda o: A4()(o), "V3 vs A4")

# V3 vs submission.py
s_v3s, s_s1 = run_match(lambda o: V3()(o), "submission.py", "V3 vs submission.py")

# A4 vs submission.py  
s_a4s, s_s2 = run_match(lambda o: A4()(o), "submission.py", "A4 vs submission.py")

print(f"\nCross-comparison:")
print(f"  V17.3 vs submission.py: {s_v3s:.0f}")
print(f"  A.4    vs submission.py: {s_a4s:.0f}")
print(f"  Delta (A4 - V3): {s_a4s - s_v3s:+.0f}")
print(f"\n  V17.3 direct score: {s_v3:.0f}")
print(f"  A.4   direct score: {s_a4:.0f}")
