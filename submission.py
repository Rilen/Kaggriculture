"""
Kaggriculture Autonomous AI Agent — Version 9 (v9)

[v8] BFS + Expansao + Pecuaria + Arbitragem Municipal
[v9] Horizonte de Eventos + Espionagem do Oponente + Hour 23 Flush
"""

from collections import deque

CROPS = {
    "WHEAT":      {"first": 2,  "max": 4,  "seed_cost": 10,  "price": 25},
    "CARROT":     {"first": 2,  "max": 3,  "seed_cost": 20,  "price": 35},
    "TOMATO":     {"first": 8,  "max": 11, "seed_cost": 50,  "price": 60},
    "STRAWBERRY": {"first": 10, "max": 16, "seed_cost": 100, "price": 120},
    "MELON":      {"first": 10, "max": 10, "seed_cost": 80,  "price": 250},
}

PLANT_PRIORITY = ["MELON", "STRAWBERRY", "TOMATO", "CARROT", "WHEAT"]

ANIMALS = {
    "GOOSE": {"buy_cost": 300, "needs": "COOP",    "product": "EGG",  "price": 50},
    "COW":   {"buy_cost": 400, "needs": "PASTURE", "product": "MILK", "price": 160},
    "SHEEP": {"buy_cost": 500, "needs": "PASTURE", "product": "WOOL", "price": 200},
}

SHOP_DEMAND = {
    "BAKERY":         ["EGG", "WHEAT"],
    "PIZZA_SHOP":     ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT":    ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE":     ["WOOL", "WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE":       ["CARROT", "CARROT"],
    "SMOOTHIE_SHOP":  ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}

MAX_MARKET_ORDERS = 10
SHED_SOFT_CAP = 75
PREMIUM_THRESHOLD = 100
SHED_HARD_CAP = 100


class KaggricultureAgentV9:
    def __init__(self):
        self.last_day = -1
        self.watered_this_day = set()
        self.fed_this_day = set()
        self.price_history = {}
        self.animals_bought = 0

    @staticmethod
    def _tile_at(farm, pos):
        if not isinstance(pos, (list, tuple)) or len(pos) != 2:
            return None
        x, y = pos
        tiles = farm.get("tiles", [])
        if not (0 <= y < len(tiles)):
            return None
        row = tiles[y]
        if not isinstance(row, list) or not (0 <= x < len(row)):
            return None
        return row[x]

    @staticmethod
    def _is_empty_unlocked(tile):
        return tile is None

    @staticmethod
    def _is_animal_struct(tile):
        return isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE")

    @staticmethod
    def _is_shed_adjacent(pos, board_size=10):
        half = board_size // 2
        x, y = pos
        return x in (half - 1, half) and y in (half - 1, half)

    def _bfs_nearest(self, start, condition, farm, exclude):
        sx, sy = start
        tiles = farm.get("tiles", [])
        board_h = len(tiles)
        board_w = len(tiles[0]) if board_h > 0 else 0
        if board_h == 0:
            return (None, None, None)

        queue = deque()
        visited = set()
        queue.append((sx, sy, None))
        visited.add((sx, sy))

        while queue:
            x, y, first_dir = queue.popleft()
            tile = self._tile_at(farm, (x, y))

            if (x, y) != (sx, sy):
                if tile != "LOCKED" and condition(tile, x, y) and (x, y) not in exclude:
                    return (x, y, first_dir)

            for dx, dy, dname in [(0, -1, "NORTH"), (0, 1, "SOUTH"), (-1, 0, "WEST"), (1, 0, "EAST")]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited and 0 <= nx < board_w and 0 <= ny < board_h:
                    visited.add((nx, ny))
                    ndir = first_dir if first_dir else dname
                    queue.append((nx, ny, ndir))

        return (None, None, None)

    def _scan_tiles(self, farm, day):
        tiles = farm.get("tiles", [])
        tasks = {"water_needed": [], "feed_needed": [], "harvest_ready": []}
        
        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                if not isinstance(tile, dict):
                    continue
                kind = tile.get("kind")
                if kind == "PLANT":
                    crop = tile.get("crop")
                    info = CROPS.get(crop, {})
                    age = day - tile.get("planted_day", day)
                    if age >= info.get("max", 2) or (crop in ("TOMATO", "STRAWBERRY") and age >= info.get("first", 2) and tile.get("yield_units", 0) > 0):
                        tasks["harvest_ready"].append((x, y))
                    if not tile.get("watered_today") and (x, y) not in self.watered_this_day:
                        tasks["water_needed"].append((x, y))
                elif kind in ("COOP", "PASTURE"):
                    if tile.get("yield_units", 0) > 0:
                        tasks["harvest_ready"].append((x, y))
                    if tile.get("animal") and not tile.get("fed_today") and (x, y) not in self.fed_this_day:
                        tasks["feed_needed"].append((x, y))
        return tasks

    def _decide_tile_action(self, tile, shed, seeds, day, worker_inventory=None, pos=None):
        if self._is_empty_unlocked(tile):
            return self._plant_action(seeds, day)

        if isinstance(tile, dict) and tile.get("kind") == "WEED":
            return ["DIG"]

        x, y = pos if pos else (-1, -1)

        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            crop = tile.get("crop")
            crop_info = CROPS.get(crop, {})
            first_day = crop_info.get("first", 2)
            max_day = crop_info.get("max", first_day)
            age = day - tile.get("planted_day", day)
            watered = bool(tile.get("watered_today")) or (pos and (x, y) in self.watered_this_day)
            fert_until = tile.get("fertilized_until_day", -1)
            can_fert = (crop in ("MELON", "STRAWBERRY") and fert_until < day and shed.get("FERTILIZER", 0) > 0)
            is_ongoing = crop in ("TOMATO", "STRAWBERRY")

            if age >= max_day: return ["HARVEST"]
            if age >= first_day:
                if is_ongoing: return ["HARVEST"]
                if not watered: return ["WATER"]
                if can_fert: return ["FERTILIZE"]
                if max_day - age <= 1: return ["HARVEST"]
                return ["PASS"]

            if not watered: return ["WATER"]
            if can_fert: return ["FERTILIZE"]
            return ["PASS"]

        if self._is_animal_struct(tile):
            if tile.get("animal") is None:
                if worker_inventory:
                    for item, qty in worker_inventory.items():
                        if qty > 0 and item in ANIMALS and ANIMALS[item]["needs"] == tile.get("kind"):
                            return ["PLACE", item]
                return ["PASS"]

            fed = bool(tile.get("fed_today")) or (pos and (x, y) in self.fed_this_day)
            if not fed and shed.get("WHEAT", 0) > 0: return ["FEED"]
            if tile.get("fertilizer_available"): return ["COLLECT_FERTILIZER"]
            if not tile.get("cared_today"): return ["CARE"]
            if tile.get("yield_units", 0) > 0: return ["HARVEST"]
            return ["PASS"]

        return ["PASS"]

    def _build_move_priorities(self, shed, day, worker_inventory):
        return [
            lambda tile, x, y: isinstance(tile, dict) and tile.get("kind") == "PLANT" and (x, y) not in self.watered_this_day and not tile.get("watered_today"),
            lambda tile, x, y: isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE") and (x, y) not in self.fed_this_day and tile.get("animal") and not tile.get("fed_today") and shed.get("WHEAT", 0) > 0,
            lambda tile, x, y: (isinstance(tile, dict) and tile.get("kind") == "PLANT" and (day - tile.get("planted_day", day)) >= CROPS.get(tile.get("crop"), {}).get("max", 2)) or (isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE", "PLANT") and tile.get("yield_units", 0) > 0),
            lambda tile, x, y: isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") in ("MELON", "STRAWBERRY") and tile.get("fertilized_until_day", -1) < day and shed.get("FERTILIZER", 0) > 0,
            lambda tile, x, y: isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE") and tile.get("fertilizer_available"),
            lambda tile, x, y: isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE") and tile.get("animal") and not tile.get("cared_today"),
            lambda tile, x, y: isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE") and tile.get("animal") is None and worker_inventory and any(qty > 0 and item in ANIMALS and ANIMALS[item]["needs"] == tile.get("kind") for item, qty in worker_inventory.items()),
            lambda tile, x, y: isinstance(tile, dict) and tile.get("kind") == "WEED",
            lambda tile, x, y: tile is None
        ]

    def _get_build_priority(self, day, shed, farm):
        goose_count = sum(1 for row in farm.get("tiles", []) for tile in row if isinstance(tile, dict) and tile.get("animal") == "GOOSE")
        cow_count = sum(1 for row in farm.get("tiles", []) for tile in row if isinstance(tile, dict) and tile.get("animal") == "COW")
        empty_coops = sum(1 for row in farm.get("tiles", []) for tile in row if isinstance(tile, dict) and tile.get("kind") == "COOP" and not tile.get("animal"))
        
        if goose_count == 0 and empty_coops == 0 and day < 5: return "BUILD_COOP"
        if goose_count < 2 and empty_coops == 0 and self.animals_bought > goose_count and day < 10: return "BUILD_COOP"
        if cow_count == 0 and goose_count >= 2 and day >= 8 and shed.get("WHEAT", 0) > 15 and sum(1 for row in farm.get("tiles", []) for tile in row if isinstance(tile, dict) and tile.get("kind") == "PASTURE" and not tile.get("animal")) == 0:
            return "BUILD_PASTURE"
        return None

    # TÁTICA 1 & 3: Horizonte de Eventos e Espionagem embutidas no Mercado
    def _build_market_orders(self, obs, tasks):
        player = obs.get("player", 0)
        farm = obs.get("farms", [{}])[player]
        op_farm = obs.get("farms", [{}, {}])[1 - player]
        private = obs.get("private", {})
        day, hour, step = obs.get("day", 0), obs.get("hour", 0), obs.get("step", 0)
        shed = private.get("shed", {}) or {}
        seeds = private.get("seeds", {}) or {}
        money = farm.get("money", 0)
        prices = obs.get("market", {}).get("prices", {}) or {}

        self._track_prices(step, prices)
        if day >= 27: return self._build_liquidation_orders(shed)

        orders = []
        total_shed = sum(shed.values())

        # TÁTICA 3: FLUSH PREVENTIVO
        # Se for de noite (>=22) e os peões estiverem lotados, força liquidação massiva!
        total_invs = sum(sum(inv.values()) for inv in private.get("inventories", []) if inv)
        projected_shed = total_shed + total_invs
        panic_flush = (hour >= 22 and projected_shed >= 95)
        force_sell = panic_flush or (total_shed > SHED_SOFT_CAP)

        animal_count = sum(1 for row in farm.get("tiles", []) for tile in row if isinstance(tile, dict) and tile.get("animal"))
        
        # TÁTICA 2: ESPIONAGEM INDUSTRIAL (Scout Oponente)
        op_melons = sum(1 for row in op_farm.get("tiles", []) for tile in row if isinstance(tile, dict) and tile.get("crop") == "MELON")
        op_flooding_melon = op_melons > 8

        # Ordens de Venda
        for item, qty in sorted(shed.items()):
            if qty <= 0 or item in ("GOOSE", "COW", "SHEEP"): continue
            
            # Se oponente vai quebrar o preço do Melão, vendemos TUDO que temos dele agora!
            if item == "MELON" and op_flooding_melon:
                orders.append(["SELL", item, qty])
                continue

            if item == "WHEAT":
                keep = 2 if panic_flush else (5 if force_sell else max(5, animal_count * 3 + 5))
            elif item == "FERTILIZER":
                keep = 0 if panic_flush else (5 if force_sell else qty)
            else:
                keep = 0 if force_sell else 3
            
            sell_qty = qty - keep
            if sell_qty > 0: orders.append(["SELL", item, sell_qty])

        # HIRE e Expansão
        urgent = len(tasks.get("water_needed", [])) + len(tasks.get("feed_needed", [])) + len(tasks.get("harvest_ready", []))
        if urgent > 12 and money > 500 and len(farm.get("hands", [])) == 0: orders.append(["HIRE"])
        if len(farm.get("unlocked_quadrants", [])) < 4 and money > (1500 * len(farm.get("unlocked_quadrants", []))):
            orders.append(["BUY_LAND"])

        # TÁTICA 1: HORIZONTE DE EVENTOS (Corte de Sementes)
        valid_crops = self._get_valid_crops(day, op_flooding_melon)

        # Compras de sementes (apenas as que tem tempo de crescer)
        seed_targets = {"MELON": 4, "WHEAT": 6, "CARROT": 4, "TOMATO": 2, "STRAWBERRY": 2}
        for crop in PLANT_PRIORITY:
            if crop not in valid_crops: continue
            have = seeds.get(crop, 0)
            if have < seed_targets[crop] and len(orders) < MAX_MARKET_ORDERS:
                need = seed_targets[crop] - have
                if money >= (CROPS[crop]["seed_cost"] * need) + 200:
                    orders.append(["BUY_SEED", crop, need])
                    money -= CROPS[crop]["seed_cost"] * need

        return orders[:MAX_MARKET_ORDERS]

    def _build_liquidation_orders(self, shed):
        return [["SELL", item, qty] for item, qty in sorted(shed.items()) if qty > 0 and item not in ("GOOSE", "COW", "SHEEP")][:MAX_MARKET_ORDERS]

    def _track_prices(self, step, prices):
        for product, price in prices.items():
            if product not in self.price_history: self.price_history[product] = []
            self.price_history[product].append((step, price))
            if len(self.price_history[product]) > 10: self.price_history[product] = self.price_history[product][-10:]

    @staticmethod
    def _get_valid_crops(day, op_flooding_melon=False):
        crops = []
        if day <= 19 and not op_flooding_melon: crops.append("MELON")
        if day <= 18: crops.append("STRAWBERRY")
        if day <= 21: crops.append("TOMATO")
        if day <= 25: crops.append("WHEAT")
        if day <= 26: crops.append("CARROT")
        return crops

    # TÁTICA 1: Horizonte de Eventos aplicado no Plantio Físico
    def _plant_action(self, seeds, day):
        valid_crops = self._get_valid_crops(day)

        if day % 3 == 0 and seeds.get("MELON", 0) > 0 and "MELON" in valid_crops: return ["PLANT", "MELON"]
        if day % 2 == 0 and seeds.get("WHEAT", 0) > 0 and "WHEAT" in valid_crops: return ["PLANT", "WHEAT"]
        
        for crop in PLANT_PRIORITY:
            if seeds.get(crop, 0) > 0 and crop in valid_crops:
                return ["PLANT", crop]
        return ["PASS"]

    def __call__(self, obs):
        if not isinstance(obs, dict): return {"farmer": ["PASS"], "hands": [], "market": []}
        player = obs.get("player", 0)
        farms = obs.get("farms", [])
        if not isinstance(farms, list) or player >= len(farms): return {"farmer": ["PASS"], "hands": [], "market": []}

        farm, private, day = farms[player] or {}, obs.get("private", {}) or {}, obs.get("day", 0)
        shed, seeds, inventories = private.get("shed", {}) or {}, private.get("seeds", {}) or {}, private.get("inventories", [])

        if day != self.last_day:
            self.last_day, self.watered_this_day, self.fed_this_day = day, set(), set()

        tasks = self._scan_tiles(farm, day)
        market_orders = self._build_market_orders(obs, tasks)
        assigned = set()

        def get_worker_action(wpos, winv):
            x, y = wpos
            tile = self._tile_at(farm, (x, y))

            if self._is_empty_unlocked(tile):
                build_cmd = self._get_build_priority(day, shed, farm)
                if build_cmd: return [build_cmd]
                action = self._decide_tile_action(tile, shed, seeds, day, winv, wpos)
                if action and action[0] != "PASS": return action

            if not self._is_empty_unlocked(tile):
                if self._is_animal_struct(tile) and tile.get("animal") is None and winv:
                    for item, qty in winv.items():
                        if qty > 0 and item in ANIMALS and ANIMALS[item]["needs"] == tile.get("kind"):
                            return ["PLACE", item]
                action = self._decide_tile_action(tile, shed, seeds, day, winv, wpos)
                if action and action[0] != "PASS":
                    if action[0] == "WATER": self.watered_this_day.add((x, y))
                    elif action[0] == "FEED": self.fed_this_day.add((x, y))
                    return action

            if self._is_shed_adjacent((x, y)):
                for atype in ("GOOSE", "COW", "SHEEP"):
                    if shed.get(atype, 0) > 0 and (not winv or sum(winv.values()) == 0):
                        self.animals_bought += 1
                        return ["PICKUP", atype, 1]
                if winv and sum(winv.values()) > 5: return ["DROP"]

            for condition in self._build_move_priorities(shed, day, winv):
                tx, ty, direction = self._bfs_nearest((x, y), condition, farm, assigned)
                if direction:
                    assigned.add((tx, ty))
                    return [direction]

            return ["PASS"]

        farmer_inv = inventories[0] if inventories else {}
        farmer_action = get_worker_action(farm.get("farmer", [0, 0]), farmer_inv)

        hands_actions = []
        for i, hpos in enumerate(farm.get("hands", [])):
            h_inv = inventories[i + 1] if i + 1 < len(inventories) else {}
            hands_actions.append(get_worker_action(hpos, h_inv))

        return {"farmer": farmer_action, "hands": hands_actions, "market": market_orders}


agent = KaggricultureAgentV9()
def agent_fn(observation, configuration=None): return agent(observation)
def main_agent(observation, configuration=None): return agent(observation)