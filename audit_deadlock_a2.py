from kaggle_environments import make
from submission_v17_3_a2 import KaggricultureAgentV17
import json
from collections import defaultdict

def run_deadlock_audit():
    SEEDS = [42, 43, 44]
    all_deadlocks = []
    
    for seed in SEEDS:
        print(f"Running seed {seed}...")
        env = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": seed})
        ag = KaggricultureAgentV17()
        
        # We need to track exactly when a worker returns PASS while AT its valid target!
        stuck_turns = defaultdict(int)
        
        # Patch the agent to hook into worker_act
        original_call = ag.__call__
        
        def patched_call(obs):
            res = original_call(obs)
            
            # Check worker_targets and worker_failures
            player = obs.get("player", 0)
            farm = obs.get("farms", [])[player] if "farms" in obs else {}
            farmer_pos = tuple(farm.get("farmer", [0, 0]))
            hands_pos = [tuple(h) for h in farm.get("hands", [])]
            
            positions = {0: farmer_pos}
            for i, hp in enumerate(hands_pos):
                positions[i+1] = hp
                
            for w_id, target_info in ag.worker_targets.items():
                tx, ty, task_name = target_info
                wpos = positions.get(w_id)
                if wpos == (tx, ty):
                    # Worker is AT the target!
                    # What did the worker do this turn?
                    act = res["farmer"][0] if w_id == 0 else res["hands"][w_id-1][0]
                    if act == "PASS":
                        # STUCK!
                        winv = obs["private"]["inventories"][w_id] if obs["private"]["inventories"] else {}
                        stuck_turns[(w_id, task_name, wpos, str(winv))] += 1
                        all_deadlocks.append({
                            "seed": seed,
                            "turn": obs["step"],
                            "worker_id": w_id,
                            "task_name": task_name,
                            "wpos": wpos,
                            "winv": winv,
                            "action": act,
                            "circuit_breaker": ag.worker_history.get(w_id)
                        })
            return res
            
        ag.__call__ = patched_call
        env.run([lambda o: ag(o), "submission.py"])
        
    print(f"Total deadlock events recorded: {len(all_deadlocks)}")
    
    # Analyze the most common deadlocks
    from collections import Counter
    summary = Counter()
    for d in all_deadlocks:
        sig = f"Task: {d['task_name']}, Inv: {d['winv']}"
        summary[sig] += 1
        
    for k, v in summary.most_common(10):
        print(f"{v} times: {k}")

if __name__ == '__main__':
    run_deadlock_audit()
