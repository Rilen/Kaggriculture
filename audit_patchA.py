import json
from collections import defaultdict
from kaggle_environments import make
from submission_v17_3 import KaggricultureAgentV17

OFFICIAL_SEEDS = [
    42, 100, 256, 1337, 2024, 777, 999, 1234, 5555, 8888,
    314, 271, 1618, 9876, 5432, 1111, 2222, 3333, 4444, 7777
]

class AuditAgent(KaggricultureAgentV17):
    def __init__(self):
        super().__init__()
        self.turn = 0
        self.audit_log = []
        self.target_history = defaultdict(list) # worker_id -> list of (turn, target)
        self.released_claims = [] # list of dicts with release info
        self.replan_events = []
        
        self.last_circuit_breaker = 0
        self.last_unreachable = 0
        self.last_invalid = 0
        self.last_arrival = 0
        self.last_prod = 0

    def __call__(self, obs):
        self.turn += 1
        
        old_targets = self.worker_targets.copy()
        old_cb = self.telemetry["circuit_breaker_triggered"]
        
        result = super().__call__(obs)
        
        new_targets = self.worker_targets.copy()
        new_cb = self.telemetry["circuit_breaker_triggered"]
        
        # Track Replans (Circuit Breaker)
        if new_cb > old_cb:
            self.replan_events.append({
                "turn": self.turn,
                "amount": new_cb - old_cb
            })
            
        # Track Releases
        for wid, target in old_targets.items():
            if wid not in new_targets or new_targets[wid] != target:
                # Target was released or changed
                reason = "UNKNOWN"
                
                # We can deduce the reason by checking telemetry diffs, but since multiple workers might release in one turn, it's an approximation.
                # However, let's just record the release event and the target.
                self.released_claims.append({
                    "turn": self.turn,
                    "worker_id": wid,
                    "target": target,
                    "new_target": new_targets.get(wid)
                })

        return result

def run_audit():
    all_releases = []
    all_replans = []
    
    # We will simulate the failure limits analytically.
    # To do this, we just need to track how many times BFS fails consecutively.
    # But for now, we'll just run standard v17.3 and observe.
    
    for seed in OFFICIAL_SEEDS:
        print(f"Running seed {seed}...")
        env = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": seed})
        ag = AuditAgent()
        
        steps = env.run([lambda o: ag(o), "random"])
        
        # After run, analyze the released claims for this seed
        # A = alcançável depois? 
        # B = consumido por outro?
        
        for release in ag.released_claims:
            release["seed"] = seed
            all_releases.append(release)
            
        for rep in ag.replan_events:
            rep["seed"] = seed
            all_replans.append(rep)
            
    with open("replays/v17.3_patchA_audit_raw.json", "w") as f:
        json.dump({"releases": all_releases, "replans": all_replans}, f)
        
    print("Audit data generated.")

if __name__ == "__main__":
    run_audit()
