import json
from collections import defaultdict
from kaggle_environments import make
from submission_v17_3_a1 import KaggricultureAgentV17

OFFICIAL_SEEDS = [
    42, 100, 256, 1337, 2024, 777, 999, 1234, 5555, 8888,
    314, 271, 1618, 9876, 5432, 1111, 2222, 3333, 4444, 7777
]

CROPS = {
    "STRAWBERRY": {"max": 4},
    "MELON": {"max": 5},
    "WHEAT": {"max": 3}
}

class DeadlockAuditAgent(KaggricultureAgentV17):
    def __init__(self):
        super().__init__()
        self.turn = 0
        self.deadlocks = defaultdict(int)
        self.deadlock_durations = defaultdict(list)
        self.current_deadlock = {} # worker_id -> (reason, start_turn)
        self.total_worker_turns_stuck = 0
        
    def _get_pass_reason(self, tile, wpos, winv, shed, seeds, day, hour, cows, sheep, empty_past):
        inv = winv or {}
        if tile is None:
            animal_in_shed = shed.get("COW", 0) + shed.get("SHEEP", 0)
            if animal_in_shed > 0 and empty_past == 0 and day <= 15:
                pass # returns BUILD_PASTURE
            elif hour <= 20:
                if seeds.get("STRAWBERRY", 0) > 0 or seeds.get("MELON", 0) > 0 or seeds.get("WHEAT", 0) > 0:
                    pass # returns PLANT
                else:
                    return "NO_SEED"
            else:
                return "TIME_CONSTRAINT"
            return "NO_SEED" # fallback for empty tile PASS
            
        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            crop = tile.get("crop", "")
            age = day - tile.get("planted_day", day)
            if age < CROPS.get(str(crop), {}).get("max", 99) and tile.get("yield_units", 0) == 0:
                watered = tile.get("watered_today") or (wpos and wpos in self.watered_this_day)
                if watered:
                    return "TARGET_NOT_MATURE"
            return "OTHER_PLANT"
            
        if isinstance(tile, dict) and tile.get("kind") == "PASTURE":
            if tile.get("animal") is None:
                return "NO_ANIMAL_ACTION"
            fed = tile.get("fed_today") or (wpos and wpos in self.fed_this_day)
            cared = tile.get("cared_today") or (wpos and wpos in self.cared_this_day)
            if not fed:
                if inv.get("WHEAT", 0) == 0:
                    return "NO_WHEAT_IN_HAND"
            return "OTHER_PASTURE"
            
        return "UNKNOWN"

    def __call__(self, obs):
        self.turn += 1
        
        o = obs.observation if hasattr(obs, 'observation') else obs
        player = o.get("player", 0)
        farm = o.get("farms", [])[player] if "farms" in o else {}
        hands = farm.get("hands", [])
        shed = farm.get("shed", {})
        seeds = farm.get("seeds", {})
        day = o.get("day", 1)
        hour = o.get("hour", 1)
        cows = sum(1 for row in farm.get('tiles', []) for t in row if isinstance(t, dict) and t.get('animal') == 'COW')
        sheep = sum(1 for row in farm.get('tiles', []) for t in row if isinstance(t, dict) and t.get('animal') == 'SHEEP')
        empty_past = sum(1 for row in farm.get('tiles', []) for t in row if isinstance(t, dict) and t.get('kind') == 'PASTURE' and not t.get('animal'))
        
        worker_positions = {0: tuple(farm.get("farmer", [0,0]))}
        for i, h in enumerate(hands):
            worker_positions[i+1] = tuple(h)
            
        worker_inventories = {0: farm.get("farmer_inventory", {})}
        for i, h in enumerate(hands):
            worker_inventories[i+1] = h.get("inventory", {}) if isinstance(h, dict) else {}
            
        # Before calling super, check which workers are on their target and about to PASS
        for wid, wpos in worker_positions.items():
            if wid in self.worker_targets:
                tx, ty = self.worker_targets[wid]
                if wpos == (tx, ty):
                    tile = self._tile_at(farm, wpos)
                    winv = worker_inventories.get(wid, {})
                    
                    # Call _decide to see if it returns PASS
                    action = self._decide(tile, shed, seeds, day, winv, wpos, hour, cows, sheep, empty_past)
                    
                    reason = None
                    if action[0] == "PASS":
                        reason = self._get_pass_reason(tile, wpos, winv, shed, seeds, day, hour, cows, sheep, empty_past)
                    else:
                        # Check if safe_return intercepts it
                        if not self._validate_action_preconditions(action, winv, tile, shed, seeds):
                            if action[0] == "HARVEST":
                                reason = "INVENTORY_FULL"
                            else:
                                reason = f"INTERCEPTED_{action[0]}"
                                
                    if reason:
                        self.total_worker_turns_stuck += 1
                        if wid not in self.current_deadlock:
                            self.current_deadlock[wid] = (reason, self.turn)
                    else:
                        if wid in self.current_deadlock:
                            r, start = self.current_deadlock[wid]
                            self.deadlock_durations[r].append(self.turn - start)
                            self.deadlocks[r] += 1
                            del self.current_deadlock[wid]
                else:
                    if wid in self.current_deadlock:
                        r, start = self.current_deadlock[wid]
                        self.deadlock_durations[r].append(self.turn - start)
                        self.deadlocks[r] += 1
                        del self.current_deadlock[wid]

        return super().__call__(obs)

def main():
    results = defaultdict(lambda: {"count": 0, "durations": []})
    total_stuck_turns = 0
    
    for seed in OFFICIAL_SEEDS:
        print(f"Seed {seed}")
        env = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": seed})
        ag = DeadlockAuditAgent()
        env.run([lambda o: ag(o), "random"])
        
        for r, count in ag.deadlocks.items():
            results[r]["count"] += count
            results[r]["durations"].extend(ag.deadlock_durations[r])
            
        for wid, (r, start) in ag.current_deadlock.items():
            results[r]["count"] += 1
            results[r]["durations"].append(ag.turn - start)
            
        total_stuck_turns += ag.total_worker_turns_stuck

    with open("replays/v17.3_a1_deadlock_raw.json", "w") as f:
        json.dump({"results": results, "total_stuck_turns": total_stuck_turns}, f)

if __name__ == "__main__":
    main()
