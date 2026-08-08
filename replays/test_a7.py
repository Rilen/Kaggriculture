import sys; sys.path.insert(0, r"C:\Users\rtl\Documents\Github\Kaggriculture")
from kaggle_environments import make
from submission_v17_3_a7_v3 import KaggricultureAgentV17 as A7
from collections import Counter

for seed in [42, 48, 50]:
    env = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": seed})
    ag = A7(); steps = env.run([lambda o: ag(o), "submission.py"])
    score = steps[-1][0].get("reward", 0)
    acts = Counter()
    for s in steps:
        a = s[0].get("action", {})
        if isinstance(a, dict):
            for wa in [a.get("farmer", [])] + a.get("hands", []):
                if wa: acts[wa[0]] += 1
    water = acts.get("WATER", 0); plant = acts.get("PLANT", 0)
    build_coop = acts.get("BUILD_COOP", 0)
    feed = acts.get("FEED", 0); care = acts.get("CARE", 0)
    harvest = acts.get("HARVEST", 0); fert = acts.get("FERTILIZE", 0)
    place = acts.get("PLACE", 0); pass_cnt = acts.get("PASS", 0)
    print(f"S{seed}: Score={score:.0f} WATER={water} PLANT={plant} COOP={build_coop} FEED={feed} CARE={care} HARVEST={harvest} FERT={fert} PLACE={place} PASS={pass_cnt}")
