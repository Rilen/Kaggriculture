import sys
sys.path.insert(0, r"C:\Users\rtl\Documents\Github\Kaggriculture")
from kaggle_environments import make
from submission_v17_3_a5 import KaggricultureAgentV17 as A5
from collections import Counter
import statistics

for seed in [42, 48, 50]:
    env = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": seed})
    ag = A5()
    steps = env.run([lambda o: ag(o), "submission.py"])
    score = steps[-1][0].get("reward", 0)
    
    acts = Counter()
    for s in steps:
        a = s[0].get("action", {})
        if isinstance(a, dict):
            for wa in [a.get("farmer", [])] + a.get("hands", []):
                if wa: acts[wa[0]] += 1
    
    water = acts.get("WATER", 0)
    plant = acts.get("PLANT", 0)
    print(f"A.5 S{seed}: Score={score:.0f} WATER={water} PLANT={plant} wp={water/max(plant,1):.1f} FEED={acts.get('FEED',0)}")
