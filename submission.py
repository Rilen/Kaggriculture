"""
Kaggriculture Autonomous AI Agent — Version 17 (v17)

Base: v15 (Fixed Asset Engine — baseline vencedor $38.943 vs starter)

Diagnostico Fase 6.5 (5 seeds x starter):
  v15: $38.943 media  — flywheel MILK/WOOL funciona
  v16: $11.315 media  — regressao por WHEAT farming de baixo valor
  Resultado: v16 REJECTED

Hipotese para v17 (baseada em replay do adversario $51.706):
  Adversario faz: 8 COW + 2 SHEEP (MILK/WOOL flywheel)
               + 9 STRAWBERRY (alto valor + demanda de lojas)
  Nao faz: WHEAT como cultura comercial primaria

Mudancas v17 vs v15 (apenas 4 pontos):

  1. OPENING: MELON 12 -> MELON 9 + STRAWBERRY 3
     Abre espaco para STRAWBERRY no early sem custar o flywheel animal.
     Capital cai ~$150 a mais — toleravel dado seed money de $3000.

  2. WHEAT feed buffer dinamico (preco real do mercado)
     v15 usa: buy_n * 30 (hardcode)
     v17 usa: buy_n * wheat_price_atual
     Evita ordens invalidas quando trigo esta caro.

  3. STRAWBERRY em tiles vagos apos objetivo de pasture satisfeito
     v15: tile vazio -> BUILD_PASTURE ate target | depois MELON/WHEAT
     v17: tile vazio -> BUILD_PASTURE ate target | depois STRAWBERRY | depois MELON
     WHEAT nao planta como comercial — apenas feed/seed
     
  4. PICKUP animal gate: apenas se empty_past > 0
     v15: PICKUP COW/SHEEP sempre que junto ao shed com inv_sum==0
     v17: PICKUP COW/SHEEP apenas se ha pastagem vazia aguardando
     Evita loop de transporte inutil que compite com FEED/CARE

  5. BUY_SEED STRAWBERRY: ate 3 seeds, dias 0-15, apenas se money > 1200
     Compra conservadora que nao ameaca o capital do flywheel.

Preservado identico ao v15:
  - BFS bidirecional (_bfs)
  - Scanner (_scan)
  - _move_priorities (incluindo WATER para plantas)
  - Targets de animais (TARGET_COW=8, TARGET_SHEEP=6)
  - BUY_LAND timing (dia 7 e 11)
  - HIRE adaptativo
  - Toda logica de FEED/CARE/HARVEST
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

# Preservado do v15 — flywheel animal e a espinha dorsal economica
TARGET_COW      = 8
TARGET_SHEEP    = 6
TARGET_PASTURES = 14

# STRAWBERRY: ciclo de 10-16 dias; so planta se ha tempo para fechar
STRAWBERRY_MIN_DAYS_LEFT = 12

# A.11 — Seb Meta Copy targets
STRAWBERRY_TARGET = 15


# =============================================================================
# OPENING BOOK — Dia 0
# =============================================================================
class OpeningBook:
    """
    Opening v17 (baseado no v15 com ajuste minimo):
      Hour 1: 5 HIRE + 2 SHEEP + 2 COW + WHEAT 7 + MELON 9 + STRAWBERRY 3
      Hour 2: BUY_PRODUCT WHEAT 2

    Diferenca vs v15: MELON 12 -> MELON 9 + STRAWBERRY 3
    Custo adicional: 3 * $100 = $300 mais em sementes vs 3 * $80 economizados = net -$60
    Capital inicial segue viavel para o flywheel animal.
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
        if ty < y: return ["NORTH"]
        if ty > y: return ["SOUTH"]
        if tx < x: return ["WEST"]
        if tx > x: return ["EAST"]
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
        tile  = self._tile_at(tiles, x, y)
        inv   = inv   or {}
        shed  = shed  or {}
        seeds = seeds or {}

        # Hora 2-5: PICKUP + BUILD + PLACE
        if hour <= 5:
            if idx == -1 and inv.get("COW",   0) == 0 and shed.get("COW",   0) > 0:
                return ["PICKUP", "COW", 2]
            if idx == 0  and inv.get("SHEEP", 0) == 0 and shed.get("SHEEP", 0) > 0:
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

        # Planta: STRAWBERRY primeiro, depois MELON, depois WHEAT
        if tile is None and hour <= 20:
            for crop in ("STRAWBERRY", "MELON", "WHEAT"):
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

        if hour <= 20 and any(seeds.get(c, 0) > 0 for c in ("STRAWBERRY", "MELON", "WHEAT")):
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

        player  = obs.get("player", 0)
        farms   = obs.get("farms") or [{}]
        farm    = (farms[player] if player < len(farms) else {}) or {}
        private = obs.get("private") or {}
        shed    = private.get("shed")   or {}
        seeds   = private.get("seeds")  or {}
        invs    = private.get("inventories") or []
        tiles   = farm.get("tiles") or []

        market = []
        if hour == 1:
            # v17 vs v15: MELON 12 -> MELON 9 + STRAWBERRY 3
            market = [
                ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"],
                ["BUY_ANIMAL", "SHEEP", 2],
                ["BUY_ANIMAL", "COW",   2],
                ["BUY_SEED",   "WHEAT", 7],
                ["BUY_SEED",   "MELON", 9],         # era 12
                ["BUY_SEED",   "STRAWBERRY", 3],    # NOVO — alto valor + lojas
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
# ENGINE DINAMICO — Mid/Late (v17: v15 + STRAWBERRY + animal survival fix)
# =============================================================================
class KaggricultureAgentV17:
    def __init__(self):
        self.opening = OpeningBook()
        self.last_day = -1
        self.watered_this_day = set()
        self.fed_this_day     = set()
        self.cared_this_day   = set()
        self.worker_history   = {}
        self.worker_targets   = {}
        self.worker_failures  = {}
        self.telemetry = {
            "invalid_action_intercepted": 0,
            "feed_precondition_fail": 0,
            "place_precondition_fail": 0,
            "plant_precondition_fail": 0,
            "water_precondition_fail": 0,
            "care_precondition_fail": 0,
            "circuit_breaker_triggered": 0,
            "replan_count": 0,
            "max_consecutive_same_intent": 0,
            "target_claims": 0,
            "target_releases": 0,
            "target_changes": 0,
            "target_persistence_turns": 0,
            "claims_released_on_arrival": 0,
            "claims_released_after_productive_action": 0,
            "claims_released_due_to_invalid_target": 0,
            "claims_released_due_to_unreachable_target": 0,
        }

    @staticmethod
    def _tile_at(farm, pos):
        if not isinstance(pos, (list, tuple)) or len(pos) != 2:
            return None
        x, y  = pos
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

    # -------------------------------------------------------------------------
    # BFS bidirecional — IDENTICO ao v15
    # -------------------------------------------------------------------------
    def _bfs(self, start, condition, farm, exclude):
        sx, sy = start
        tiles  = farm.get("tiles", [])
        bh     = len(tiles)
        bw     = len(tiles[0]) if bh else 0
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

        fwd_queue   = deque([(sx, sy)])
        fwd_visited = {(sx, sy): None}  # type: dict[tuple[int, int], str | None]

        bwd_queue   = deque(targets)
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
                                if   curr_x > nx: first_dir = "EAST"
                                elif curr_x < nx: first_dir = "WEST"
                                elif curr_y > ny: first_dir = "SOUTH"
                                elif curr_y < ny: first_dir = "NORTH"
                            return target[0], target[1], first_dir
                        if (nx, ny) not in bwd_visited:
                            bwd_visited[(nx, ny)] = target
                            bwd_queue.append((nx, ny))

        return None, None, None

    # -------------------------------------------------------------------------
    # Scanner — IDENTICO ao v15
    # -------------------------------------------------------------------------
    def _count_animals(self, farm):
        cows = sheep = pastures = empty_past = 0
        for row in farm.get("tiles", []):
            for t in row if isinstance(row, list) else []:
                if isinstance(t, dict) and t.get("kind") == "PASTURE":
                    pastures += 1
                    if   t.get("animal") == "COW":   cows  += 1
                    elif t.get("animal") == "SHEEP":  sheep += 1
                    elif not t.get("animal"):         empty_past += 1
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
                    if not t.get("fed_today")   and (x, y) not in self.fed_this_day:
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
                    age  = day - t.get("planted_day", day)
                    if age >= info.get("max", 2) or t.get("yield_units", 0) > 0:
                        tasks["harvest"].append((x, y))
                elif k == "WEED":
                    tasks["weeds"].append((x, y))
        return tasks

    # -------------------------------------------------------------------------
    # Market — v15 + 3 mudancas pontuais
    # -------------------------------------------------------------------------
    def _market(self, obs, tasks, cows, sheep, pastures, empty_past):
        player        = obs.get("player", 0)
        farm          = obs.get("farms", [{}])[player]
        private       = obs.get("private", {})
        day           = obs.get("day",  0)
        hour          = obs.get("hour", 0)
        shed          = private.get("shed",  {}) or {}
        seeds         = private.get("seeds", {}) or {}
        money         = farm.get("money", 0)
        n_quads       = len(farm.get("unlocked_quadrants", []))
        current_hands = len(farm.get("hands") or [])
        hires_today   = farm.get("hires_today", 0) or 0
        # MUDANCA 2: preco real do trigo (era hardcode 30)
        wheat_price   = obs.get("market", {}).get("prices", {}).get("WHEAT", 30)
        days_left     = 29 - day

        orders = []

        if day >= 28:
            for item, qty in sorted(shed.items()):
                if qty > 0 and item not in ("GOOSE", "COW", "SHEEP"):
                    orders.append(["SELL", item, qty])
            return orders[:MAX_MARKET_ORDERS]

        total_shed = sum(v for k, v in shed.items() if k not in ("GOOSE", "COW", "SHEEP"))
        force      = total_shed > SHED_SOFT_CAP or hour >= 21

        # SELL — identico ao v15
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
                keep = 0 if force or item in ("MILK", "WOOL", "MELON", "STRAWBERRY") else 1
                sell = qty - keep
            if sell > 0:
                orders.append(["SELL", item, sell])

        # BUY_PRODUCT WHEAT — MUDANCA 2: usa wheat_price real
        wheat_need = (cows + sheep) * 2 + 4
        wheat_have = shed.get("WHEAT", 0)
        if wheat_have < wheat_need and money > 50 and len(orders) < MAX_MARKET_ORDERS:
            buy_n = min(wheat_need - wheat_have, 6)
            if money > buy_n * wheat_price + 20:  # era: buy_n * 30 + 20
                orders.append(["BUY_PRODUCT", "WHEAT", buy_n])
                money -= buy_n * wheat_price

        # BUY_PRODUCT FERTILIZER — A.11: only if we have STRAWBERRY/MELON planted
        strw_count = 0
        melon_count = 0
        for row in farm.get("tiles", []):
            for tile in row:
                if isinstance(tile, dict):
                    if tile.get("crop") == "STRAWBERRY":
                        strw_count += 1
                    elif tile.get("crop") == "MELON":
                        melon_count += 1
        
        if (strw_count > 0 or melon_count > 0) and money > 800 and len(orders) < MAX_MARKET_ORDERS:
            buy_n = min(3, MAX_MARKET_ORDERS - len(orders))
            if money > 100 * buy_n + 800:
                orders.append(["BUY_PRODUCT", "FERTILIZER", buy_n])
                money -= 100 * buy_n

        # HIRE adaptativo — A.11: consistent hiring, but with day 1 guard
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
        elif day <= 20:
            target_h = 12
        else:
            target_h = 10

        urgent = (len(tasks["feed"]) + len(tasks["care"])
                  + len(tasks["harvest"]) + len(tasks["water"]))
        if urgent > 15:
            target_h = min(target_h + 3, 14)

        needed   = max(0, target_h - current_hands)
        cost_est = sum(fib[min(hires_today + i, len(fib) - 1)] for i in range(needed))
        reserve  = 30 if day <= 3 else (100 if day <= 8 else 300)

        if needed > 0 and money > cost_est + reserve:
            for i in range(min(needed, MAX_MARKET_ORDERS - len(orders))):
                orders.append(["HIRE"])
                money -= fib[min(hires_today + i, len(fib) - 1)]

        # BUY_ANIMAL — identico ao v15
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

        # BUY_LAND — identico ao v15
        land_cost = LAND_COST.get(n_quads, 9999)
        if n_quads < 3 and day >= 7 and money > land_cost + 400:
            if n_quads == 1 and day >= 7:
                orders.append(["BUY_LAND"])
                money -= land_cost
            elif n_quads == 2 and day >= 11 and money > land_cost + 800:
                orders.append(["BUY_LAND"])
                money -= land_cost

        # Seeds — A.11: STRAWBERRY expansion (balanced, not excessive)
        if day <= 20 and len(orders) < MAX_MARKET_ORDERS:
            strw_have = seeds.get("STRAWBERRY", 0)
            if (strw_have < STRAWBERRY_TARGET
                    and days_left >= STRAWBERRY_MIN_DAYS_LEFT
                    and money > 600
                    and len(orders) < MAX_MARKET_ORDERS):
                need = min(STRAWBERRY_TARGET - strw_have, 2)
                if money > 100 * need + 400:
                    orders.append(["BUY_SEED", "STRAWBERRY", need])
                    money -= 100 * need

        if day <= 12 and len(orders) < MAX_MARKET_ORDERS:
            # MELON: cash rapido early — identico ao v15
            melon_have = seeds.get("MELON", 0)
            if melon_have < 4 and money > 400 and day <= 10:
                need = 4 - melon_have
                orders.append(["BUY_SEED", "MELON", need])
                money -= 80 * need
            # WHEAT seed: bulk buy only when truly low
            wheat_seeds = seeds.get("WHEAT", 0)
            if wheat_seeds < 5 and money > 200:
                buy_n = min(10 - wheat_seeds, 5)
                if money > 10 * buy_n + 200:
                    orders.append(["BUY_SEED", "WHEAT", buy_n])

        return orders[:MAX_MARKET_ORDERS]

    # -------------------------------------------------------------------------
    # _decide — v17.1 Cirurgia A: PLANT desacoplado de BUILD_PASTURE
    # -------------------------------------------------------------------------
    def _decide(self, tile, shed, seeds, day, inv, pos, hour, cows, sheep, empty_past):
        inv  = inv or {}
        x, y = pos if pos else (-1, -1)

        # A.11 — Endgame liquidation
        if day >= 28:
            if isinstance(tile, dict) and tile.get("kind") == "PASTURE" and tile.get("animal"):
                if tile.get("yield_units", 0) > 0:
                    return ["HARVEST"]
                return ["PASS"]
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                if tile.get("yield_units", 0) > 0:
                    return ["HARVEST"]
                return ["PASS"]
            return ["PASS"]
        
        if day >= 25 and tile is None:
            return ["PASS"]

        if tile is None:
            days_left      = 29 - day
            animal_in_shed = shed.get("COW", 0) + shed.get("SHEEP", 0)

            # Cirurgia A — regra de prioridade no tile vazio:
            #
            # CASO 1: animal aguardando no shed E sem pastagem vazia disponivel
            #   → BUILD_PASTURE imediato (desbloqueia PICKUP gate)
            #
            # CASO 2: animal no shed MAS ja existe pastagem vazia
            #   → PLANT (pasture ja disponivel; agente pode PICKUP + PLACE)
            #
            # CASO 3: sem animal aguardando
            #   → PLANT
            #
            # Em TODOS os casos que nao plantam: BUILD_PASTURE se ainda construindo

            # Caso 1: emergencia — destravar gate
            if animal_in_shed > 0 and empty_past == 0 and day <= 15:
                return ["BUILD_PASTURE"]

            # Casos 2 e 3: PLANT prioritario
            if hour <= 20:
                if seeds.get("STRAWBERRY", 0) > 0 and days_left >= STRAWBERRY_MIN_DAYS_LEFT:
                    return ["PLANT", "STRAWBERRY"]
                if seeds.get("MELON", 0) > 0 and day <= 12:
                    return ["PLANT", "MELON"]
                # WHEAT: suporte early — nao e cultura comercial primaria
                if seeds.get("WHEAT", 0) > 0 and day <= 8:
                    return ["PLANT", "WHEAT"]

            # BUILD_PASTURE para expansao normal (animal no shed, pastagem disponivel)
            if animal_in_shed > 0 and day <= 15:
                return ["BUILD_PASTURE"]

            return ["PASS"]

        if isinstance(tile, dict) and tile.get("kind") == "WEED":
            return ["DIG"]

        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            crop    = tile.get("crop", "")
            info    = CROPS.get(crop, {})
            age     = day - tile.get("planted_day", day)
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
            fed   = tile.get("fed_today")   or (pos and (x, y) in self.fed_this_day)
            cared = tile.get("cared_today") or (pos and (x, y) in self.cared_this_day)
            if not fed and (shed.get("WHEAT", 0) > 0 or inv.get("WHEAT", 0) > 0):
                return ["FEED"]
            if tile.get("fertilizer_available"):
                return ["COLLECT_FERTILIZER"]
            if not cared:
                return ["CARE"]
            if tile.get("yield_units", 0) > 0:
                return ["HARVEST"]
            return ["PASS"]

        return ["PASS"]

    # -------------------------------------------------------------------------
    # A.10 — CARE Timing Filter
    # -------------------------------------------------------------------------
    @staticmethod
    def _expected_days_to_yield(tile, day):
        animal = tile.get("animal")
        if animal == "COW": interval = 2
        elif animal == "SHEEP": interval = 3
        elif animal == "GOOSE": interval = 1
        else: return 99
        if tile.get("yield_units", 0) > 0:
            return 0
        return interval

    def _is_care_valuable(self, tile, day):
        return self._expected_days_to_yield(tile, day) < 3

    # -------------------------------------------------------------------------
    # _move_priorities — v17.1 Cirurgia B: emergency build + fallback
    # -------------------------------------------------------------------------
    def _move_priorities(self, shed, day, inv, empty_past=0):
        inv = inv or {}
        animal_in_shed = shed.get("COW", 0) + shed.get("SHEEP", 0)
        return [
            # 1. WATER — A.5: top priority (opponent waters 5.5x more, crop revenue = survival)
            lambda t, x, y: (isinstance(t, dict) and t.get("kind") == "PLANT"
                             and not t.get("watered_today")
                             and (x, y) not in self.watered_this_day),
            # 2. FEED
            lambda t, x, y: (isinstance(t, dict) and t.get("kind") == "PASTURE"
                             and t.get("animal") and not t.get("fed_today")
                             and (x, y) not in self.fed_this_day
                             and (shed.get("WHEAT", 0) > 0 or inv.get("WHEAT", 0) > 0)),
            # 3. CARE — A.10: only if expected days to yield < 3 (~57 steps)
            lambda t, x, y: (isinstance(t, dict) and t.get("kind") == "PASTURE"
                             and t.get("animal") and not t.get("cared_today")
                             and (x, y) not in self.cared_this_day
                             and self._is_care_valuable(t, day)),
            # 4. HARVEST
            lambda t, x, y: (isinstance(t, dict)
                             and ((t.get("kind") == "PASTURE" and t.get("yield_units", 0) > 0)
                                  or (t.get("kind") == "PLANT" and (
                                      t.get("yield_units", 0) > 0
                                      or (day - t.get("planted_day", day))
                                         >= CROPS.get(str(t.get("crop") or ""), {}).get("max", 99))))),
            # 5. PLACE animal (tem animal no inventario)
            lambda t, x, y: (isinstance(t, dict) and t.get("kind") == "PASTURE"
                             and t.get("animal") is None and inv
                             and any(inv.get(a, 0) > 0 for a in ("COW", "SHEEP"))),
            # 6. COLLECT_FERTILIZER — moved below PLACE (Seb: 352 vs our 1173 was excessive)
            lambda t, x, y: (isinstance(t, dict) and t.get("kind") == "PASTURE"
                             and t.get("fertilizer_available")),
            # 7. Cirurgia B — EMERGENCY BUILD PASTURE:
            #    animal aguardando no shed E sem pastagem vazia
            #    → worker vai a tile vazio para BUILD_PASTURE (destrava PICKUP gate)
            lambda t, x, y: (
                t is None
                and animal_in_shed > 0
                and empty_past == 0
                and day <= 15
            ),
            # 8. Tile vazio generico (para PLANT via _decide)
            lambda t, x, y: t is None,
            # 9. WEED
            lambda t, x, y: isinstance(t, dict) and t.get("kind") == "WEED",
        ]

    # -------------------------------------------------------------------------
    # v17.2 — State Integrity Layer
    # -------------------------------------------------------------------------
    def _validate_action_preconditions(self, action, winv, tile, shed, seeds):
        if not action or action[0] == "PASS":
            return True
        
        op = action[0]
        if op == "FEED":
            return winv.get("WHEAT", 0) > 0 and isinstance(tile, dict) and "animal" in tile
        elif op == "PLACE":
            if len(action) < 2: return False
            return winv.get(action[1], 0) > 0 and isinstance(tile, dict) and "animal" not in tile
        elif op == "PLANT":
            if len(action) < 2: return False
            return seeds.get(action[1], 0) > 0 and tile is None
        elif op == "WATER":
            return isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today")
        elif op == "CARE":
            return isinstance(tile, dict) and "animal" in tile and not tile.get("cared_today")
        elif op == "HARVEST":
            return isinstance(tile, dict) and tile.get("yield_units", 0) > 0
        elif op == "COLLECT_FERTILIZER":
            return isinstance(tile, dict) and "animal" in tile and tile.get("fertilizer_available")
        elif op == "PICKUP":
            if len(action) < 2: return False
            return shed.get(action[1], 0) > 0
            
        return True

    # -------------------------------------------------------------------------
    # Entry point
    # -------------------------------------------------------------------------
    def __call__(self, obs):
        if not isinstance(obs, dict):
            return {"farmer": ["PASS"], "hands": [], "market": []}
        player = obs.get("player", 0)
        farms  = obs.get("farms", [])
        if not isinstance(farms, list) or player >= len(farms):
            return {"farmer": ["PASS"], "hands": [], "market": []}

        day = obs.get("day", 0)

        if self.opening.is_active(day):
            result = self.opening.execute(obs)
            if result is not None:
                return result

        farm        = farms[player] or {}
        private     = obs.get("private", {}) or {}
        shed        = private.get("shed",   {}) or {}
        seeds       = private.get("seeds",  {}) or {}
        inventories = private.get("inventories", [])
        hour        = obs.get("hour", 0)

        if day != self.last_day:
            self.last_day         = day
            self.watered_this_day = set()
            self.fed_this_day     = set()
            self.cared_this_day   = set()

        cows, sheep, pastures, empty_past = self._count_animals(farm)
        tasks  = self._scan(farm, day)
        market = self._market(obs, tasks, cows, sheep, pastures, empty_past)
        assigned = {pos for pos in self.worker_targets.values()}

        def worker_act(worker_id, wpos, winv):
            x, y    = wpos
            tile    = self._tile_at(farm, (x, y))
            winv    = winv or {}
            inv_sum = sum(winv.values())

            # State Integrity Layer: Assinatura de estado + Circuit Breaker
            state_sig = f"{tile.get('kind', 'None')}-{tile.get('yield_units', 0)}-{tile.get('fed_today', False)}" if isinstance(tile, dict) else "None"
            
            def safe_return(intent):
                if not intent or intent[0] == "PASS" or intent[0] in ("NORTH", "SOUTH", "EAST", "WEST", "DROP"):
                    return intent
                if not self._validate_action_preconditions(intent, winv, tile, shed, seeds):
                    self.telemetry["invalid_action_intercepted"] += 1
                    key = f"{intent[0].lower()}_precondition_fail"
                    if key in self.telemetry:
                        self.telemetry[key] += 1
                    return None
                
                last_intent, last_target, last_sig, count = self.worker_history.get(worker_id, (None, None, None, 0))
                if intent == last_intent and wpos == last_target and state_sig == last_sig:
                    count += 1
                else:
                    count = 1
                
                if count > self.telemetry["max_consecutive_same_intent"]:
                    self.telemetry["max_consecutive_same_intent"] = count

                self.worker_history[worker_id] = (intent, wpos, state_sig, count)
                if count >= 3:
                    self.telemetry["circuit_breaker_triggered"] += 1
                    self.telemetry["replan_count"] += 1
                    return None # Circuit breaker: abandona e replaneja
                return intent

            def release_target():
                if worker_id in self.worker_targets:
                    tx, ty = self.worker_targets.pop(worker_id)
                    self.worker_failures.pop(worker_id, None)
                    if (tx, ty) in assigned:
                        assigned.remove((tx, ty))
                    self.telemetry["target_releases"] += 1
                    self.telemetry["target_changes"] += 1

            if inv_sum > 5 and self._is_shed_adj((x, y)):
                release_target()
                return ["DROP"]
            if inv_sum > 8:
                release_target()
                targets = [(4, 4), (5, 4), (4, 5), (5, 5)]
                best    = min(targets, key=lambda t: abs(t[0] - x) + abs(t[1] - y))
                if best != (x, y):
                    tx, ty = best
                    if ty < y: return ["NORTH"]
                    if ty > y: return ["SOUTH"]
                    if tx < x: return ["WEST"]
                    if tx > x: return ["EAST"]

            action = self._decide(tile, shed, seeds, day, winv, wpos, hour,
                                  cows, sheep, empty_past)
            valid_action = safe_return(action)
            if valid_action and valid_action[0] != "PASS":
                if   valid_action[0] == "WATER": self.watered_this_day.add((x, y))
                elif valid_action[0] == "FEED":  self.fed_this_day.add((x, y))
                elif valid_action[0] == "CARE":  self.cared_this_day.add((x, y))
                return valid_action

            if self._is_shed_adj((x, y)):
                for a in ("COW", "SHEEP"):
                    # MUDANCA 4: apenas PICKUP se ha pastagem vazia disponivel
                    if shed.get(a, 0) > 0 and inv_sum == 0 and empty_past > 0:
                        pickup = safe_return(["PICKUP", a, 1])
                        if pickup: return pickup
                if shed.get("WHEAT", 0) > 0 and winv.get("WHEAT", 0) == 0 and tasks["feed"]:
                    pickup = safe_return(["PICKUP", "WHEAT", min(3, shed["WHEAT"])])
                    if pickup: return pickup
                if inv_sum > 2:
                    release_target()
                    return ["DROP"]

            def is_target_valid(tx, ty):
                target_tile = self._tile_at(farm, (tx, ty))
                if target_tile == "LOCKED": return False
                for cond in self._move_priorities(shed, day, winv, empty_past=empty_past):
                    if cond(target_tile, tx, ty):
                        return True
                return False

            if worker_id in self.worker_targets:
                tx, ty = self.worker_targets[worker_id]
                if not is_target_valid(tx, ty):
                    del self.worker_targets[worker_id]
                    self.worker_failures.pop(worker_id, None)
                    if (tx, ty) in assigned:
                        assigned.remove((tx, ty))
                    self.telemetry["target_releases"] += 1
                    self.telemetry["target_changes"] += 1
                    last_intent_data = self.worker_history.get(worker_id)
                    last_intent = last_intent_data[0] if last_intent_data else None
                    if last_intent and last_intent[0] in ["HARVEST", "PLANT", "WATER", "FEED", "CARE", "PLACE", "COLLECT_FERTILIZER", "BUILD_PASTURE"]:
                        self.telemetry["claims_released_after_productive_action"] += 1
                    elif (x, y) == (tx, ty):
                        self.telemetry["claims_released_on_arrival"] += 1
                    else:
                        self.telemetry["claims_released_due_to_invalid_target"] += 1
                else:
                    if (tx, ty) in assigned:
                        assigned.remove((tx, ty))
                    _, _, direction = self._bfs((x, y), lambda t, cx, cy: (cx, cy) == (tx, ty), farm, assigned)
                    assigned.add((tx, ty))
                    
                    if direction:
                        self.worker_failures[worker_id] = 0
                        self.telemetry["target_persistence_turns"] += 1
                        return [direction]
                    else:
                        fails = self.worker_failures.get(worker_id, 0) + 1
                        self.worker_failures[worker_id] = fails
                        if fails > 3:
                            del self.worker_targets[worker_id]
                            del self.worker_failures[worker_id]
                            assigned.remove((tx, ty))
                            self.telemetry["target_releases"] += 1
                            self.telemetry["target_changes"] += 1
                            self.telemetry["claims_released_due_to_unreachable_target"] += 1
                        else:
                            return ["PASS"]

            for cond in self._move_priorities(shed, day, winv, empty_past=empty_past):
                tx, ty, direction = self._bfs((x, y), cond, farm, assigned)
                if direction:
                    self.worker_targets[worker_id] = (tx, ty)
                    self.telemetry["target_claims"] += 1
                    assigned.add((tx, ty))
                    return [direction]

            return ["PASS"]

        farmer_inv    = inventories[0] if inventories else {}
        farmer_action = worker_act(0, farm.get("farmer", [0, 0]), farmer_inv)

        hands_actions = []
        for i, hpos in enumerate(farm.get("hands", [])):
            h_inv = inventories[i + 1] if i + 1 < len(inventories) else {}
            hands_actions.append(worker_act(i + 1, hpos, h_inv))

        return {"farmer": farmer_action, "hands": hands_actions, "market": market}


# =============================================================================
# ENTRY POINTS
# =============================================================================
agent = KaggricultureAgentV17()


def agent_fn(observation, configuration=None):
    return agent(observation)


def main_agent(observation, configuration=None):
    return agent(observation)
