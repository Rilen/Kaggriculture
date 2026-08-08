import sys
from submission import KaggricultureAgentV17

def run_tests():
    agent = KaggricultureAgentV17()
    agent.last_day = 1 # initialize state
    
    # Mock farm state
    farm = {
        "farmer": [2, 2],
        "hands": [[3, 3]],
        "tiles": [
            [None, None, None, None, None],
            [None, None, None, None, None],
            [None, None, {"kind": "PASTURE", "animal": "COW", "fed_today": False}, None, None],
            [None, None, None, {"kind": "PLANT", "crop": "STRAWBERRY"}, None],
            [None, None, None, None, None],
        ]
    }
    
    obs = {
        "player": 0,
        "day": 1,
        "hour": 6,
        "farms": [farm],
        "private": {
            "shed": {"WHEAT": 5, "COW": 2},
            "seeds": {"STRAWBERRY": 0},
            "inventories": [{}, {}] # No wheat
        }
    }
    
    print("--- Teste 1: FEED sem WHEAT ---")
    res = agent(obs)
    farmer_act = res["farmer"]
    print(f"Farmer action (has WHEAT=0, on COW): {farmer_act}")
    assert farmer_act[0] != "FEED", "Falha: FEED emitido sem WHEAT"
    
    print("--- Teste 2: FEED com WHEAT ---")
    obs["private"]["inventories"][0] = {"WHEAT": 1}
    res = agent(obs)
    farmer_act = res["farmer"]
    print(f"Farmer action (has WHEAT=1, on COW): {farmer_act}")
    assert farmer_act[0] == "FEED", "Falha: FEED bloqueado incorretamente"
    
    print("--- Teste 3: PLACE sem animal ---")
    farm["tiles"][2][2] = {"kind": "PASTURE"} # Empty pasture
    obs["private"]["inventories"][0] = {} # No animal
    res = agent(obs)
    farmer_act = res["farmer"]
    print(f"Farmer action (Empty pasture, no animal): {farmer_act}")
    assert farmer_act[0] != "PLACE", "Falha: PLACE emitido sem animal"

    print("--- Teste 4: PLANT sem seed ---")
    farm["tiles"][2][2] = None # Empty tile
    obs["private"]["inventories"][0] = {} 
    res = agent(obs)
    farmer_act = res["farmer"]
    print(f"Farmer action (Empty tile, no seed for PLANT): {farmer_act}")
    assert farmer_act[0] != "PLANT", "Falha: PLANT emitido sem seed"

    print("--- Teste 5: Circuit Breaker ---")
    # Simulate a repeated valid-looking action that fails to transition state.
    # We will mock the history and state to trigger circuit breaker.
    agent.worker_history[0] = (["FEED"], [2, 2], "PASTURE-0-False", 2)
    farm["tiles"][2][2] = {"kind": "PASTURE", "animal": "COW", "fed_today": False}
    obs["private"]["inventories"][0] = {"WHEAT": 1} # Has WHEAT, so it WOULD pass precondition
    res = agent(obs)
    farmer_act = res["farmer"]
    print(f"Farmer action (3rd attempt of FEED): {farmer_act}")
    assert farmer_act[0] != "FEED", "Falha: Circuit breaker nao bloqueou a 3a tentativa"

    print("--- Teste 6: Recuperacao (BFS fallback) ---")
    # FEED necessario, WHEAT = 0
    obs["private"]["inventories"][0] = {}
    farm["tiles"][2][2] = {"kind": "PASTURE", "animal": "COW", "fed_today": False}
    agent.worker_history[0] = (["NORTH"], [2, 2], "PASTURE-0-False", 0) # reset history
    res = agent(obs)
    farmer_act = res["farmer"]
    print(f"Farmer action (FEED blocked, what does BFS do?): {farmer_act}")
    
    print("\nALL TESTS PASSED")

if __name__ == "__main__":
    run_tests()
