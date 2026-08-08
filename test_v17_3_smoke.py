from kaggle_environments import make

seeds = [42, 43, 44]

def run_smoke():
    for seed in seeds:
        print(f"--- SEED {seed} ---")
        
        # v17.2
        env = make('kaggriculture', configuration={'episodeSteps': 3000, 'randomSeed': seed})
        env.run(['submission.py', 'submission.py'])
        score_v17_2 = env.steps[-1][0]['reward']
        print(f"v17.2 Score: {score_v17_2}")

        # v17.3
        env = make('kaggriculture', configuration={'episodeSteps': 3000, 'randomSeed': seed})
        env.run(['submission_v17_3.py', 'submission.py'])
        score_v17_3 = env.steps[-1][0]['reward']
        print(f"v17.3 Score: {score_v17_3}")

if __name__ == '__main__':
    run_smoke()
