import json, os, collections

REPLAYS = [
    ("90150089", "replays/episode-90150089-replay.json"),
    ("90070951", "replays/episode-90070951-replay.json"),
    ("90070264", "replays/episode-90070264-replay.json"),
    ("90068877", "replays/episode-90068877-replay.json"),
]

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def analyze(rid, data):
    steps = data["steps"]
    money_ours = []
    money_opp = []
    opp_seed_buys = collections.Counter()
    opp_plant_by_day = collections.defaultdict(lambda: collections.Counter())
    opp_unique_plants = collections.Counter()
    idle_count = 0
    total_worker_actions = 0
    target_steps = {100, 200, 300}
    snapshots = {}

    for idx, step_list in enumerate(steps, start=1):
        if not isinstance(step_list, list) or len(step_list) != 2:
            continue
        for agent_idx, step in enumerate(step_list):
            obs = step.get("observation", {})
            player = obs.get("player", agent_idx)
            farm = obs.get("farms", [{}])[player]
            money = farm.get("money", 0)
            if player == 0:
                money_ours.append((idx, money))
                if idx in target_steps:
                    snapshots[idx] = {"ours": money}
            else:
                money_opp.append((idx, money))
                if idx in target_steps:
                    if idx not in snapshots:
                        snapshots[idx] = {}
                    snapshots[idx]["opp"] = money

            action = step.get("action", {})
            farmer_actions = action.get("farmer", []) if isinstance(action, dict) else []
            hands_actions = action.get("hands", []) if isinstance(action, dict) else []
            all_actions = [farmer_actions] + hands_actions

            tiles = farm.get("tiles", [])
            empty_tiles = 0
            if isinstance(tiles, list):
                for row in tiles:
                    if isinstance(row, list):
                        for t in row:
                            if t is None or t == {} or t == []:
                                empty_tiles += 1

            has_capacity = empty_tiles > 0
            has_money = money > 500

            for unit_actions in all_actions:
                if not isinstance(unit_actions, list):
                    continue
                for a in unit_actions:
                    total_worker_actions += 1
                    if a is None or a == "None" or a == "PASS":
                        if has_capacity and has_money:
                            idle_count += 1

            if player != 0:
                market_orders = action.get("market", []) if isinstance(action, dict) else []
                for order in market_orders:
                    if isinstance(order, list) and len(order) >= 2:
                        cmd = order[0]
                        arg = order[1] if len(order) > 1 else None
                        if cmd == "BUY_SEED" and arg:
                            opp_seed_buys[arg] += 1

                if isinstance(tiles, list):
                    seen = set()
                    for y, row in enumerate(tiles):
                        if not isinstance(row, list):
                            continue
                        for x, t in enumerate(row):
                            if isinstance(t, dict) and t.get("kind") == "PLANT":
                                crop = t.get("crop")
                                day = obs.get("day")
                                key = (x, y, crop)
                                if key not in seen:
                                    seen.add(key)
                                    opp_unique_plants[crop] += 1
                                    opp_plant_by_day[day][crop] += 1

    print(f"=== Replay {rid} ===")
    print("Money snapshots (step 100/200/300):")
    for s in sorted(snapshots):
        ours = snapshots[s].get("ours", "?")
        opp = snapshots[s].get("opp", "?")
        print(f" step {s}: ours={ours} opp={opp}")

    print("Opponent unique plant tile counts:")
    for crop, cnt in opp_unique_plants.most_common():
        print(f" {crop}: {cnt}")

    print("Opponent seed buys:")
    for crop, cnt in opp_seed_buys.most_common():
        print(f" {crop}: {cnt}")

    print("Opponent plantings by day (top 10 days by count):")
    top_days = sorted(opp_plant_by_day.items(), key=lambda kv: sum(kv[1].values()), reverse=True)[:10]
    for day, counts in top_days:
        print(f" day {day}: {dict(counts)}")

    print(f"Idle actions with empty space+money: {idle_count} / {total_worker_actions}")
    print()

for rid, path in REPLAYS:
    analyze(rid, load(path))
