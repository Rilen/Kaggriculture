"""
Kaggriculture Autonomous AI Agent — submission_v7.py
Experimento 1 (alavanca de receita): MELAO CEDO + VOLUME.

Base: submission.py (v2, 100% plantacao). Mudancas cirurgicas:
1. MELON_TARGET 18 -> 24 (mais melao, maior valor/tile).
2. _choose_plant prioriza MELON primeiro (leva 10 dias -> plantar o quanto antes),
   depois STRAWBERRY, depois WHEAT. Antes o v2 plantava o MENOR deficit, o que
   atrasava o melao (motor de dinheiro).
3. Compra mais sementes de melao (estoque alvo 4 -> 8).

Tudo o mais identico ao v2 (2 quadrantes, expansao cedo, 100% plantacao).
"""
from collections import deque

# ----------------------------------------------------------------------------
# Static game data (from the official Object Types / Price tables)
# ----------------------------------------------------------------------------
CROPS = {
    "WHEAT":      {"seed": 10,  "price": 25,  "first": 2,  "max": 4,  "ongoing": False},
    "CARROT":     {"seed": 20,  "price": 35,  "first": 2,  "max": 3,  "ongoing": False},
    "TOMATO":     {"seed": 50,  "price": 60,  "first": 8,  "max": 11, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "price": 120, "first": 10, "max": 16, "ongoing": True},
    "MELON":      {"seed": 80,  "price": 250, "first": 10, "max": 10, "ongoing": False},
}

ANIMALS = {
    "GOOSE": {"cost": 300, "struct": "COOP",     "product": "EGG",  "price": 50,  "interval": 1},
    "COW":   {"cost": 400, "struct": "PASTURE",  "product": "MILK", "price": 160, "interval": 2},
    "SHEEP": {"cost": 500, "struct": "PASTURE",  "product": "WOOL", "price": 200, "interval": 3},
}

SELLABLE = {"WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "EGG", "MILK", "WOOL", "FERTILIZER"}

# Build / planting targets
TARGET_COOPS = 0
TARGET_PASTURES = 0
WHEAT_TARGET = 12
STRAWBERRY_TARGET = 10
MELON_TARGET = 24            # [exp 1] 18 -> 24 (mais melao)

PLANT_DEADLINE = {"MELON": 18, "STRAWBERRY": 21, "TOMATO": 19, "CARROT": 25, "WHEAT": 27}
LIQUIDATE_DAY = 27

MAX_MARKET_ORDERS = 10


def _fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


class GranjaAgent:
    def __init__(self):
        self.last_day = -1
        self.watered = set()
        self.fed = set()
        self.cared = set()
        self.collected = set()

    # -- tile helpers --------------------------------------------------------
    @staticmethod
    def _tile(farm, pos):
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
    def _is_empty(tile):
        return tile is None

    @staticmethod
    def _shed_adjacent(pos, board=10):
        half = board // 2
        x, y = pos
        return x in (half - 1, half) and y in (half - 1, half)

    # -- BFS -----------------------------------------------------------------
    def _bfs_dir(self, start, predicate, farm, assigned):
        sx, sy = start
        tiles = farm.get("tiles", [])
        h = len(tiles)
        w = len(tiles[0]) if h else 0
        if h == 0:
            return None
        q = deque()
        q.append((sx, sy, None))
        seen = {(sx, sy)}
        while q:
            x, y, first = q.popleft()
            if (x, y) != (sx, sy):
                t = self._tile(farm, (x, y))
                if t != "LOCKED" and predicate(t, x, y) and (x, y) not in assigned:
                    return (x, y, first)
            for dx, dy, d in ((0, -1, "NORTH"), (0, 1, "SOUTH"),
                              (-1, 0, "WEST"), (1, 0, "EAST")):
                nx, ny = x + dx, y + dy
                if (nx, ny) not in seen and 0 <= nx < w and 0 <= ny < h:
                    seen.add((nx, ny))
                    nd = first if first else d
                    q.append((nx, ny, nd))
        return None

    # -- per-tile immediate action ------------------------------------------
    def _act_on_tile(self, tile, shed, seeds, day, inv, pos):
        if tile is None or tile == "LOCKED":
            return None
        if not isinstance(tile, dict):
            return None
        x, y = pos
        kind = tile.get("kind")

        if kind == "WEED":
            return ["DIG"]

        if kind == "PLANT":
            crop = tile.get("crop")
            info = CROPS.get(crop if isinstance(crop, str) else "", {})
            age = day - tile.get("planted_day", day)
            maxd = info.get("max", 4)
            watered = bool(tile.get("watered_today")) or (x, y) in self.watered
            if info.get("ongoing"):
                if tile.get("yield_units", 0) > 0:
                    return ["HARVEST"]
                if not watered:
                    return ["WATER"]
                if crop in ("MELON", "STRAWBERRY") and tile.get("fertilized_until_day", -1) < day and shed.get("FERTILIZER", 0) > 0:
                    return ["FERTILIZE"]
                return None
            else:
                if age >= maxd:
                    return ["HARVEST"]
                if not watered:
                    return ["WATER"]
                if crop in ("MELON", "STRAWBERRY") and tile.get("fertilized_until_day", -1) < day and shed.get("FERTILIZER", 0) > 0:
                    return ["FERTILIZE"]
                return None

        if kind in ("COOP", "PASTURE"):
            if tile.get("animal") is None:
                for item, qty in (inv or {}).items():
                    if qty > 0 and item in ANIMALS and ANIMALS[item]["struct"] == kind:
                        return ["PLACE", item]
                return None
            fed = bool(tile.get("fed_today")) or (x, y) in self.fed
            if tile.get("yield_units", 0) > 0:
                return ["HARVEST"]
            if not fed and shed.get("WHEAT", 0) > 0:
                return ["FEED"]
            if tile.get("fertilizer_available") and (x, y) not in self.collected:
                return ["COLLECT_FERTILIZER"]
            if not tile.get("cared_today") and (x, y) not in self.cared:
                return ["CARE"]
            return None

        return None

    # -- worker decision -----------------------------------------------------
    def _worker(self, pos, inv, farm, shed, seeds, day, counts, assigned):
        x, y = pos
        tile = self._tile(farm, pos)

        # 1) act on the tile we're standing on
        act = self._act_on_tile(tile, shed, seeds, day, inv, pos)
        if act:
            if act[0] == "WATER":
                self.watered.add((x, y))
            elif act[0] == "FEED":
                self.fed.add((x, y))
            elif act[0] == "CARE":
                self.cared.add((x, y))
            elif act[0] == "COLLECT_FERTILIZER":
                self.collected.add((x, y))
            return act

        # 2) shed logistics
        if self._shed_adjacent(pos):
            inv_sell = sum(v for k, v in (inv or {}).items() if k in SELLABLE)
            if inv_sell > 0:
                return ["DROP"]
            for animal in ("GOOSE", "COW"):
                if shed.get(animal, 0) > 0 and counts["empty_structure_for"][animal] > 0 and (not inv or sum(inv.values()) == 0):
                    return ["PICKUP", animal, 1]
            if shed.get("FERTILIZER", 0) > 0 and (not inv or sum(inv.values()) == 0) and counts["needs_fert"] > 0:
                return ["PICKUP", "FERTILIZER", 1]

        # 3) if carrying sellable goods and not at the shed, go dump them
        inv_sell = sum(v for k, v in (inv or {}).items() if k in SELLABLE)
        if inv_sell >= 3 and not self._shed_adjacent(pos):
            tgt = self._bfs_dir(pos, lambda t, x, y: self._shed_adjacent((x, y)), farm, assigned)
            if tgt:
                assigned.add((tgt[0], tgt[1]))
                return [tgt[2]]

        # 4) build / plant on an empty tile we occupy
        if self._is_empty(tile):
            if counts["coops"] < TARGET_COOPS and day < 28:
                return ["BUILD_COOP"]
            if counts["pastures"] < TARGET_PASTURES and day < 28:
                return ["BUILD_PASTURE"]
            plant = self._choose_plant(seeds, day, counts)
            if plant and seeds.get(plant, 0) > 0:
                return ["PLANT", plant]

        # 5) move toward the highest-priority task
        preds = [
            lambda t, x, y: isinstance(t, dict) and (
                (t.get("kind") == "PLANT" and ((CROPS.get(str(t.get("crop") or ""), {}).get("ongoing") and t.get("yield_units", 0) > 0) or
                 (not CROPS.get(str(t.get("crop") or ""), {}).get("ongoing") and (day - t.get("planted_day", day)) >= CROPS.get(str(t.get("crop") or ""), {}).get("max", 4))))
                or (t.get("kind") in ("COOP", "PASTURE") and t.get("animal") and t.get("yield_units", 0) > 0)
            ),
            lambda t, x, y: isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE") and t.get("animal") and not t.get("fed_today") and (x, y) not in self.fed and shed.get("WHEAT", 0) > 0,
            lambda t, x, y: isinstance(t, dict) and t.get("kind") == "PLANT" and not t.get("watered_today") and (x, y) not in self.watered,
            lambda t, x, y: isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE") and t.get("animal") and not t.get("cared_today") and (x, y) not in self.cared,
            lambda t, x, y: isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") in ("MELON", "STRAWBERRY") and t.get("fertilized_until_day", -1) < day and (x, y) not in self.watered and shed.get("FERTILIZER", 0) > 0,
            lambda t, x, y: isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE") and t.get("fertilizer_available") and (x, y) not in self.collected,
            lambda t, x, y: t == "WEED",
        ]
        for p in preds:
            tgt = self._bfs_dir(pos, p, farm, assigned)
            if tgt:
                assigned.add((tgt[0], tgt[1]))
                return [tgt[2]]

        # 6) expand: deliberately walk to an empty tile to build/plant
        if (counts["coops"] < TARGET_COOPS or counts["pastures"] < TARGET_PASTURES
                or self._choose_plant(seeds, day, counts) is not None):
            tgt = self._bfs_dir(pos, lambda t, x, y: t is None, farm, assigned)
            if tgt:
                assigned.add((tgt[0], tgt[1]))
                return [tgt[2]]

        return ["PASS"]

    def _choose_plant(self, seeds, day, counts):
        # [exp 1] MELAO primeiro (maior valor/tile, leva 10 dias -> plantar cedo),
        # depois MORANGO (ongoing), depois TRIGO.
        if day <= PLANT_DEADLINE["MELON"] and counts["melon"] < MELON_TARGET and seeds.get("MELON", 0) > 0:
            return "MELON"
        if day <= PLANT_DEADLINE["STRAWBERRY"] and counts["strawberry"] < STRAWBERRY_TARGET and seeds.get("STRAWBERRY", 0) > 0:
            return "STRAWBERRY"
        if day <= PLANT_DEADLINE["WHEAT"] and counts["wheat"] < WHEAT_TARGET and seeds.get("WHEAT", 0) > 0:
            return "WHEAT"
        return None

    # -- market --------------------------------------------------------------
    def _market(self, obs, farm, shed, seeds, day, counts):
        orders = []
        money = farm.get("money", 0)
        animals_total = counts["animals"]
        quads = len(farm.get("unlocked_quadrants", []))
        hires_today = farm.get("hires_today", 0)

        # --- HIRE a small daily crew (cheap labor) ---
        desired = 4 + min(4, day // 5)
        while hires_today < desired and len(orders) < MAX_MARKET_ORDERS - 2:
            cost = _fib(hires_today)
            if money < cost + 20:
                break
            orders.append(["HIRE"])
            money -= cost
            hires_today += 1

        # --- BUY_LAND: only the NE quadrant (2 quadrants total) ---
        if quads == 1 and money >= 1600:
            orders.append(["BUY_LAND"]); money -= 1000

        if day < LIQUIDATE_DAY:
            # --- BUY seeds (mais melao para suportar o volume) ---
            for crop, target in (("WHEAT", 10), ("STRAWBERRY", 5), ("MELON", 8)):
                have = seeds.get(crop, 0)
                if have < target and len(orders) < MAX_MARKET_ORDERS - 2:
                    need = target - have
                    cost = CROPS[crop]["seed"] * need
                    if money >= cost + 200:
                        orders.append(["BUY_SEED", crop, need]); money -= cost

            # --- safety: buy WHEAT if we can't feed our animals ---
            if shed.get("WHEAT", 0) < animals_total and money > 60:
                need = min(animals_total - shed.get("WHEAT", 0) + 3, (money - 50) // 30)
                if need > 0 and len(orders) < MAX_MARKET_ORDERS - 2:
                    orders.append(["BUY_PRODUCT", "WHEAT", need]); money -= need * 25

        # --- SELL: convert stored goods to cash ---
        sell_caps = {"EGG": 9999, "WHEAT": 9999, "MILK": 20, "WOOL": 12,
                     "STRAWBERRY": 20, "MELON": 15, "TOMATO": 20, "CARROT": 20,
                     "FERTILIZER": 10}
        floors = {"EGG": 1, "WHEAT": 1, "MILK": 15, "WOOL": 1, "STRAWBERRY": 20,
                  "MELON": 25, "TOMATO": 15, "CARROT": 10, "FERTILIZER": 20}
        prices = obs.get("market", {}).get("prices", {}) or {}
        wheat_reserve = animals_total + 3
        for item, qty in sorted(shed.items()):
            if qty <= 0 or item in ("GOOSE", "COW", "SHEEP"):
                continue
            if item == "WHEAT":
                sell_qty = qty - wheat_reserve
                if sell_qty <= 0:
                    continue
            else:
                sell_qty = qty
            if day >= LIQUIDATE_DAY:
                sell_qty = qty
            cap = sell_caps.get(item, 15)
            sell_qty = min(sell_qty, cap)
            price = prices.get(item, 0)
            if item != "EGG" and item != "WHEAT" and price < floors.get(item, 10):
                continue
            if sell_qty > 0 and len(orders) < MAX_MARKET_ORDERS:
                orders.append(["SELL", item, sell_qty])

        return orders[:MAX_MARKET_ORDERS]

    # -- main ----------------------------------------------------------------
    def __call__(self, obs):
        try:
            return self._run(obs)
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}

    def _run(self, obs):
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
            self.watered = set()
            self.fed = set()
            self.cared = set()
            self.collected = set()

        counts = self._count(farm, shed, day)
        assigned = set()

        def worker(pos, inv):
            return self._worker(pos, inv, farm, shed, seeds, day, counts, assigned)

        farmer_inv = inventories[0] if inventories else {}
        farmer_act = worker(farm.get("farmer", [0, 0]), farmer_inv)
        hands_acts = []
        for i, hpos in enumerate(farm.get("hands", [])):
            hinv = inventories[i + 1] if i + 1 < len(inventories) else {}
            hands_acts.append(worker(hpos, hinv))

        market = self._market(obs, farm, shed, seeds, day, counts)
        return {"farmer": farmer_act, "hands": hands_acts, "market": market}

    def _count(self, farm, shed, day):
        tiles = farm.get("tiles", [])
        coops = pastures = animals = empty_coops = empty_pastures = 0
        wheat = strawberry = melon = tomato = carrot = 0
        needs_fert = 0
        struct_for = {"GOOSE": 0, "COW": 0}
        for row in tiles:
            for t in row:
                if not isinstance(t, dict):
                    continue
                k = t.get("kind")
                if k == "PLANT":
                    c = t.get("crop")
                    if c == "WHEAT":
                        wheat += 1
                    elif c == "STRAWBERRY":
                        strawberry += 1
                    elif c == "MELON":
                        melon += 1
                    elif c == "TOMATO":
                        tomato += 1
                    elif c == "CARROT":
                        carrot += 1
                    if c in ("MELON", "STRAWBERRY") and t.get("fertilized_until_day", -1) < day:
                        needs_fert += 1
                elif k == "COOP":
                    coops += 1
                    if t.get("animal"):
                        animals += 1
                    else:
                        empty_coops += 1
                        struct_for["GOOSE"] += 1
                elif k == "PASTURE":
                    pastures += 1
                    if t.get("animal"):
                        animals += 1
                    else:
                        empty_pastures += 1
                        struct_for["COW"] += 1
        wheat_target = animals + 6
        return {
            "coops": coops, "pastures": pastures, "animals": animals,
            "empty_coops": empty_coops, "empty_pastures": empty_pastures,
            "wheat": wheat, "strawberry": strawberry, "melon": melon,
            "tomato": tomato, "carrot": carrot,
            "needs_fert": needs_fert, "empty_structure_for": struct_for,
            "wheat_target": wheat_target,
        }


agent = GranjaAgent()
def agent_fn(observation, configuration=None):
    return agent(observation)
def main_agent(observation, configuration=None):
    return agent(observation)
