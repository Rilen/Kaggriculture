from kaggle_environments import make
from submission_v17_3_a2 import KaggricultureAgentV17 as A2Agent
from submission_v17_3 import KaggricultureAgentV17 as V3Agent

seed = 50

env = make('kaggriculture', configuration={'episodeSteps': 3000, 'randomSeed': seed})
ag_a2 = A2Agent()
steps_a2 = env.run([lambda o: ag_a2(o), 'submission.py'])
score_a2 = steps_a2[-1][0].get('reward', 0)
tel = ag_a2.telemetry
print(f"Seed {seed} - A.2 Score: {score_a2}")
print(f"Telemetry:")
for k, v in tel.items():
    print(f"  {k}: {v}")
    
import collections
action_counts = collections.Counter()
for s in steps_a2:
    obs = s[0].get("observation")
    act = s[0].get("action")
    if not act: continue
    if isinstance(act, dict):
        f = act.get("farmer", ["PASS"])[0]
        action_counts[f] += 1
        for h in act.get("hands", []):
            if isinstance(h, list) and len(h) > 0:
                action_counts[h[0]] += 1
print(f"Actions: {action_counts}")
