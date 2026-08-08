import os
import json
from kaggle_environments import make
from submission_v17_3 import KaggricultureAgentV17

# Using the official 20 seeds
OFFICIAL_SEEDS = [
    42, 100, 256, 1337, 2024, 777, 999, 1234, 5555, 8888,
    314, 271, 1618, 9876, 5432, 1111, 2222, 3333, 4444, 7777
]

def main():
    results = {}
    
    for seed in OFFICIAL_SEEDS:
        print(f"Running Seed {seed}...")
        
        # We must instantiate a new agent per match
        agent = KaggricultureAgentV17()
        
        env = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": seed})
        # Use our instance directly to preserve telemetry access
        env.run([agent, "submission.py"])
        
        score = env.steps[-1][0]['reward']
        
        results[seed] = {
            "score": score,
            "bfs_calls": agent.telemetry.get("replan_count", 0), # Wait, bfs calls? Let's just dump telemetry
            **agent.telemetry
        }
        
        # For productive actions, we'd need to extract them from the agent if not in telemetry.
        # But wait, the agent doesn't track productive actions in telemetry!
        
    os.makedirs("replays", exist_ok=True)
    with open("replays/v17.3_patchA_results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    print("Benchmark complete!")

if __name__ == "__main__":
    main()
