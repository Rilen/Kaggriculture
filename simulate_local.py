"""
Local Simulation Harness — Kaggriculture
Runs our agent against a recorded opponent replay without deploying to Kaggle.

IMPORTANT: This uses the RECORDED observations from the replay.
It does NOT re-simulate the full game engine (Kaggle does not provide that).
Instead, it shows what OUR agent would do given the same observations
that the recorded opponent (e.g., Seb) saw during the episode.

This is useful for:
1. Comparing action distributions (our agent vs recorded opponent)
2. Identifying strategic differences
3. A/B testing without deploying to Kaggle
"""
import json
import copy
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from submission import agent


def load_replay(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def simulate_episode(replay_path, agent_player=1, verbose=True):
    """
    Simulate one episode from a replay file.
    agent_player: which player index our agent controls (0 or 1)
    The other player uses recorded actions from the replay.
    
    NOTE: This replays the SAME observations from the original game.
    Our agent's actions do NOT change the game state for subsequent steps.
    This is an "offline evaluation" of what our agent would have done.
    """
    data = load_replay(replay_path)
    steps = data["steps"]
    agents = data["info"]["Agents"]
    
    print(f"=== SIMULATION ===")
    print(f"Episode: {data.get('id')}")
    print(f"Agents: {agents[0]['Name']} vs {agents[1]['Name']}")
    print(f"Total steps: {len(steps)}")
    print(f"Mode: Offline evaluation (replaying recorded observations)")
    print()
    
    opp_idx = 1 - agent_player
    opp_name = agents[opp_idx]['Name']
    our_name = "Our Agent (A.11)"
    
    our_money = []
    opp_money = []
    our_hands = []
    opp_hands = []
    our_market = []
    opp_market = []
    
    for step_idx, step in enumerate(steps):
        p0 = step[0]
        p1 = step[1]
        
        # Choose which observation to give our agent
        if agent_player == 1:
            our_obs = p1["observation"]
            opp_obs = p0["observation"]
            our_recorded = p1["action"]
            opp_recorded = p0["action"]
        else:
            our_obs = p0["observation"]
            opp_obs = p1["observation"]
            our_recorded = p0["action"]
            opp_recorded = p1["action"]
        
        day = our_obs.get("day", 0)
        hour = our_obs.get("hour", 0)
        
        # Track money from recorded observations
        our_money.append(our_obs["farms"][agent_player]["money"])
        opp_money.append(opp_obs["farms"][opp_idx]["money"])
        
        # Run our agent
        our_action = agent(copy.deepcopy(our_obs))
        
        # Track recorded opponent actions
        if opp_recorded and "hands" in opp_recorded:
            for h in opp_recorded.get("hands", []):
                if h and isinstance(h, list):
                    opp_hands.append(h[0])
            for m in opp_recorded.get("market", []):
                if m and isinstance(m, list):
                    opp_market.append(m[0])
        
        # Track our agent actions
        if our_action and "hands" in our_action:
            for h in our_action.get("hands", []):
                if h and isinstance(h, list):
                    our_hands.append(h[0])
            for m in our_action.get("market", []):
                if m and isinstance(m, list):
                    our_market.append(m[0])
        
        if verbose and step_idx % 120 == 0:
            print(f"Step {step_idx:3d} | Day {day:2d} Hour {hour:2d} | "
                  f"{opp_name}: ${opp_money[-1]:8.0f} | {our_name}: ${our_money[-1]:8.0f}")
    
    # Use final money from original replay (since we're not re-simulating)
    # But note: if our agent took different actions, final money would differ
    our_final = our_money[-1]
    opp_final = opp_money[-1]
    
    print()
    print(f"=== FINAL RESULTS (from recorded observations) ===")
    print(f"{opp_name}: ${opp_final:,.0f}")
    print(f"{our_name}: ${our_final:,.0f}")
    
    if our_final > opp_final:
        print(f"RESULT: WIN (+${our_final - opp_final:,.0f})")
    elif our_final < opp_final:
        print(f"RESULT: LOSS (-${opp_final - our_final:,.0f})")
    else:
        print("RESULT: TIE")
    
    print()
    print("NOTE: This uses original replay money because the game engine")
    print("      is not re-simulated. Our agent's actions are recorded")
    print("      for comparison but don't change game state.")
    
    return {
        "our_final": our_final,
        "opp_final": opp_final,
        "our_money_trace": our_money,
        "opp_money_trace": opp_money,
        "our_hands": our_hands,
        "opp_hands": opp_hands,
        "our_market": our_market,
        "opp_market": opp_market,
    }


def analyze_actions(result):
    """Analyze action distribution from simulation."""
    from collections import Counter
    
    print()
    print("=== ACTION DISTRIBUTION COMPARISON ===")
    print()
    print("OUR HANDS:")
    for action, count in Counter(result["our_hands"]).most_common():
        pct = count / len(result["our_hands"]) * 100 if result["our_hands"] else 0
        print(f"  {action:20s}: {count:5d} ({pct:5.1f}%)")
    
    print()
    print("OPPONENT HANDS:")
    for action, count in Counter(result["opp_hands"]).most_common():
        pct = count / len(result["opp_hands"]) * 100 if result["opp_hands"] else 0
        print(f"  {action:20s}: {count:5d} ({pct:5.1f}%)")
    
    print()
    print("=== MARKET ORDERS COMPARISON ===")
    print()
    print("OUR MARKET:")
    for action, count in Counter(result["our_market"]).most_common():
        print(f"  {action:20s}: {count:5d}")
    
    print()
    print("OPPONENT MARKET:")
    for action, count in Counter(result["opp_market"]).most_common():
        print(f"  {action:20s}: {count:5d}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Local Kaggriculture Simulation")
    parser.add_argument("--episode", type=str, default="seb_episodes/episode-91150561-replay.json",
                        help="Path to replay JSON")
    parser.add_argument("--player", type=int, default=1, choices=[0, 1],
                        help="Which player our agent controls (0 or 1)")
    parser.add_argument("--quiet", action="store_true", help="Suppress step-by-step output")
    args = parser.parse_args()
    
    result = simulate_episode(args.episode, agent_player=args.player, verbose=not args.quiet)
    analyze_actions(result)

