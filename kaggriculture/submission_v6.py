"""
Kaggriculture Autonomous AI Agent — submission_v6.py
Motor economico de PECUARIA DE ALTA DENSIDADE (v23_fork + HealthStone).

Abandona a arquitetura puramente agricola. Foco em leite/la premium em escala,
com trigo proprio como racao. Estrutura de estados limpa para workers nao
colidirem (assigned set + prioridades deterministicas).

Diretrizes:
1. ORQUESTRACAO DA ABERTURA (Day 0): 5 HIRE + 2 COW + 2 SHEEP + sementes de
   WHEAT (racao) + WHEAT produto (racao imediata) + um pouco de MELON secundario.
   Caixa ~zero: o foco e infraestrutura animal, nao melao.
2. ENGINE DE LOGISTICA BULLETPROOF (prioridade absoluta):
   FEED (morte) > HARVEST (leite/la) > WATER (trigo->racao) > CARE (+18%) >
   HARVEST (trigo) > WEED REPAIR (DIG + re-trace local).
3. PIPELINE ESCALAVEL: reinveste leite/la em mais animais ate 8 COW + 6 SHEEP
   (14 pastagens), com racão garantida (compra WHEAT se faltar).
4. MERCADO DE ALTA FREQUENCIA: vende MILK/WOOL em lotes no inicio do ciclo
   diario (hour < 6) para capturar o premio antes do glut compartilhado.

Mantem aliases agent / agent_fn / main_agent.
"""
from collections import deque

# ----------------------------------------------------------------------------
# Static game data
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

# ----------------------------------------------------------------------------
# [1] Abertura v23_fork (Day 0)
# ----------------------------------------------------------------------------
OPENING_HIRES = 5
OPENING_COWS = 2
OPENING_SHEEP = 2
OPENING_WHEAT_SEEDS = 14    # racao (plantar trigo)
OPENING_MELON_SEEDS = 6     # secundario (usa caixa restante)
OPENING_WHEAT_BUY = 12      # racao imediata (antes de o trigo crescer)

# ----------------------------------------------------------------------------
# [3] Pecuaria de alta densidade
# ----------------------------------------------------------------------------
TARGET_COWS = 8
TARGET_SHEEP = 6
TARGET_PASTURES = TARGET_COWS + TARGET_SHEEP   # 14
TARGET_COOPS = 0
WHEAT_TARGET = 16            # plantas de trigo para racao
MELON_TARGET = 10            # secundario

PLANT_DEADLINE = {"MELON": 18, "STRAWBERRY": 21, "TOMATO": 19, "CARROT": 25, "WHEAT": 27}
LIQUIDATE_DAY = 27

MAX_MARKET_ORDERS = 10

# ----------------------------------------------------------------------------
# [4] Mercado de alta frequencia (front-run premium)
# ----------------------------------------------------------------------------
FRONT_RUN_HOUR = 6
MILK_FLOOR = 60
WOOL_FLOOR = 80

# Labor scaling (maos para manter 14 pastagens + trigo)
HANDS_BASE = 4
HANDS_DAY_BONUS = 4
MAX_HANDS = 12
SEED_RESERVE = 250


def _fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


class GranjaV6:
    def __init__(self):
        self.last_day = -1
        self.watered = set()
        self.fed = set()
        self.cared = set()
        self.collected = set()
        self.opening_done = False

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

        # [2] WEED REPAIR OVERLAY: DIG antes de qualquer PLANT/BUILD/CARE
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
                return None
            else:
                if age >= maxd:
                    return ["HARVEST"]
                if not watered:
                    return ["WATER"]
                return None

        if kind in ("COOP", "PASTURE"):
            if tile.get("animal") is None:
                for item, qty in (inv or {}).items():
                    if qty > 0 and item in ANIMALS and ANIMALS[item]["struct"] == kind:
                        return ["PLACE", item]
                return None
            # [2] PRIORIDADE ABSOLUTA: FEED antes de HARVEST (morte vs coleta)
            fed = bool(tile.get("fed_today")) or (x, y) in self.fed
            if not fed and shed.get("WHEAT", 0) > 0:
                return ["FEED"]
            if tile.get("yield_units", 0) > 0:
                return ["HARVEST"]
            if not tile.get("cared_today") and (x, y) not in self.cared:
                return ["CARE"]
            return None

        return None

    # -- worker decision -----------------------------------------------------
    def _worker(self, pos, inv, farm, shed, seeds, day, counts, assigned):
        x, y = pos
        tile = self._tile(farm, pos)

        # 1) agir sobre o tile em que estamos
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

        # 2) logistica do galpao
        if self._shed_adjacent(pos):
            inv_sell = sum(v for k, v in (inv or {}).items() if k in SELLABLE)
            if inv_sell > 0:
                return ["DROP"]
            # pegar animal do galpao para colocar em pastagem vazia
            for animal in ("COW", "SHEEP"):
                if shed.get(animal, 0) > 0 and counts["empty_pastures"] > 0 and (not inv or sum(inv.values()) == 0):
                    return ["PICKUP", animal, 1]

        # 3) descarregar se carregando
        inv_sell = sum(v for k, v in (inv or {}).items() if k in SELLABLE)
        if inv_sell >= 3 and not self._shed_adjacent(pos):
            tgt = self._bfs_dir(pos, lambda t, x, y: self._shed_adjacent((x, y)), farm, assigned)
            if tgt:
                assigned.add((tgt[0], tgt[1]))
                return [tgt[2]]

        # 4) construir pastagem / plantar trigo em tile vazio
        #    [correcao] NAO constroi/planta se houver animal com fome (FEED 1o)
        if tile is None and counts.get("hungry", 0) == 0:
            if counts["pastures"] < TARGET_PASTURES and day < 28:
                counts["pastures"] += 1  # [correcao] evita overshoot entre workers
                return ["BUILD_PASTURE"]
            plant = self._choose_plant(seeds, day, counts)
            if plant and seeds.get(plant, 0) > 0:
                return ["PLANT", plant]

        # 5) mover-se para a tarefa de maior prioridade (bulletproof)
        preds = [
            # FEED (morte)
            lambda t, x, y: isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE") and t.get("animal") and not t.get("fed_today") and (x, y) not in self.fed and shed.get("WHEAT", 0) > 0,
            # HARVEST animal (leite/la)
            lambda t, x, y: isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE") and t.get("animal") and t.get("yield_units", 0) > 0,
            # WATER planta (trigo -> racao)
            lambda t, x, y: isinstance(t, dict) and t.get("kind") == "PLANT" and not t.get("watered_today") and (x, y) not in self.watered,
            # CARE animal (+18%)
            lambda t, x, y: isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE") and t.get("animal") and not t.get("cared_today") and (x, y) not in self.cared,
            # HARVEST planta (trigo pronto)
            lambda t, x, y: isinstance(t, dict) and t.get("kind") == "PLANT" and not CROPS.get(str(t.get("crop") or ""), {}).get("ongoing") and (day - t.get("planted_day", day)) >= CROPS.get(str(t.get("crop") or ""), {}).get("max", 4),
            # limpar mato
            lambda t, x, y: t == "WEED",
        ]
        for p in preds:
            tgt = self._bfs_dir(pos, p, farm, assigned)
            if tgt:
                assigned.add((tgt[0], tgt[1]))
                return [tgt[2]]

        # 6) expandir para tile vazio (construir pastagem / plantar)
        if (counts["pastures"] < TARGET_PASTURES
                or self._choose_plant(seeds, day, counts) is not None):
            tgt = self._bfs_dir(pos, lambda t, x, y: t is None, farm, assigned)
            if tgt:
                assigned.add((tgt[0], tgt[1]))
                if counts["pastures"] < TARGET_PASTURES:
                    counts["pastures"] += 1  # [correcao] evita overshoot
                return [tgt[2]]

        return ["PASS"]

    def _choose_plant(self, seeds, day, counts):
        # [correcao] TRIGO (racao) e CRITICO DE MORTE: plantar primeiro, sempre.
        if day <= PLANT_DEADLINE["WHEAT"] and counts["wheat"] < WHEAT_TARGET and seeds.get("WHEAT", 0) > 0:
            return "WHEAT"
        # melao secundario (so depois de garantir a racao)
        if day <= PLANT_DEADLINE["MELON"] and counts["melon"] < MELON_TARGET and seeds.get("MELON", 0) > 0:
            return "MELON"
        return None

    def _desired_hands(self, day, quads):
        base = HANDS_BASE + min(HANDS_DAY_BONUS, day // 5)
        area = 2 * max(0, quads - 1)
        return min(base + area, MAX_HANDS)

    # -- market --------------------------------------------------------------
    def _market(self, obs, farm, shed, seeds, day, counts):
        orders = []
        money = farm.get("money", 0)
        animals_total = counts["animals"]
        quads = len(farm.get("unlocked_quadrants", []))
        hires_today = farm.get("hires_today", 0)
        hour = obs.get("hour", 0)
        prices = obs.get("market", {}).get("prices", {}) or {}

        def room():
            return len(orders) < MAX_MARKET_ORDERS - 1

        # --- [1] ABERTURA Day 0: 5 HIRE + 2 COW + 2 SHEEP + racao ---
        desired = OPENING_HIRES if day == 0 else self._desired_hands(day, quads)
        while hires_today < desired and room():
            cost = _fib(hires_today)
            if money < cost + 30:
                break
            orders.append(["HIRE"])
            money -= cost
            hires_today += 1

        if day == 0 and not self.opening_done:
            for animal, target in (("COW", OPENING_COWS), ("SHEEP", OPENING_SHEEP)):
                have = counts["cows"] if animal == "COW" else counts["sheep"]
                if have < target and money >= ANIMALS[animal]["cost"] and room():
                    n = target - have
                    orders.append(["BUY_ANIMAL", animal, n])
                    money -= ANIMALS[animal]["cost"] * n
            for crop, target in (("WHEAT", OPENING_WHEAT_SEEDS), ("MELON", OPENING_MELON_SEEDS)):
                have = seeds.get(crop, 0)
                if have < target and room():
                    need = target - have
                    cost = CROPS[crop]["seed"] * need
                    if money >= cost + 50:
                        orders.append(["BUY_SEED", crop, need]); money -= cost
            # racao imediata (antes de o trigo crescer)
            if shed.get("WHEAT", 0) < OPENING_WHEAT_BUY and money >= OPENING_WHEAT_BUY * 25 + 50 and room():
                need = OPENING_WHEAT_BUY - shed.get("WHEAT", 0)
                orders.append(["BUY_PRODUCT", "WHEAT", need]); money -= need * 25
            self.opening_done = True

        # --- BUY_LAND: expandir quando o caixa do leite/la entrar ---
        if quads == 1 and money >= 1600 and day >= 1:
            orders.append(["BUY_LAND"]); money -= 1000

        if day < LIQUIDATE_DAY:
            # sementes de rotina (racao primeiro)
            for crop, target in (("WHEAT", 10), ("MELON", 4)):
                have = seeds.get(crop, 0)
                if have < target and room():
                    need = target - have
                    cost = CROPS[crop]["seed"] * need
                    if money >= cost + SEED_RESERVE:
                        orders.append(["BUY_SEED", crop, need]); money -= cost

            # [3] reinvestir em animais ate 8C+6S
            if counts["empty_pastures"] > 0 and money > ANIMALS["COW"]["cost"] + 300 and shed.get("WHEAT", 0) >= 3:
                if counts["cows"] < TARGET_COWS and room():
                    n = min(counts["empty_pastures"], TARGET_COWS - counts["cows"], 2)
                    if n > 0:
                        orders.append(["BUY_ANIMAL", "COW", n]); money -= ANIMALS["COW"]["cost"] * n
            if counts["empty_pastures"] > 0 and money > ANIMALS["SHEEP"]["cost"] + 300 and shed.get("WHEAT", 0) >= 3:
                if counts["sheep"] < TARGET_SHEEP and room():
                    n = min(counts["empty_pastures"], TARGET_SHEEP - counts["sheep"], 2)
                    if n > 0:
                        orders.append(["BUY_ANIMAL", "SHEEP", n]); money -= ANIMALS["SHEEP"]["cost"] * n

            # seguranca de racao: nunca deixar os animais sem comida
            if shed.get("WHEAT", 0) < animals_total + 3 and money > 60:
                need = min(animals_total + 3 - shed.get("WHEAT", 0) + 2, (money - 50) // 30)
                if need > 0 and room():
                    orders.append(["BUY_PRODUCT", "WHEAT", need]); money -= need * 25

        # --- [4] MERCADO DE ALTA FREQUENCIA: front-run de MILK/WOOL ---
        if hour < FRONT_RUN_HOUR and day >= 1:
            for item, floor in (("MILK", MILK_FLOOR), ("WOOL", WOOL_FLOOR)):
                qty = shed.get(item, 0)
                price = prices.get(item, 0)
                if qty > 0 and price >= floor and room():
                    orders.append(["SELL", item, qty])
        # fim do dia: liquidar premium restante (nao segurar)
        elif hour >= 20 and day >= 1:
            for item in ("MILK", "WOOL"):
                qty = shed.get(item, 0)
                if qty > 0 and room():
                    orders.append(["SELL", item, qty])

        # --- SELL: demais itens (trigo excedente, melao) ---
        sell_caps = {"EGG": 9999, "WHEAT": 9999, "STRAWBERRY": 20, "MELON": 15,
                     "TOMATO": 20, "CARROT": 20, "FERTILIZER": 10}
        floors = {"EGG": 1, "WHEAT": 1, "STRAWBERRY": 20, "MELON": 25,
                  "TOMATO": 15, "CARROT": 10, "FERTILIZER": 20}
        wheat_reserve = animals_total + 5
        for item, qty in sorted(shed.items()):
            if qty <= 0 or item in ("GOOSE", "COW", "SHEEP", "MILK", "WOOL"):
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
        cows = sheep = hungry = 0
        wheat = strawberry = melon = tomato = carrot = 0
        for row in tiles:
            for t in row:
                if not isinstance(t, dict):
                    continue
                k = t.get("kind")
                if k == "PLANT":
                    c = t.get("crop")
                    if c == "WHEAT":
                        wheat += 1
                    elif c == "MELON":
                        melon += 1
                    elif c == "STRAWBERRY":
                        strawberry += 1
                    elif c == "TOMATO":
                        tomato += 1
                    elif c == "CARROT":
                        carrot += 1
                elif k == "COOP":
                    coops += 1
                    if t.get("animal"):
                        animals += 1
                        if not t.get("fed_today"):
                            hungry += 1
                    else:
                        empty_coops += 1
                elif k == "PASTURE":
                    pastures += 1
                    a = t.get("animal")
                    if a:
                        animals += 1
                        if a == "COW":
                            cows += 1
                        elif a == "SHEEP":
                            sheep += 1
                        if not t.get("fed_today"):
                            hungry += 1
                    else:
                        empty_pastures += 1
        return {
            "coops": coops, "pastures": pastures, "animals": animals,
            "empty_coops": empty_coops, "empty_pastures": empty_pastures,
            "cows": cows, "sheep": sheep, "hungry": hungry,
            "wheat": wheat, "strawberry": strawberry, "melon": melon,
            "tomato": tomato, "carrot": carrot,
            "needs_fert": 0, "empty_structure_for": {"GOOSE": 0, "COW": empty_pastures, "SHEEP": empty_pastures},
            "wheat_target": animals + 6,
        }


agent = GranjaV6()
def agent_fn(observation, configuration=None):
    return agent(observation)
def main_agent(observation, configuration=None):
    return agent(observation)
