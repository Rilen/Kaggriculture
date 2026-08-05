"""
Kaggriculture Autonomous AI Agent — Version 8 (v8)

Navegacao BFS + investimento animal + expansao territorial
+ contratacao de mao de obra + arbitragem municipal
+ timing de mercado + liquidacao final.

Schema oficial de observacao da Kaggriculture.
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


class KaggricultureAgentV8:
    def __init__(self):
        self.last_day = -1
        self.watered_this_day = set()
        self.fed_this_day = set()
        self.price_history = {}
        self.coops_built = 0
        self.pastures_built = 0
        self.animals_bought = 0
        self._tile_cache = None
        self._cache_day = -1

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
    def _is_locked(tile):
        return tile == "LOCKED"

    @staticmethod
    def _is_plant(tile):
        return isinstance(tile, dict) and tile.get("kind") == "PLANT"

    @staticmethod
    def _is_weed(tile):
        return isinstance(tile, dict) and tile.get("kind") == "WEED"

    @staticmethod
    def _is_animal_struct(tile):
        return isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE")

    @staticmethod
    def _is_shed_adjacent(pos, board_size=10):
        half = board_size // 2
        x, y = pos
        return x in (half - 1, half) and y in (half - 1, half)

    @staticmethod
    def _move_toward(current, target):
        cx, cy = current
        tx, ty = target
        dx = tx - cx
        dy = ty - cy
        if abs(dx) >= abs(dy):
            return "EAST" if dx > 0 else "WEST"
        else:
            return "SOUTH" if dy > 0 else "NORTH"

    def _bfs_nearest(self, start, condition, farm, exclude):
        sx, sy = start
        board_h = len(farm.get("tiles", []))
        board_w = len(farm["tiles"][0]) if board_h > 0 else 0
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
                if tile not in (None, "LOCKED") and condition(tile, x, y) and (x, y) not in exclude:
                    return (x, y, first_dir)

            for dx, dy, dname in [(0, -1, "NORTH"), (0, 1, "SOUTH"), (-1, 0, "WEST"), (1, 0, "EAST")]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited and 0 <= nx < board_w and 0 <= ny < board_h:
                    visited.add((nx, ny))
                    ndir = first_dir if first_dir else dname
                    queue.append((nx, ny, ndir))

        return (None, None, None)

    def _scan_tiles(self, farm, shed, seeds, day):
        tiles = farm.get("tiles", [])
        board_h = len(tiles)
        board_w = len(tiles[0]) if board_h > 0 else 0
        unlocked = set(farm.get("unlocked_quadrants", []))

        tasks = {
            "harvest_ready": [],
            "feed_needed": [],
            "water_needed": [],
            "fertilize_me": [],
            "weed_tiles": [],
            "plantable": [],
            "collect_fert": [],
            "care_wanted": [],
            "build_spots": [],
            "place_needed": [],
        }

        for y in range(board_h):
            for x in range(board_w):
                tile = tiles[y][x]
                if tile is None:
                    tasks["plantable"].append((x, y))
                    tasks["build_spots"].append((x, y))
                    continue
                if tile == "LOCKED":
                    continue
                if not isinstance(tile, dict):
                    continue

                kind = tile.get("kind")

                if kind == "WEED":
                    tasks["weed_tiles"].append((x, y))
                    continue

                if kind == "PLANT":
                    crop = tile.get("crop")
                    crop_info = CROPS.get(crop, {})
                    first_day = crop_info.get("first", 2)
                    max_day = crop_info.get("max", first_day)
                    age = day - tile.get("planted_day", day)
                    is_ongoing = crop in ("TOMATO", "STRAWBERRY")

                    if age >= max_day or (is_ongoing and age >= first_day and tile.get("yield_units", 0) > 0):
                        tasks["harvest_ready"].append((x, y))

                    if not tile.get("watered_today") and (x, y) not in self.watered_this_day:
                        tasks["water_needed"].append((x, y))

                    fert_until = tile.get("fertilized_until_day", -1)
                    if crop in ("MELON", "STRAWBERRY") and fert_until < day and shed.get("FERTILIZER", 0) > 0:
                        tasks["fertilize_me"].append((x, y))

                    continue

                if kind in ("COOP", "PASTURE"):
                    animal = tile.get("animal")

                    if animal is None:
                        tasks["place_needed"].append((x, y))
                        continue

                    if tile.get("yield_units", 0) > 0:
                        tasks["harvest_ready"].append((x, y))

                    if not tile.get("fed_today") and (x, y) not in self.fed_this_day:
                        tasks["feed_needed"].append((x, y))

                    if tile.get("fertilizer_available"):
                        tasks["collect_fert"].append((x, y))

                    if not tile.get("cared_today"):
                        tasks["care_wanted"].append((x, y))

                    continue

        return tasks

    def _decide_tile_action(self, tile, shed, seeds, day, worker_inventory=None, pos=None):
        if self._is_empty_unlocked(tile):
            return self._plant_action(seeds, day)

        if self._is_weed(tile):
            return ["DIG"]

        x, y = pos if pos else (-1, -1)

        if self._is_plant(tile):
            crop = tile.get("crop")
            crop_info = CROPS.get(crop, {})
            first_day = crop_info.get("first", 2)
            max_day = crop_info.get("max", first_day)
            age = day - tile.get("planted_day", day)
            watered = bool(tile.get("watered_today")) or (pos and (x, y) in self.watered_this_day)
            fert_until = tile.get("fertilized_until_day", -1)
            can_fert = (crop in ("MELON", "STRAWBERRY")
                        and fert_until < day and shed.get("FERTILIZER", 0) > 0)
            is_ongoing = crop in ("TOMATO", "STRAWBERRY")

            if age >= max_day:
                return ["HARVEST"]

            if age >= first_day:
                if is_ongoing:
                    return ["HARVEST"]
                if not watered:
                    return ["WATER"]
                if can_fert:
                    return ["FERTILIZE"]
                if max_day - age <= 1:
                    return ["HARVEST"]
                return ["PASS"]

            if not watered:
                return ["WATER"]
            if can_fert:
                return ["FERTILIZE"]
            return ["PASS"]

        if self._is_animal_struct(tile):
            if tile.get("animal") is None:
                if worker_inventory:
                    for item, qty in worker_inventory.items():
                        if qty > 0 and item in ANIMALS:
                            needed = ANIMALS[item]["needs"]
                            if needed == tile.get("kind"):
                                return ["PLACE", item]
                return ["PASS"]

            fed = bool(tile.get("fed_today")) or (pos and (x, y) in self.fed_this_day)
            if not fed and shed.get("WHEAT", 0) > 0:
                return ["FEED"]
            if tile.get("fertilizer_available"):
                return ["COLLECT_FERTILIZER"]
            if not tile.get("cared_today"):
                return ["CARE"]
            if tile.get("yield_units", 0) > 0:
                return ["HARVEST"]
            return ["PASS"]

        return ["PASS"]

    def _build_move_priorities(self, shed, day, animal_in_shed, worker_inventory, farm):
        priorities = []

        def make_harvest_cond():
            def cond(tile, x, y):
                if isinstance(tile, dict):
                    k = tile.get("kind")
                    if k == "PLANT":
                        crop = tile.get("crop")
                        info = CROPS.get(crop, {})
                        first_d = info.get("first", 2)
                        max_d = info.get("max", first_d)
                        age = day - tile.get("planted_day", day)
                        if age >= max_d:
                            return True
                        if crop in ("TOMATO", "STRAWBERRY") and age >= first_d and tile.get("yield_units", 0) > 0:
                            return True
                    if k in ("COOP", "PASTURE") and tile.get("yield_units", 0) > 0:
                        return True
                return False
            return cond

        def make_water_cond():
            def cond(tile, x, y):
                if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                    if (x, y) in self.watered_this_day:
                        return False
                    return not tile.get("watered_today")
                return False
            return cond

        def make_feed_cond():
            def cond(tile, x, y):
                if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE"):
                    if (x, y) in self.fed_this_day:
                        return False
                    return tile.get("animal") and not tile.get("fed_today") and shed.get("WHEAT", 0) > 0
                return False
            return cond

        def make_fert_cond():
            def cond(tile, x, y):
                if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                    c = tile.get("crop")
                    fu = tile.get("fertilized_until_day", -1)
                    return c in ("MELON", "STRAWBERRY") and fu < day and shed.get("FERTILIZER", 0) > 0
                return False
            return cond

        def make_collect_fert_cond():
            def cond(tile, x, y):
                if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE"):
                    return tile.get("fertilizer_available")
                return False
            return cond

        def make_care_cond():
            def cond(tile, x, y):
                if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE"):
                    return tile.get("animal") and not tile.get("cared_today")
                return False
            return cond

        def make_weed_cond():
            def cond(tile, x, y):
                return isinstance(tile, dict) and tile.get("kind") == "WEED"
            return cond

        def make_plantable_cond():
            def cond(tile, x, y):
                return tile is None
            return cond

        def make_place_cond():
            def cond(tile, x, y):
                if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE"):
                    if tile.get("animal") is None and worker_inventory:
                        for item, qty in worker_inventory.items():
                            if qty > 0 and item in ANIMALS:
                                if ANIMALS[item]["needs"] == tile.get("kind"):
                                    return True
                return False
            return cond

        priorities.append(make_water_cond())
        priorities.append(make_feed_cond())
        priorities.append(make_harvest_cond())
        priorities.append(make_fert_cond())
        priorities.append(make_collect_fert_cond())
        priorities.append(make_care_cond())
        priorities.append(make_place_cond())
        priorities.append(make_weed_cond())
        priorities.append(make_plantable_cond())

        return priorities

    def _get_build_priority(self, day, shed, animal_in_shed, farm):
        goose_count = self._count_animals_of_type(farm, "GOOSE")
        cow_count = self._count_animals_of_type(farm, "COW")
        sheep_count = self._count_animals_of_type(farm, "SHEEP")
        empty_coops = self._count_empty_structures(farm, "COOP")

        if goose_count == 0 and empty_coops == 0 and day < 5:
            return "BUILD_COOP"
        if goose_count < 2 and empty_coops == 0 and self.animals_bought > goose_count and day < 10:
            return "BUILD_COOP"
        if cow_count == 0 and goose_count >= 2 and day >= 8 and shed.get("WHEAT", 0) > 15:
            empty_pastures = self._count_empty_structures(farm, "PASTURE")
            if empty_pastures == 0:
                return "BUILD_PASTURE"
        return None

    def _count_animals_of_type(self, farm, animal_type):
        count = 0
        tiles = farm.get("tiles", [])
        for row in tiles:
            for tile in row:
                if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE"):
                    if tile.get("animal") == animal_type:
                        count += 1
        return count

    def _build_market_orders(self, obs, tasks=None):
        player = obs.get("player", 0)
        farm = obs.get("farms", [{}])[player] if isinstance(obs.get("farms"), list) and player < len(obs["farms"]) else {}
        private = obs.get("private", {})
        day = obs.get("day", 0)
        step = obs.get("step", 0)
        shed = private.get("shed", {}) or {}
        seeds = private.get("seeds", {}) or {}
        money = farm.get("money", 0)
        prices = obs.get("market", {}).get("prices", {}) or {}
        town_shops = obs.get("town", {}).get("unlocked_shops", [])
        hires_today = farm.get("hires_today", 0)

        self._track_prices(step, prices)

        if day >= 27:
            return self._build_liquidation_orders(shed)

        orders = []

        total_shed = sum(shed.values()) if isinstance(shed, dict) else 0
        force_sell = total_shed > SHED_SOFT_CAP
        animal_count = self._count_animals_on_farm(farm)
        orders.extend(self._sell_orders(shed, force_sell, prices, day, animal_count))

        if self._should_hire(farm, obs, tasks):
            orders.append(["HIRE"])

        if self._should_buy_land(farm, money, tasks):
            orders.append(["BUY_LAND"])

        animal_orders = self._animal_buy_orders(farm, shed, money, day)
        orders.extend(animal_orders)

        wheat_reserve = max(5, self._count_animals_on_farm(farm) * 3)
        if shed.get("WHEAT", 0) < wheat_reserve and money > 100:
            need = wheat_reserve - shed.get("WHEAT", 0)
            if len(orders) < MAX_MARKET_ORDERS:
                wheat_price = prices.get("WHEAT", 25)
                if wheat_price < 35:
                    orders.append(["BUY_PRODUCT", "WHEAT", min(need, 10)])

        town_bonus = self._compute_town_demand_bonus(town_shops)

        if len(orders) < MAX_MARKET_ORDERS and money > 200:
            orders.extend(self._seed_orders(seeds, money, len(orders), town_bonus))

        return orders[:MAX_MARKET_ORDERS]

    def _should_hire(self, farm, obs, tasks):
        urgent = (len(tasks.get("water_needed", [])) +
                  len(tasks.get("feed_needed", [])) +
                  len(tasks.get("harvest_ready", [])))
        hires_today = farm.get("hires_today", 0)
        hands = farm.get("hands", []) or []
        money = farm.get("money", 0)
        fib = [1, 1, 2, 3, 5, 8, 13]
        next_cost = fib[min(hires_today, len(fib) - 1)]

        if urgent > 12 and money > 500 and len(hands) == 0:
            return True
        if urgent > 20 and money > 500 + next_cost and len(hands) == 1 and hires_today < 3:
            return True
        return False

    def _should_buy_land(self, farm, money, tasks):
        unlocked = farm.get("unlocked_quadrants", ["NW"])
        quad_count = len(unlocked)
        if quad_count >= 4:
            return False
        tiles_in_use = 0
        tiles = farm.get("tiles", [])
        for row in tiles:
            for tile in row:
                if tile is not None and tile != "LOCKED":
                    tiles_in_use += 1

        if quad_count == 1 and money > 1500 and tiles_in_use >= 15:
            return True
        if quad_count == 2 and money > 3000 and tiles_in_use >= 35:
            return True
        if quad_count == 3 and money > 6000 and tiles_in_use >= 55:
            return True
        return False

    def _animal_buy_orders(self, farm, shed, money, day):
        orders = []
        goose_count = self._count_animals_of_type(farm, "GOOSE")
        cow_count = self._count_animals_of_type(farm, "COW")
        empty_coops = self._count_empty_structures(farm, "COOP")
        empty_pastures = self._count_empty_structures(farm, "PASTURE")
        goose_in_shed = shed.get("GOOSE", 0)
        cow_in_shed = shed.get("COW", 0)

        if day < 12 and goose_count < 3 and money > 400:
            total_geese = goose_count + goose_in_shed
            capacity = max(empty_coops, 1)
            want = min(3 - total_geese, capacity)
            if want > 0 and len(orders) < MAX_MARKET_ORDERS:
                orders.append(["BUY_ANIMAL", "GOOSE", want])
                money -= ANIMALS["GOOSE"]["buy_cost"] * want
                self.animals_bought += want

        if day >= 8 and cow_count == 0 and money > 600 and shed.get("WHEAT", 0) > 15:
            if empty_pastures > 0 and len(orders) < MAX_MARKET_ORDERS:
                orders.append(["BUY_ANIMAL", "COW", 1])
                self.animals_bought += 1

        return orders

    def _count_animals_on_farm(self, farm):
        count = 0
        tiles = farm.get("tiles", [])
        for row in tiles:
            for tile in row:
                if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE"):
                    if tile.get("animal") is not None:
                        count += 1
        return count

    def _count_empty_structures(self, farm, struct_kind):
        count = 0
        tiles = farm.get("tiles", [])
        for row in tiles:
            for tile in row:
                if isinstance(tile, dict) and tile.get("kind") == struct_kind and tile.get("animal") is None:
                    count += 1
        return count

    def _sell_orders(self, shed, force_sell, prices, day, animal_count=0):
        orders = []

        for item in sorted(shed.keys()):
            qty = shed.get(item, 0)
            if not isinstance(qty, (int, float)) or qty <= 0:
                continue

            if item == "WHEAT":
                keep = 5 if force_sell else max(5, animal_count * 3 + 5)
                sell_qty = qty - keep
                if sell_qty > 0:
                    orders.append(["SELL", item, sell_qty])
                continue

            if item in ("GOOSE", "COW", "SHEEP"):
                continue

            if item == "FERTILIZER":
                if force_sell and qty > 5:
                    orders.append(["SELL", item, qty - 5])
                continue

            item_price = prices.get(item, CROPS.get(item, {}).get("price", 0))
            if hasattr(self, 'price_history') and item in self.price_history:
                hist = self.price_history.get(item, [])
                if hist:
                    recent = [p for _, p in hist[-3:]]
                    avg_recent = sum(recent) / len(recent)
                    base_price = CROPS.get(item, {}).get("price", 0) or ANIMALS.get(item, {}).get("price", 0)
                    if base_price > PREMIUM_THRESHOLD and avg_recent < 0.6 * base_price:
                        keep = qty
                    else:
                        keep = 0 if force_sell else 3
                else:
                    keep = 0 if force_sell else 3
            else:
                keep = 0 if force_sell else 3

            sell_qty = qty - keep
            if sell_qty > 0:
                orders.append(["SELL", item, sell_qty])

        return orders

    def _seed_orders(self, seeds, money, current_len, town_bonus=None):
        orders = []
        seed_targets = {"MELON": 4, "WHEAT": 6, "CARROT": 4, "TOMATO": 2, "STRAWBERRY": 2}
        priority_order = ["MELON", "WHEAT", "CARROT", "TOMATO", "STRAWBERRY"]
        if town_bonus:
            priority_order = sorted(priority_order,
                                    key=lambda c: -(town_bonus.get(c, 0)))
        for crop in priority_order:
            have = seeds.get(crop, 0)
            target = seed_targets[crop]
            if have >= target or current_len + len(orders) >= MAX_MARKET_ORDERS:
                continue
            need = target - have
            cost = CROPS[crop]["seed_cost"] * need
            if money >= cost + 200:
                orders.append(["BUY_SEED", crop, need])
                money -= cost
                current_len += 1
        return orders

    def _build_liquidation_orders(self, shed):
        orders = []
        for item, qty in sorted(shed.items()):
            if isinstance(qty, (int, float)) and qty > 0:
                if item not in ("GOOSE", "COW", "SHEEP"):
                    orders.append(["SELL", item, qty])
        return orders[:MAX_MARKET_ORDERS]

    def _track_prices(self, step, prices):
        for product, price in prices.items():
            if product not in self.price_history:
                self.price_history[product] = []
            self.price_history[product].append((step, price))
            if len(self.price_history[product]) > 10:
                self.price_history[product] = self.price_history[product][-10:]

    def _compute_town_demand_bonus(self, unlocked_shops):
        demand_count = {}
        for shop in unlocked_shops:
            for product in SHOP_DEMAND.get(shop, []):
                demand_count[product] = demand_count.get(product, 0) + 1
        return demand_count

    def _plant_action(self, seeds, day):
        if day % 3 == 0 and seeds.get("MELON", 0) > 0:
            return ["PLANT", "MELON"]
        if day % 2 == 0 and seeds.get("WHEAT", 0) > 0:
            return ["PLANT", "WHEAT"]
        if seeds.get("CARROT", 0) > 0:
            return ["PLANT", "CARROT"]
        for crop in PLANT_PRIORITY:
            if seeds.get(crop, 0) > 0:
                return ["PLANT", crop]
        return ["PASS"]

    def __call__(self, obs):
        if not isinstance(obs, dict):
            return {"farmer": ["PASS"], "hands": [], "market": []}

        player = obs.get("player", 0)
        farms = obs.get("farms", [])
        if not isinstance(farms, list) or player >= len(farms):
            return {"farmer": ["PASS"], "hands": [], "market": []}

        farm = farms[player] or {}
        private = obs.get("private", {}) or {}
        day = obs.get("day", 0)
        shed = private.get("shed", {}) or {}
        seeds = private.get("seeds", {}) or {}
        inventories = private.get("inventories", [])

        if day != self.last_day:
            self.last_day = day
            self.watered_this_day.clear()
            self.fed_this_day.clear()

        tasks = self._scan_tiles(farm, shed, seeds, day)
        market_orders = self._build_market_orders(obs, tasks)

        assigned = set()
        animal_in_shed = {k: shed.get(k, 0) for k in ("GOOSE", "COW", "SHEEP")}

        def get_worker_action(wpos, winv):
            x, y = wpos
            tile = self._tile_at(farm, (x, y))

            if self._is_empty_unlocked(tile):
                build_cmd = self._get_build_priority(day, shed, animal_in_shed, farm)
                if build_cmd:
                    return [build_cmd]
                return self._decide_tile_action(tile, shed, seeds, day, winv, wpos)

            if self._is_animal_struct(tile) and tile.get("animal") is None and winv:
                for item, qty in winv.items():
                    if qty > 0 and item in ANIMALS:
                        if ANIMALS[item]["needs"] == tile.get("kind"):
                            return ["PLACE", item]

            action = self._decide_tile_action(tile, shed, seeds, day, winv, wpos)
            act_type = action[0] if action else "PASS"

            if act_type != "PASS":
                if act_type == "WATER":
                    self.watered_this_day.add((x, y))
                elif act_type == "FEED":
                    self.fed_this_day.add((x, y))
                return action

            if self._is_shed_adjacent((x, y)):
                for atype in ("GOOSE", "COW", "SHEEP"):
                    if animal_in_shed.get(atype, 0) > 0:
                        if not winv or sum(winv.values()) == 0:
                            return ["PICKUP", atype, 1]
                total_inv = sum(winv.values()) if winv else 0
                if total_inv > 5:
                    return ["DROP"]

            priority_conditions = self._build_move_priorities(shed, day, animal_in_shed, winv, farm)
            for condition in priority_conditions:
                tx, ty, direction = self._bfs_nearest((x, y), condition, farm, assigned)
                if direction:
                    assigned.add((tx, ty))
                    return [direction]

            return ["PASS"]

        farmer_pos = farm.get("farmer", [0, 0])
        farmer_inv = inventories[0] if isinstance(inventories, list) and len(inventories) > 0 else {}
        farmer_action = get_worker_action(farmer_pos, farmer_inv)

        hands_pos = farm.get("hands", []) or []
        hands_actions = []
        for i, hpos in enumerate(hands_pos):
            h_inv = inventories[i + 1] if isinstance(inventories, list) and i + 1 < len(inventories) else {}
            hands_actions.append(get_worker_action(hpos, h_inv))

        return {
            "farmer": farmer_action,
            "hands": hands_actions,
            "market": market_orders,
        }


agent = KaggricultureAgentV8()


def agent_fn(observation, configuration=None):
    return agent(observation)


def main_agent(observation, configuration=None):
    return agent(observation)
