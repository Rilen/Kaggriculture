"""
Kaggriculture Autonomous AI Agent — "Granja" engine (ground-up rewrite)

Core economic thesis (derived from the rules / price table):
  * Animals produce INDEFINITELY while fed. Geese are the backbone:
      - GOOSE costs $300, yields 1 EGG/day, EGG price is stable (~$40-50) because
        its glut target is only 0.20 (it barely crashes even under heavy supply).
      - FEED (1 WHEAT/day) + CARE (1 action/day) doubles output: banked care bonus
        pays out on the daily production -> 2 EGGS/day per goose.
      - Self-grown WHEAT (seed $10 -> 4-6 WHEAT) makes feeding nearly free.
  * STRAWBERRY (ongoing, base $120) and MELON (one-time, base $250) add diversity /
    early cash but their markets crash hard on glut, so we cap volumes and lean on
    town demand (which grows monotonically and absorbs supply late game).
  * Hired hands are CHEAP (fib cost: 1,1,2,3,5,8... resets daily) -> labor is not the
    bottleneck; we hire a small crew every day to multiply tile actions.
  * Land expands the tile budget: BUY_LAND 1k/2k/4k.
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
TARGET_PASTURES = 0          # drop fragile animal engine -> reliable crop economy
WHEAT_TARGET = 12             # sell surplus + buffer
STRAWBERRY_TARGET = 10        # ongoing, moderate (crash risk -> keep moderate)
MELON_TARGET = 18             # highest value/tile, tiny volume -> safe to sell lots

# When to stop planting long crops (growth days must fit before day 30)
PLANT_DEADLINE = {"MELON": 18, "STRAWBERRY": 21, "TOMATO": 19, "CARROT": 25, "WHEAT": 27}
LIQUIDATE_DAY = 27           # stop buying capital, dump shed to cash

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
    def _is_struct(tile):
        return isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE")

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
            # already cared+fed+collected this day: nothing to do here
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
            # pick up an animal we still need to place
            for animal in ("GOOSE", "COW"):
                if shed.get(animal, 0) > 0 and counts["empty_structure_for"][animal] > 0 and (not inv or sum(inv.values()) == 0):
                    return ["PICKUP", animal, 1]
            # pick up fertilizer if we have spare and want to fertilize later
            if shed.get("FERTILIZER", 0) > 0 and (not inv or sum(inv.values()) == 0) and counts["needs_fert"] > 0:
                return ["PICKUP", "FERTILIZER", 1]

        # 3) if carrying sellable goods and not at the shed, go dump them
        #    (especially WHEAT: animals can only be fed from the shed)
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
            # nothing to plant -> free a weed-free empty tile is fine; move on

        # 5) move toward the highest-priority task.
        # Feeding animals is DEATH-CRITICAL (2 missed feeds -> escaped/unrecoverable,
        # a $300+ loss), so it outranks watering plants (which only cost yield on a
        # single miss). Harvesting ready produce collects cash we've already earned.
        preds = [
            # harvest ready plants & animals (collect cash already produced)
            lambda t, x, y: isinstance(t, dict) and (
                (t.get("kind") == "PLANT" and ((CROPS.get(str(t.get("crop") or ""), {}).get("ongoing") and t.get("yield_units", 0) > 0) or
                 (not CROPS.get(str(t.get("crop") or ""), {}).get("ongoing") and (day - t.get("planted_day", day)) >= CROPS.get(str(t.get("crop") or ""), {}).get("max", 4))))
                or (t.get("kind") in ("COOP", "PASTURE") and t.get("animal") and t.get("yield_units", 0) > 0)
            ),
            # feed unfed animals (death-critical)
            lambda t, x, y: isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE") and t.get("animal") and not t.get("fed_today") and (x, y) not in self.fed and shed.get("WHEAT", 0) > 0,
            # water unwatered plants (daily; prevents death / low yield)
            lambda t, x, y: isinstance(t, dict) and t.get("kind") == "PLANT" and not t.get("watered_today") and (x, y) not in self.watered,
            # care animals (banks +1/day -> doubles goose output)
            lambda t, x, y: isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE") and t.get("animal") and not t.get("cared_today") and (x, y) not in self.cared,
            # fertilize high-value crops
            lambda t, x, y: isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") in ("MELON", "STRAWBERRY") and t.get("fertilized_until_day", -1) < day and (x, y) not in self.watered and shed.get("FERTILIZER", 0) > 0,
            # collect fertilizer
            lambda t, x, y: isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE") and t.get("fertilizer_available") and (x, y) not in self.collected,
            # clear weeds
            lambda t, x, y: t == "WEED",
        ]
        for p in preds:
            tgt = self._bfs_dir(pos, p, farm, assigned)
            if tgt:
                assigned.add((tgt[0], tgt[1]))
                return [tgt[2]]

        # 6) expand: deliberately walk to an empty tile to build a structure
        #    or plant a crop (this is what makes the farm actually grow)
        if (counts["coops"] < TARGET_COOPS or counts["pastures"] < TARGET_PASTURES
                or self._choose_plant(seeds, day, counts) is not None):
            tgt = self._bfs_dir(pos, lambda t, x, y: t is None, farm, assigned)
            if tgt:
                assigned.add((tgt[0], tgt[1]))
                return [tgt[2]]

        return ["PASS"]

    def _choose_plant(self, seeds, day, counts):
        # Grow all crops in PARALLEL: pick the crop furthest below its target so
        # high-value MELON/STRAWBERRY aren't starved by the wheat pipeline.
        candidates = [
            ("WHEAT", WHEAT_TARGET, counts["wheat"], PLANT_DEADLINE["WHEAT"]),
            ("STRAWBERRY", STRAWBERRY_TARGET, counts["strawberry"], PLANT_DEADLINE["STRAWBERRY"]),
            ("MELON", MELON_TARGET, counts["melon"], PLANT_DEADLINE["MELON"]),
        ]
        best, best_def = None, 999
        for name, tgt, have, deadline in candidates:
            if day <= deadline and have < tgt:
                deficit = tgt - have
                if deficit < best_def:
                    best_def, best = deficit, name
        if best and seeds.get(best, 0) > 0:
            return best
        if day <= PLANT_DEADLINE["WHEAT"]:
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
        # Hands are very cheap (fib: 1,1,2,3,5,8...), so keep hiring whenever we
        # can afford at least one more. NEVER let labor collapse: with no hands
        # the single farmer cannot maintain the farm and everything dies.
        desired = 4 + min(4, day // 5)
        while hires_today < desired and len(orders) < MAX_MARKET_ORDERS - 2:
            cost = _fib(hires_today)
            if money < cost + 20:
                break
            orders.append(["HIRE"])
            money -= cost
            hires_today += 1

        # --- BUY_LAND: only the NE quadrant (2 quadrants total) ---
        # Staying dense avoids spreading tiles across the board, which would
        # waste most turns on travel. The 2nd quadrant doubles tile count.
        if quads == 1 and money >= 1600:
            orders.append(["BUY_LAND"]); money -= 1000

        if day < LIQUIDATE_DAY:
            # --- BUY seeds to keep the pipeline stocked ---
            for crop, target in (("WHEAT", 10), ("STRAWBERRY", 5), ("MELON", 4)):
                have = seeds.get(crop, 0)
                if have < target and len(orders) < MAX_MARKET_ORDERS - 2:
                    need = target - have
                    cost = CROPS[crop]["seed"] * need
                    if money >= cost + 200:
                        orders.append(["BUY_SEED", crop, need]); money -= cost

            # --- BUY animals to fill empty structures (only when we can feed them) ---
            if counts["empty_coops"] > 0 and money > ANIMALS["GOOSE"]["cost"] + 500 and shed.get("WHEAT", 0) >= 5:
                n = min(counts["empty_coops"], 2)
                if len(orders) < MAX_MARKET_ORDERS - 2:
                    orders.append(["BUY_ANIMAL", "GOOSE", n]); money -= ANIMALS["GOOSE"]["cost"] * n
            if counts["empty_pastures"] > 0 and money > ANIMALS["COW"]["cost"] + 500 and shed.get("WHEAT", 0) >= 3:
                n = min(counts["empty_pastures"], 1)
                if len(orders) < MAX_MARKET_ORDERS - 2:
                    orders.append(["BUY_ANIMAL", "COW", n]); money -= ANIMALS["COW"]["cost"] * n

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
                sell_qty = qty  # dump everything endgame
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

        # ---- count state ----
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
