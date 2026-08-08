"""
Kaggriculture Autonomous AI Agent ??? Version 15 (v15)

Meta: Fixed Asset Engine (Kaileh57 Top-1 clone, 128k-148k pts)

Opening (Dia 0, Hora 1):
  5x HIRE + 2 SHEEP + 2 COW + WHEAT 7 + MELON 12
  Sem BUY_LAND. Capital cai para ~$158.

Fluxo:
  Dia 0   : BUILD_PASTURE + PLACE + plant MELON/WHEAT (cash early) + FEED
  Dia 1   : Broke -> 0 hands, so farmer FEED/CARE/COLLECT + BUY_PRODUCT WHEAT
  Dia 3-11: Escala para 8 COW + 6 SHEEP, BUY_LAND nos dias 7 e 11
  Mid/Late: Venda continua MILK/WOOL, rehire adaptativo, zero crops finais
"""

from collections import deque

# =============================================================================
# CONSTANTES
# =============================================================================
CROPS = {
    "WHEAT":      {"first": 2,  "max": 4,  "seed_cost": 10,  "price": 25},
    "CARROT":     {"first": 2,  "max": 3,  "seed_cost": 20,  "price": 35},
    "TOMATO":     {"first": 8,  "max": 11, "seed_cost": 50,  "price": 60},
    "STRAWBERRY": {"first": 10, "max": 16, "seed_cost": 100, "price": 120},
    "MELON":      {"first": 10, "max": 10, "seed_cost": 80,  "price": 250},
}

ANIMALS = {
    "GOOSE": {"buy_cost": 300, "needs": "COOP",    "product": "EGG",  "price": 50},
    "COW":   {"buy_cost": 400, "needs": "PASTURE", "product": "MILK", "price": 160},
    "SHEEP": {"buy_cost": 500, "needs": "PASTURE", "product": "WOOL", "price": 200},
}

MAX_MARKET_ORDERS = 10
SHED_SOFT_CAP = 75
LAND_COST = {1: 1000, 2: 2000, 3: 4000}

TARGET_COW = 8
TARGET_SHEEP = 6
TARGET_PASTURES = 14


# =============================================================================
# OPENING BOOK ??? Dia 0 (replica exata do Top 1)
# =============================================================================
class OpeningBook:
    """
    Opening deterministico v15 (Kaileh57):
      Hour 1    : market dump (5 HIRE + animals + seeds)
      Hour 2-5  : PICKUP + BUILD_PASTURE + PLACE
      Hour 6-23 : FEED / CARE / PLANT MELON+WHEAT / WATER
    """

    def __init__(self):
        self.done = False

    def is_active(self, day):
        return day == 0 and not self.done

    @staticmethod
    def _tile_at(tiles, x, y):
        if not (0 <= y < len(tiles)):
            return None
        row = tiles[y]
        if not isinstance(row, list) or not (0 <= x < len(row)):
            return None
        return row[x]

    @staticmethod
    def _navigate(pos, target):
        x, y = pos
        tx, ty = target
        if ty < y:
            return ["NORTH"]
        if ty > y:
            return ["SOUTH"]
        if tx < x:
            return ["WEST"]
        if tx > x:
            return ["EAST"]
        return ["PASS"]

    def _find_empty(self, tiles):
        h = len(tiles)
        w = len(tiles[0]) if h else 0
        half = h // 2
        for y_range in (range(half), range(h)):
            for y in y_range:
                row = tiles[y] if y < h else []
                for x in range(w):
                    if x < len(row) and row[x] is None:
                        return (x, y)
        return None

    def _find_empty_pasture(self, tiles):
        for y, row in enumerate(tiles):
            for x, t in enumerate(row if isinstance(row, list) else []):
                if isinstance(t, dict) and t.get("kind") == "PASTURE" and not t.get("animal"):
                    return (x, y)
        return None

    @staticmethod
    def _is_shed_adj(pos, board=10):
        half = board // 2
        x, y = pos
        return x in (half - 1, half) and y in (half - 1, half)

    def _worker(self, hour, pos, inv, tiles, shed, seeds, idx):
        x, y = pos
        tile = self._tile_at(tiles, x, y)
        inv = inv or {}
        shed = shed or {}
        seeds = seeds or {}

        # Hora 2-5: PICKUP + BUILD + PLACE
        if hour <= 5:
            if idx == -1 and inv.get("COW", 0) == 0 and shed.get("COW", 0) > 0:
                return ["PICKUP", "COW", 2]
            if idx == 0 and inv.get("SHEEP", 0) == 0 and shed.get("SHEEP", 0) > 0:
                return ["PICKUP", "SHEEP", 2]
            carrying = [a for a in ("COW", "SHEEP") if inv.get(a, 0) > 0]
            if carrying:
                if isinstance(tile, dict) and tile.get("kind") == "PASTURE" and not tile.get("animal"):
                    return ["PLACE", carrying[0]]
                target = self._find_empty_pasture(tiles)
                if target and target != (x, y):
                    return self._navigate(pos, target)
                if tile is None:
                    return ["BUILD_PASTURE"]
                empty = self._find_empty(tiles)
                if empty and empty != (x, y):
                    return self._navigate(pos, empty)
                return ["PASS"]
            if tile is None:
                return ["BUILD_PASTURE"]
            empty = self._find_empty(tiles)
            if empty and empty != (x, y):
                return self._navigate(pos, empty)
            return ["PASS"]

        # Hora 6+: FEED / CARE / PLANT / WATER
        if isinstance(tile, dict) and tile.get("kind") == "PASTURE" and tile.get("animal"):
            if not tile.get("fed_today") and (shed.get("WHEAT", 0) > 0 or inv.get("WHEAT", 0) > 0):
                return ["FEED"]
            if not tile.get("cared_today"):
                return ["CARE"]
            if tile.get("yield_units", 0) > 0:
                return ["HARVEST"]
            if tile.get("fertilizer_available"):
                return ["COLLECT_FERTILIZER"]

        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            if not tile.get("watered_today"):
                return ["WATER"]
            if tile.get("yield_units", 0) > 0:
                return ["HARVEST"]

        if tile is None and hour <= 20:
            for crop in ("MELON", "WHEAT"):
                if seeds.get(crop, 0) > 0:
                    return ["PLANT", crop]

        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row if isinstance(row, list) else []):
                if not (isinstance(t, dict) and t.get("kind") == "PASTURE" and t.get("animal")):
                    continue
                needs = ((not t.get("fed_today") and shed.get("WHEAT", 0) > 0)
                         or not t.get("cared_today"))
                if needs and (rx, ry) != (x, y):
                    return self._navigate(pos, (rx, ry))

        if hour <= 20 and any(seeds.get(c, 0) > 0 for c in ("MELON", "WHEAT")):
            empty = self._find_empty(tiles)
            if empty and empty != (x, y):
                return self._navigate(pos, empty)

        if self._is_shed_adj(pos) and shed.get("WHEAT", 0) > 0 and inv.get("WHEAT", 0) == 0:
            return ["PICKUP", "WHEAT", min(3, shed.get("WHEAT", 0))]

        return ["PASS"]

    def execute(self, obs):
        hour = obs.get("hour", 0)
        if hour >= 24:
            self.done = True
            return None

        player = obs.get("player", 0)
        farms = obs.get("farms") or [{}]
        farm = (farms[player] if player < len(farms) else {}) or {}
        private = obs.get("private") or {}
        shed = private.get("shed") or {}
        seeds = private.get("seeds") or {}
        invs = private.get("inventories") or []
        tiles = farm.get("tiles") or []

        market = []
        if hour == 1:
            market = [
                ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"],
                ["BUY_ANIMAL", "SHEEP", 2],
                ["BUY_ANIMAL", "COW", 2],
                ["BUY_SEED", "WHEAT", 7],
                ["BUY_SEED", "MELON", 12],
            ]
        elif hour == 2:
            market = [["BUY_PRODUCT", "WHEAT", 2]]

        farmer_pos = farm.get("farmer") or [0, 0]
        farmer_inv = invs[0] if invs else {}
        farmer_act = self._worker(hour, farmer_pos, farmer_inv, tiles, shed, seeds, -1)

        hands_acts = []
        for i, hpos in enumerate(farm.get("hands") or []):
            h_inv = invs[i + 1] if i + 1 < len(invs) else {}
            hands_acts.append(self._worker(hour, hpos, h_inv, tiles, shed, seeds, i))

        return {"farmer": farmer_act, "hands": hands_acts, "market": market}


# =============================================================================
# ENGINE DINAMICO ??? Mid/Late (Fixed Asset Meta)
# =============================================================================
class KaggricultureAgentV15:
    def __init__(self):
        self.opening = OpeningBook()
        self.last_day = -1
        self.watered_this_day = set()
        self.fed_this_day = set()
        self.cared_this_day = set()

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
    def _is_shed_adj(pos, board=10):
        half = board // 2
        x, y = pos
        return x in (half - 1, half) and y in (half - 1, half)

    def _bfs(self, start, condition, farm, exclude):
        sx, sy = start
        tiles = farm.get("tiles", [])
        bh = len(tiles)
        bw = len(tiles[0]) if bh else 0
        if bh == 0:
            return None, None, None

        targets = []
        for y in range(bh):
            for x in range(bw):
                if (x, y) != (sx, sy) and (x, y) not in exclude:
                    tile = self._tile_at(farm, (x, y))
                    if tile != "LOCKED" and condition(tile, x, y):
                        targets.append((x, y))
        
        if not targets:
            return None, None, None

        fwd_queue = deque([(sx, sy)])
        fwd_visited = {(sx, sy): None}
        
        bwd_queue = deque(targets)
        bwd_visited = {t: t for t in targets}

        while fwd_queue and bwd_queue:
            if len(fwd_queue) <= len(bwd_queue):
                curr_x, curr_y = fwd_queue.popleft()
                curr_dir = fwd_visited[(curr_x, curr_y)]
                for dx, dy, dname in ((0, -1, "NORTH"), (0, 1, "SOUTH"), (-1, 0, "WEST"), (1, 0, "EAST")):
                    nx, ny = curr_x + dx, curr_y + dy
                    if 0 <= nx < bw and 0 <= ny < bh:
                        if (nx, ny) in bwd_visited:
                            target = bwd_visited[(nx, ny)]
                            return target[0], target[1], curr_dir if curr_dir else dname
                        if (nx, ny) not in fwd_visited:
                            fwd_visited[(nx, ny)] = curr_dir if curr_dir else dname
                            fwd_queue.append((nx, ny))
            else:
                curr_x, curr_y = bwd_queue.popleft()
                target = bwd_visited[(curr_x, curr_y)]
                for dx, dy, dname in ((0, -1, "NORTH"), (0, 1, "SOUTH"), (-1, 0, "WEST"), (1, 0, "EAST")):
                    nx, ny = curr_x + dx, curr_y + dy
                    if 0 <= nx < bw and 0 <= ny < bh:
                        if (nx, ny) in fwd_visited:
                            first_dir = fwd_visited[(nx, ny)]
                            if first_dir is None:
                                if curr_x > nx: first_dir = "EAST"
                                elif curr_x < nx: first_dir = "WEST"
                                elif curr_y > ny: first_dir = "SOUTH"
                                elif curr_y < ny: first_dir = "NORTH"
                            return target[0], target[1], first_dir
                        if (nx, ny) not in bwd_visited:
                            bwd_visited[(nx, ny)] = target
                            bwd_queue.append((nx, ny))

        return None, None, None

    def _count_animals(self, farm):
        cows = sheep = pastures = empty_past = 0
        for row in farm.get("tiles", []):
            for t in row if isinstance(row, list) else []:
                if isinstance(t, dict) and t.get("kind") == "PASTURE":
                    pastures += 1
                    if t.get("animal") == "COW":
                        cows += 1
                    elif t.get("animal") == "SHEEP":
                        sheep += 1
                    elif not t.get("animal"):
                        empty_past += 1
        return cows, sheep, pastures, empty_past

    def _scan(self, farm, day):
        tasks = {
            "feed": [], "care": [], "harvest": [], "water": [],
            "fert": [], "empty": 0, "weeds": [],
        }
        for y, row in enumerate(farm.get("tiles", [])):
            for x, t in enumerate(row if isinstance(row, list) else []):
                if t is None:
                    tasks["empty"] += 1
                    continue
                if not isinstance(t, dict):
                    continue
                k = t.get("kind")
                if k == "PASTURE" and t.get("animal"):
                    if not t.get("fed_today") and (x, y) not in self.fed_this_day:
                        tasks["feed"].append((x, y))
                    if not t.get("cared_today") and (x, y) not in self.cared_this_day:
                        tasks["care"].append((x, y))
                    if t.get("yield_units", 0) > 0:
                        tasks["harvest"].append((x, y))
                    if t.get("fertilizer_available"):
                        tasks["fert"].append((x, y))
                elif k == "PLANT":
                    if not t.get("watered_today") and (x, y) not in self.watered_this_day:
                        tasks["water"].append((x, y))
                    crop = t.get("crop", "")
                    info = CROPS.get(crop, {})
                    age = day - t.get("planted_day", day)
                    if age >= info.get("max", 2) or t.get("yield_units", 0) > 0:
                        tasks["harvest"].append((x, y))
                elif k == "WEED":
                    tasks["weeds"].append((x, y))
        return tasks

    def _market(self, obs, tasks, cows, sheep, pastures, empty_past):
        player = obs.get("player", 0)
        farm = obs.get("farms", [{}])[player]
        private = obs.get("private", {})
        day = obs.get("day", 0)
        hour = obs.get("hour", 0)
        shed = private.get("shed", {}) or {}
        seeds = private.get("seeds", {}) or {}
        money = farm.get("money", 0)
        n_quads = len(farm.get("unlocked_quadrants", []))
        current_hands = len(farm.get("hands") or [])
        hires_today = farm.get("hires_today", 0) or 0

        orders = []

        if day >= 28:
            for item, qty in sorted(shed.items()):
                if qty > 0 and item not in ("GOOSE", "COW", "SHEEP"):
                    orders.append(["SELL", item, qty])
            return orders[:MAX_MARKET_ORDERS]

        total_shed = sum(v for k, v in shed.items() if k not in ("GOOSE", "COW", "SHEEP"))
        force = total_shed > SHED_SOFT_CAP or hour >= 21

        for item in ("MILK", "WOOL", "MELON", "EGG", "FERTILIZER", "TOMATO",
                     "STRAWBERRY", "CARROT", "WHEAT"):
            qty = shed.get(item, 0)
            if qty <= 0:
                continue
            if item == "WHEAT":
                keep = max(5, (cows + sheep) * 3 + 5)
                if force:
                    keep = max(3, (cows + sheep) * 2)
                sell = qty - keep
            elif item == "FERTILIZER":
                keep = 0 if force else min(qty, 5)
                sell = qty - keep
            else:
                keep = 0 if force or item in ("MILK", "WOOL", "MELON") else 1
                sell = qty - keep
            if sell > 0:
                orders.append(["SELL", item, sell])

        # BUY_PRODUCT WHEAT (feed critico)
        wheat_need = (cows + sheep) * 2 + 4
        wheat_have = shed.get("WHEAT", 0)
        if wheat_have < wheat_need and money > 50 and len(orders) < MAX_MARKET_ORDERS:
            buy_n = min(wheat_need - wheat_have, 6)
            if money > buy_n * 30 + 20:
                orders.append(["BUY_PRODUCT", "WHEAT", buy_n])
                money -= buy_n * 30

        # HIRE adaptativo
        fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
        if day == 1:
            target_h = 0
        elif day <= 3:
            target_h = 4
        elif day <= 6:
            target_h = 5
        elif day <= 9:
            target_h = 8
        elif day <= 14:
            target_h = 11
        else:
            target_h = 8

        urgent = (len(tasks["feed"]) + len(tasks["care"])
                  + len(tasks["harvest"]) + len(tasks["water"]))
        if urgent > 15:
            target_h = min(target_h + 3, 14)

        needed = max(0, target_h - current_hands)
        cost_est = sum(fib[min(hires_today + i, len(fib) - 1)] for i in range(needed))
        reserve = 30 if day <= 3 else (100 if day <= 8 else 300)

        if needed > 0 and money > cost_est + reserve:
            for i in range(min(needed, MAX_MARKET_ORDERS - len(orders))):
                orders.append(["HIRE"])
                money -= fib[min(hires_today + i, len(fib) - 1)]

        # BUY_ANIMAL (escala ate targets)
        if day >= 3 and day <= 15 and money > 600 and len(orders) < MAX_MARKET_ORDERS:
            if cows < TARGET_COW and (empty_past > 0 or pastures < TARGET_PASTURES):
                n = min(2, TARGET_COW - cows, max(1, empty_past))
                if money > 400 * n + 200:
                    orders.append(["BUY_ANIMAL", "COW", n])
                    money -= 400 * n
            elif sheep < TARGET_SHEEP and (empty_past > 0 or pastures < TARGET_PASTURES):
                n = min(2, TARGET_SHEEP - sheep, max(1, empty_past))
                if money > 500 * n + 200:
                    orders.append(["BUY_ANIMAL", "SHEEP", n])
                    money -= 500 * n

        # BUY_LAND (Dia 7 e ~11)
        land_cost = LAND_COST.get(n_quads, 9999)
        if n_quads < 3 and day >= 7 and money > land_cost + 400:
            if n_quads == 1 and day >= 7:
                orders.append(["BUY_LAND"])
                money -= land_cost
            elif n_quads == 2 and day >= 11 and money > land_cost + 800:
                orders.append(["BUY_LAND"])
                money -= land_cost

        # Seeds: MELON early + WHEAT
        if day <= 12 and len(orders) < MAX_MARKET_ORDERS:
            melon_have = seeds.get("MELON", 0)
            if melon_have < 4 and money > 400 and day <= 10:
                need = 4 - melon_have
                orders.append(["BUY_SEED", "MELON", need])
                money -= 80 * need
            wheat_seeds = seeds.get("WHEAT", 0)
            if wheat_seeds < 3 and money > 100:
                orders.append(["BUY_SEED", "WHEAT", 3])

        return orders[:MAX_MARKET_ORDERS]

    def _decide(self, tile, shed, seeds, day, inv, pos, hour, cows, sheep, empty_past):
        inv = inv or {}
        x, y = pos if pos else (-1, -1)

        if tile is None:
            total_animals = cows + sheep
            if total_animals < TARGET_COW + TARGET_SHEEP or empty_past == 0:
                if day <= 15:
                    return ["BUILD_PASTURE"]
            if day <= 12 and hour <= 20:
                for crop in ("MELON", "WHEAT"):
                    if seeds.get(crop, 0) > 0:
                        return ["PLANT", crop]
            return ["PASS"]

        if isinstance(tile, dict) and tile.get("kind") == "WEED":
            return ["DIG"]

        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            crop = tile.get("crop", "")
            info = CROPS.get(crop, {})
            age = day - tile.get("planted_day", day)
            watered = tile.get("watered_today") or (pos and (x, y) in self.watered_this_day)
            if age >= info.get("max", 2) or tile.get("yield_units", 0) > 0:
                return ["HARVEST"]
            if not watered:
                return ["WATER"]
            return ["PASS"]

        if isinstance(tile, dict) and tile.get("kind") == "PASTURE":
            if tile.get("animal") is None:
                for a in ("COW", "SHEEP"):
                    if inv.get(a, 0) > 0:
                        return ["PLACE", a]
                return ["PASS"]
            fed = tile.get("fed_today") or (pos and (x, y) in self.fed_this_day)
            if not fed and (shed.get("WHEAT", 0) > 0 or inv.get("WHEAT", 0) > 0):
                return ["FEED"]
            if tile.get("fertilizer_available"):
                return ["COLLECT_FERTILIZER"]
            cared = tile.get("cared_today") or (pos and (x, y) in self.cared_this_day)
            if not cared:
                return ["CARE"]
            if tile.get("yield_units", 0) > 0:
                return ["HARVEST"]
            return ["PASS"]

        return ["PASS"]

    def _move_priorities(self, shed, day, inv):
        inv = inv or {}
        return [
            lambda t, x, y: (isinstance(t, dict) and t.get("kind") == "PASTURE"
                             and t.get("animal") and not t.get("fed_today")
                             and (x, y) not in self.fed_this_day
                             and (shed.get("WHEAT", 0) > 0 or inv.get("WHEAT", 0) > 0)),
            lambda t, x, y: (isinstance(t, dict)
                             and ((t.get("kind") == "PASTURE" and t.get("yield_units", 0) > 0)
                                  or (t.get("kind") == "PLANT" and (
                                      t.get("yield_units", 0) > 0
                                      or (day - t.get("planted_day", day))
                                         >= CROPS.get(str(t.get("crop") or ""), {}).get("max", 99))))),
            lambda t, x, y: (isinstance(t, dict) and t.get("kind") == "PASTURE"
                             and t.get("animal") and not t.get("cared_today")
                             and (x, y) not in self.cared_this_day),
            lambda t, x, y: (isinstance(t, dict) and t.get("kind") == "PASTURE"
                             and t.get("fertilizer_available")),
            lambda t, x, y: (isinstance(t, dict) and t.get("kind") == "PLANT"
                             and not t.get("watered_today")
                             and (x, y) not in self.watered_this_day),
            lambda t, x, y: (isinstance(t, dict) and t.get("kind") == "PASTURE"
                             and t.get("animal") is None and inv
                             and any(inv.get(a, 0) > 0 for a in ("COW", "SHEEP"))),
            lambda t, x, y: t is None,
            lambda t, x, y: isinstance(t, dict) and t.get("kind") == "WEED",
        ]

    def __call__(self, obs):
        if not isinstance(obs, dict):
            return {"farmer": ["PASS"], "hands": [], "market": []}
        player = obs.get("player", 0)
        farms = obs.get("farms", [])
        if not isinstance(farms, list) or player >= len(farms):
            return {"farmer": ["PASS"], "hands": [], "market": []}

        day = obs.get("day", 0)

        if self.opening.is_active(day):
            result = self.opening.execute(obs)
            if result is not None:
                return result

        farm = farms[player] or {}
        private = obs.get("private", {}) or {}
        shed = private.get("shed", {}) or {}
        seeds = private.get("seeds", {}) or {}
        inventories = private.get("inventories", [])
        hour = obs.get("hour", 0)

        if day != self.last_day:
            self.last_day = day
            self.watered_this_day = set()
            self.fed_this_day = set()
            self.cared_this_day = set()

        cows, sheep, pastures, empty_past = self._count_animals(farm)
        tasks = self._scan(farm, day)
        market = self._market(obs, tasks, cows, sheep, pastures, empty_past)
        assigned = set()

        def worker_act(wpos, winv):
            x, y = wpos
            tile = self._tile_at(farm, (x, y))
            winv = winv or {}

            inv_sum = sum(winv.values())
            if inv_sum > 5 and self._is_shed_adj((x, y)):
                return ["DROP"]
            if inv_sum > 8:
                targets = [(4, 4), (5, 4), (4, 5), (5, 5)]
                best = min(targets, key=lambda t: abs(t[0] - x) + abs(t[1] - y))
                if best != (x, y):
                    tx, ty = best
                    if ty < y:
                        return ["NORTH"]
                    if ty > y:
                        return ["SOUTH"]
                    if tx < x:
                        return ["WEST"]
                    if tx > x:
                        return ["EAST"]

            action = self._decide(tile, shed, seeds, day, winv, wpos, hour,
                                  cows, sheep, empty_past)
            if action and action[0] != "PASS":
                if action[0] == "WATER":
                    self.watered_this_day.add((x, y))
                elif action[0] == "FEED":
                    self.fed_this_day.add((x, y))
                elif action[0] == "CARE":
                    self.cared_this_day.add((x, y))
                return action

            if self._is_shed_adj((x, y)):
                for a in ("COW", "SHEEP"):
                    if shed.get(a, 0) > 0 and inv_sum == 0:
                        return ["PICKUP", a, 1]
                if shed.get("WHEAT", 0) > 0 and winv.get("WHEAT", 0) == 0 and tasks["feed"]:
                    return ["PICKUP", "WHEAT", min(3, shed["WHEAT"])]
                if inv_sum > 3:
                    return ["DROP"]

            for cond in self._move_priorities(shed, day, winv):
                tx, ty, direction = self._bfs((x, y), cond, farm, assigned)
                if direction:
                    assigned.add((tx, ty))
                    return [direction]

            return ["PASS"]

        farmer_inv = inventories[0] if inventories else {}
        farmer_action = worker_act(farm.get("farmer", [0, 0]), farmer_inv)

        hands_actions = []
        for i, hpos in enumerate(farm.get("hands", [])):
            h_inv = inventories[i + 1] if i + 1 < len(inventories) else {}
            hands_actions.append(worker_act(hpos, h_inv))

        return {"farmer": farmer_action, "hands": hands_actions, "market": market}


# =============================================================================
# ENTRY POINTS
# =============================================================================
agent = KaggricultureAgentV15()


def agent_fn(observation, configuration=None):
    return agent(observation)


def main_agent(observation, configuration=None):
    return agent(observation)
