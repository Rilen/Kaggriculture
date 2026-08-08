import os
import json
from kaggle_environments import make

seeds = [42, 43, 44]

def run_smoke():
    print("--- SMOKE TEST: v17.2 vs v17.3 vs v17.3-A.1 ---")
    for seed in seeds:
        print(f"\\nSEED {seed}:")
        
        # v17.2
        env = make('kaggriculture', configuration={'episodeSteps': 3000, 'randomSeed': seed})
        env.run(['submission.py', 'submission.py'])
        score_v2 = env.steps[-1][0]['reward']
        print(f"v17.2     : {score_v2}")

        # v17.3
        env = make('kaggriculture', configuration={'episodeSteps': 3000, 'randomSeed': seed})
        env.run(['submission_v17_3.py', 'submission.py'])
        score_v3 = env.steps[-1][0]['reward']
        print(f"v17.3     : {score_v3}")
        
        # v17.3-A.1
        env = make('kaggriculture', configuration={'episodeSteps': 3000, 'randomSeed': seed})
        env.run(['submission_v17_3_a1.py', 'submission.py'])
        score_a1 = env.steps[-1][0]['reward']
        print(f"v17.3-A.1 : {score_a1}")

if __name__ == '__main__':
    run_smoke()
