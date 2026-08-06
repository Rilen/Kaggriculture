"""
Kaggriculture Autonomous AI Agent — Version 12 (v12)

[v8]  BFS + Expansao + Pecuaria + Arbitragem Municipal
[v9]  Horizonte de Eventos + Espionagem do Oponente + Hour 23 Flush
[v10] Early Game Acelerado: BUY_LAND custo real, HIRE adaptativo,
      seed_targets escalados por quadrante, reserva de capital dinâmica
[v11] Fixes do Fórum: Anti-Weed (PASS em hora>=23), venda de
      FERTILIZER excedente (>10 unidades), Fixed Asset Meta acelerado
[v12] Deterministic Opening Book — "Tall Meta" (análise Top 1 Global, 128k+ pts):
      Autômato de Estado Finito para as primeiras horas do Dia 0.
      Premissa: NÃO comprar terra no early — adensar os 25 tiles iniciais.

      Fases do Opening Book (Dia 0):
        Hour 0-1  | GOLDEN_DUMP  : 5x HIRE + comprar animais/sementes em massa
        Hour 2    | SUPPLY_HACK  : BUY_PRODUCT WHEAT + PICKUP de animais do shed
        Hour 3-5  | INFRA_RUSH   : BUILD_PASTURE nos tiles vazios + PLACE animais
        Hour 6-9  | IGNITION     : FEED/CARE animais + PLANT MELON/WHEAT
        Hour >=10 | COMPLETE     : Transicao para engine dinamica v11
"""

from collections import deque

# =============================================================================
# CONSTANTES GLOBAIS
# =============================================================================
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
SHED_SOFT_CAP     = 75
SHED_HARD_CAP     = 100
LAND_COST: dict[int, int] = {1: 1000, 2: 2000, 3: 4000}


# =============================================================================
# OPENING BOOK -- Autoamato de Estado Finito para o Dia 0
# =============================================================================
class OpeningBook:
    """
    Deterministic Opening Book: "Golden Path" do Top 1 Global.

    Premissa "Tall": NAO comprar terra no early game -- o retorno de curto prazo
    dos quadrantes extras nao compensa o custo de oportunidade frente ao
    adensamento dos 25 tiles iniciais com animais e Meloes.

    A sequencia abaixo e executada deterministicamente por hora (Dia 0).
    Quando done=True, o agente devolve o controle ao engine dinamico v11.
    """

    # Mapa de fases: (nome, hora_limite_exclusiva)
    # A fase e ativa quando hour < hora_limite.
    _PHASE_MAP = [
        ("golden_dump", 2),   # hours 0-1
        ("supply_hack",  3),   # hour  2
        ("infra_rush",   6),   # hours 3-5
        ("ignition",    10),   # hours 6-9
    ]

    def __init__(self):
        self.done = False

    def is_active(self, day):
        """Retorna True enquanto o Opening Book deve controlar o turno (Dia 0)."""
        return day == 0 and not self.done

    # -- Helpers de Navegacao e Tiles --

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
        """Passo direcional greedy em direcao ao alvo (prioridade eixo Y)."""
        x, y   = pos
        tx, ty = target
        if ty < y: return ["NORTH"]
        if ty > y: return ["SOUTH"]
        if tx < x: return ["WEST"]
        if tx > x: return ["EAST"]
        return ["PASS"]

    def _find_empty_tile(self, tiles, nw_only=True):
        """Busca tile vazio (None) mais proximo do canto NW."""
        h    = len(tiles)
        w    = len(tiles[0]) if h > 0 else 0
        half = max(w, h) // 2
        ry   = range(half) if nw_only else range(h)
        rx   = range(half) if nw_only else range(w)
        for y in ry:
            row = tiles[y] if y < h else []
            for x in rx:
                if x < len(row) and row[x] is None:
                    return (x, y)
        if nw_only:
            return self._find_empty_tile(tiles, nw_only=False)
        return None

    @staticmethod
    def _get_phase(hour):
        for name, upper in OpeningBook._PHASE_MAP:
            if hour < upper:
                return name
        return "complete"

    # -- Ordens de Mercado por Fase --

    @staticmethod
    def _market_golden_dump():
        """
        Step 1 (hora 0-1): Golden Dump.
        5x HIRE  -- aproveitar custo Fibonacci no "fundo do poco" do Dia 0.
        BUY_ANIMAL SHEEP 2 + COW 2 -- montar o Fixed Asset Engine imediatamente.
        BUY_SEED WHEAT 7 + MELON 12 -- pipeline de plantio pronto para Hora 6.
        Total: 9 ordens (dentro do limite MAX_MARKET_ORDERS=10).
        """
        return [
            ["HIRE"],
            ["HIRE"],
            ["HIRE"],
            ["HIRE"],
            ["HIRE"],
            ["BUY_ANIMAL", "SHEEP", 2],
            ["BUY_ANIMAL", "COW",   2],
            ["BUY_SEED",   "WHEAT", 7],
            ["BUY_SEED",   "MELON", 12],
        ]

    @staticmethod
    def _market_supply_hack():
        """
        Step 2 (hora 2): Supply Hack.
        BUY_PRODUCT WHEAT 4 -- HOTFIX: 1 trigo por animal (2 COW + 2 SHEEP = 4).
        Trigo adulto direto do mercado para burlar o ciclo de crescimento.
        """
        return [["BUY_PRODUCT", "WHEAT", 4]]

    # -- Acao Individual de Worker por Fase --

    def _worker_action(self, phase, pos, inv, tiles, shed, seeds, worker_idx=0):
        """
        Determina a acao de UM worker no Opening Book.

        worker_idx:
          -1 = fazendeiro principal (farmer)
           0 = hand 0 (primeiro peao contratado)
           1 = hand 1 (segundo peao contratado)
           N >= 2 = peoes extras (sem tarefa critica no opening)
        """
        x, y  = pos
        tile  = self._tile_at(tiles, x, y)
        inv   = inv   or {}
        seeds = seeds or {}

        # ── SUPPLY_HACK (hora 2): rotas estritas por ator ──────────────────
        # Evita colisao de inventario: cada ator pega exatamente o que vai usar.
        #   Farmer (idx -1) : PICKUP COW  2  -> vai para INFRA_RUSH colocar vacas
        #   Hand 0 (idx  0) : PICKUP SHEEP 2 -> vai para INFRA_RUSH colocar ovelhas
        #   Hand 1 (idx  1) : PICKUP WHEAT 4 -> sera o alimentador no IGNITION
        #   Demais (idx >=2): PASS           -> sem tarefa critica nesta fase
        if phase == "supply_hack":
            if worker_idx == -1:
                if inv.get("COW", 0) == 0 and shed.get("COW", 0) > 0:
                    return ["PICKUP", "COW", 2]
            elif worker_idx == 0:
                if inv.get("SHEEP", 0) == 0 and shed.get("SHEEP", 0) > 0:
                    return ["PICKUP", "SHEEP", 2]
            elif worker_idx == 1:
                if inv.get("WHEAT", 0) == 0 and shed.get("WHEAT", 0) > 0:
                    return ["PICKUP", "WHEAT", 4]
            return ["PASS"]

        # ── INFRA_RUSH (horas 3-5): construir PASTUREs + alocar animais ────
        if phase == "infra_rush":
            # Validacao: apenas atores que carregam um animal COW/SHEEP fazem PLACE
            carrying = {a for a in ("COW", "SHEEP", "GOOSE") if inv.get(a, 0) > 0}

            # Esta sobre pastagem vazia -> alocar o animal que carrega
            if isinstance(tile, dict) and tile.get("kind") == "PASTURE" and not tile.get("animal"):
                for atype in ("COW", "SHEEP"):
                    if atype in carrying:           # guard: tem o animal no inv
                        return ["PLACE", atype]
                return ["PASS"]                    # sem animal -> aguarda

            # Esta carregando animal -> navegar ate pastagem vazia mais proxima
            if carrying:
                for ry, row in enumerate(tiles):
                    for rx, t in enumerate(row if isinstance(row, list) else []):
                        if isinstance(t, dict) and t.get("kind") == "PASTURE" and not t.get("animal"):
                            if (rx, ry) != (x, y):
                                return self._navigate(pos, (rx, ry))
                return ["PASS"]

            # Tile atual esta vazio -> construir pastagem
            if tile is None:
                return ["BUILD_PASTURE"]

            # Mover em direcao ao tile vazio mais proximo do NW
            target = self._find_empty_tile(tiles, nw_only=True)
            if target and target != (x, y):
                return self._navigate(pos, target)
            return ["PASS"]

        # ── IGNITION (horas 6-9): alimentar/cuidar animais + plantar ────────
        if phase == "ignition":
            # Prioridade 1: acao direta sobre tile atual (animal)
            if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE"):
                if tile.get("animal"):
                    # HOTFIX: FEED so e enviado se o ATOR tem WHEAT no inventario.
                    # Hand 1 (worker_idx==1) pegou WHEAT 4 no SUPPLY_HACK; os demais
                    # nao tem trigo e nao devem tentar alimentar (evita penalidade).
                    can_feed = inv.get("WHEAT", 0) > 0
                    if not tile.get("fed_today") and can_feed:
                        return ["FEED"]
                    if not tile.get("cared_today"):
                        return ["CARE"]
                    if tile.get("yield_units", 0) > 0:
                        return ["HARVEST"]

            # Prioridade 2: plantar na tile atual (MELON > WHEAT)
            if tile is None:
                for crop in ("MELON", "WHEAT"):
                    # HOTFIX: valida disponibilidade de sementes antes de PLANT.
                    if seeds.get(crop, 0) > 0:
                        return ["PLANT", crop]

            # Prioridade 3: navegar ate animal nao tratado
            # Para o Hand 1 (com trigo), prioriza animals nao alimentados.
            # Para os demais, prioriza animals nao cuidados (CARE).
            for ry, row in enumerate(tiles):
                for rx, t in enumerate(row if isinstance(row, list) else []):
                    if not (isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE") and t.get("animal")):
                        continue
                    needs_feed  = not t.get("fed_today")  and inv.get("WHEAT", 0) > 0
                    needs_care  = not t.get("cared_today")
                    if (needs_feed or needs_care) and (rx, ry) != (x, y):
                        return self._navigate(pos, (rx, ry))

            # Prioridade 4: navegar ate tile vazio para plantar (quadrante NW)
            # HOTFIX: so navega para plantar se houver semente disponivel.
            if any(seeds.get(c, 0) > 0 for c in ("MELON", "WHEAT")):
                target = self._find_empty_tile(tiles, nw_only=True)
                if target and target != (x, y):
                    return self._navigate(pos, target)

            return ["PASS"]

        return ["PASS"]

    # -- Entry Point Principal --

    def execute(self, obs):
        """
        Executa um step do Opening Book.
        Retorna dict {farmer, hands, market} ou None quando completo.
        None sinaliza ao agente para usar a engine dinamica.
        """
        hour  = obs.get("hour", 0)
        phase = self._get_phase(hour)

        if phase == "complete":
            self.done = True
            return None

        player  = obs.get("player", 0)
        farms   = obs.get("farms") or [{}]
        farm    = (farms[player] if player < len(farms) else {}) or {}
        private = obs.get("private") or {}
        shed    = private.get("shed")         or {}
        seeds   = private.get("seeds")        or {}
        invs    = private.get("inventories")  or []
        tiles   = farm.get("tiles")           or []

        # Ordens de mercado (apenas nas fases iniciais)
        if phase == "golden_dump":
            market = self._market_golden_dump()
        elif phase == "supply_hack":
            market = self._market_supply_hack()
        else:
            market = []

        # Acao do fazendeiro principal (worker_idx=-1 = rota exclusiva de COW)
        farmer_pos = farm.get("farmer") or [0, 0]
        farmer_inv = invs[0] if invs else {}
        farmer_act = self._worker_action(phase, farmer_pos, farmer_inv, tiles, shed, seeds,
                                         worker_idx=-1)

        # Acoes dos peoes contratados (worker_idx=i: 0=SHEEP, 1=WHEAT/feed, 2+=extras)
        hands_acts = []
        for i, hpos in enumerate(farm.get("hands") or []):
            h_inv = invs[i + 1] if i + 1 < len(invs) else {}
            hands_acts.append(
                self._worker_action(phase, hpos, h_inv, tiles, shed, seeds,
                                    worker_idx=i)
            )

        return {"farmer": farmer_act, "hands": hands_acts, "market": market}


# =============================================================================
# ENGINE DINAMICO -- Mid/Late Game (v11, com todos os hotfixes)
# =============================================================================
class KaggricultureAgentV12:
    """
    Agente principal v12.
    - Dia 0, hora < 10  -> OpeningBook (Golden Path deterministico)
    - Dia 0, hora >= 10 e demais dias -> Engine dinamica v11 com hotfixes:
        Anti-Weed Lock  : PASS em vez de PLANT se hour >= 23
        Fertilizer Sell : vender FERTILIZER excedente (manter <= 10 unidades)
        Fixed Asset Meta: BUILD_PASTURE acelerado (dia 5, sem exigir gansos)
    """

    def __init__(self):
        self.opening      = OpeningBook()
        self.last_day     = -1
        self.watered_this_day: set = set()
        self.fed_this_day: set     = set()
        self.price_history: dict   = {}
        self.animals_bought        = 0

    # -- Helpers estaticos --

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

    # -- BFS --

    def _bfs_nearest(self, start, condition, farm, exclude):
        sx, sy  = start
        tiles   = farm.get("tiles", [])
        board_h = len(tiles)
        board_w = len(tiles[0]) if board_h > 0 else 0
        if board_h == 0:
            return (None, None, None)

        queue   = deque()
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

    # -- Scan de Tarefas --

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
                    info = CROPS.get(crop if isinstance(crop, str) else "", {})
                    age  = day - tile.get("planted_day", day)
                    if (age >= info.get("max", 2)
                            or (crop in ("TOMATO", "STRAWBERRY")
                                and age >= info.get("first", 2)
                                and tile.get("yield_units", 0) > 0)):
                        tasks["harvest_ready"].append((x, y))
                    if not tile.get("watered_today") and (x, y) not in self.watered_this_day:
                        tasks["water_needed"].append((x, y))
                elif kind in ("COOP", "PASTURE"):
                    if tile.get("yield_units", 0) > 0:
                        tasks["harvest_ready"].append((x, y))
                    if tile.get("animal") and not tile.get("fed_today") and (x, y) not in self.fed_this_day:
                        tasks["feed_needed"].append((x, y))
        return tasks

    # -- Decisao de Acao por Tile --

    def _decide_tile_action(self, tile, shed, seeds, day, worker_inventory=None, pos=None, hour=0):
        if self._is_empty_unlocked(tile):
            # FIX v11: Semente plantada sem agua na mesma hora vira mato na madrugada.
            # Hora 23 nao tem mais turns no dia para regar -- bloqueia o plantio!
            if hour >= 23:
                return ["PASS"]
            return self._plant_action(seeds, day)

        if isinstance(tile, dict) and tile.get("kind") == "WEED":
            return ["DIG"]

        x, y = pos if pos else (-1, -1)

        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            crop      = tile.get("crop")
            crop_info = CROPS.get(crop if isinstance(crop, str) else "", {})
            first_day = crop_info.get("first", 2)
            max_day   = crop_info.get("max", first_day)
            age       = day - tile.get("planted_day", day)
            watered   = bool(tile.get("watered_today")) or (pos and (x, y) in self.watered_this_day)
            fert_until = tile.get("fertilized_until_day", -1)
            can_fert   = (crop in ("MELON", "STRAWBERRY") and fert_until < day and shed.get("FERTILIZER", 0) > 0)
            is_ongoing = crop in ("TOMATO", "STRAWBERRY")

            if age >= max_day:   return ["HARVEST"]
            if age >= first_day:
                if is_ongoing:   return ["HARVEST"]
                if not watered:  return ["WATER"]
                if can_fert:     return ["FERTILIZE"]
                if max_day - age <= 1: return ["HARVEST"]
                return ["PASS"]

            if not watered: return ["WATER"]
            if can_fert:    return ["FERTILIZE"]
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
            if tile.get("fertilizer_available"):       return ["COLLECT_FERTILIZER"]
            if not tile.get("cared_today"):            return ["CARE"]
            if tile.get("yield_units", 0) > 0:        return ["HARVEST"]
            return ["PASS"]

        return ["PASS"]

    # -- Prioridades de Movimento (BFS conditions) --

    def _build_move_priorities(self, shed, day, worker_inventory):
        return [
            lambda tile, x, y: (isinstance(tile, dict) and tile.get("kind") == "PLANT"
                                 and (x, y) not in self.watered_this_day
                                 and not tile.get("watered_today")),
            lambda tile, x, y: (isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE")
                                 and (x, y) not in self.fed_this_day
                                 and tile.get("animal") and not tile.get("fed_today")
                                 and shed.get("WHEAT", 0) > 0),
            lambda tile, x, y: ((isinstance(tile, dict) and tile.get("kind") == "PLANT"
                                  and (day - tile.get("planted_day", day)) >= CROPS.get(str(tile.get("crop") or ""), {}).get("max", 2))
                                 or (isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE", "PLANT")
                                     and tile.get("yield_units", 0) > 0)),
            lambda tile, x, y: (isinstance(tile, dict) and tile.get("kind") == "PLANT"
                                 and tile.get("crop") in ("MELON", "STRAWBERRY")
                                 and tile.get("fertilized_until_day", -1) < day
                                 and shed.get("FERTILIZER", 0) > 0),
            lambda tile, x, y: (isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE")
                                 and tile.get("fertilizer_available")),
            lambda tile, x, y: (isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE")
                                 and tile.get("animal") and not tile.get("cared_today")),
            lambda tile, x, y: (isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE")
                                 and tile.get("animal") is None and worker_inventory
                                 and any(qty > 0 and item in ANIMALS and ANIMALS[item]["needs"] == tile.get("kind")
                                         for item, qty in worker_inventory.items())),
            lambda tile, x, y: isinstance(tile, dict) and tile.get("kind") == "WEED",
            lambda tile, x, y: tile is None,
        ]

    # -- Prioridade de Construcao --

    def _get_build_priority(self, day, shed, farm):
        goose_count = sum(1 for row in farm.get("tiles", []) for tile in row
                          if isinstance(tile, dict) and tile.get("animal") == "GOOSE")
        cow_count   = sum(1 for row in farm.get("tiles", []) for tile in row
                          if isinstance(tile, dict) and tile.get("animal") == "COW")
        empty_coops = sum(1 for row in farm.get("tiles", []) for tile in row
                          if isinstance(tile, dict) and tile.get("kind") == "COOP"    and not tile.get("animal"))
        empty_past  = sum(1 for row in farm.get("tiles", []) for tile in row
                          if isinstance(tile, dict) and tile.get("kind") == "PASTURE" and not tile.get("animal"))

        if goose_count == 0 and empty_coops == 0 and day < 5:  return "BUILD_COOP"
        if goose_count < 2 and empty_coops == 0 and self.animals_bought > goose_count and day < 10:
            return "BUILD_COOP"

        # FIX v11 -- Fixed Asset Meta: PASTURE desde o dia 5, sem exigir gansos.
        # YARN_STORE garante demanda constante de WOOL -> sem risco de crash de preco.
        if cow_count == 0 and day >= 5 and shed.get("WHEAT", 0) > 10 and empty_past == 0:
            return "BUILD_PASTURE"
        return None

    # -- Ordens de Mercado (Mid/Late Game) --

    def _build_market_orders(self, obs, tasks):
        player  = obs.get("player", 0)
        farm    = obs.get("farms", [{}])[player]
        op_farm = obs.get("farms", [{}, {}])[1 - player]
        private = obs.get("private", {})
        day, hour, step = obs.get("day", 0), obs.get("hour", 0), obs.get("step", 0)
        shed    = private.get("shed",  {}) or {}
        seeds   = private.get("seeds", {}) or {}
        money   = farm.get("money", 0)
        prices  = obs.get("market", {}).get("prices", {}) or {}

        self._track_prices(step, prices)
        if day >= 27:
            return self._build_liquidation_orders(shed)

        n_quadrants = len(farm.get("unlocked_quadrants", []))
        land_cost   = LAND_COST.get(n_quadrants, 9999)

        orders: list[list] = []
        total_shed  = sum(shed.values())
        total_invs  = sum(sum(inv.values()) for inv in private.get("inventories", []) if inv)
        projected   = total_shed + total_invs
        panic_flush = (hour >= 22 and projected >= 95)
        force_sell  = panic_flush or (total_shed > SHED_SOFT_CAP)

        animal_count = sum(1 for row in farm.get("tiles", []) for tile in row
                           if isinstance(tile, dict) and tile.get("animal"))
        op_melons    = sum(1 for row in op_farm.get("tiles", []) for tile in row
                           if isinstance(tile, dict) and tile.get("crop") == "MELON")
        op_flooding  = op_melons > 8

        # Bloco de Vendas
        for item, qty in sorted(shed.items()):
            if qty <= 0 or item in ("GOOSE", "COW", "SHEEP"):
                continue

            if item == "MELON" and op_flooding:
                orders.append(["SELL", item, qty])
                continue

            if item == "WHEAT":
                keep = 2 if panic_flush else (5 if force_sell else max(5, animal_count * 3 + 5))
            elif item == "FERTILIZER":
                # FIX v11: Fertilizante E vendavel (bug de doc). Buffer = 10 unidades.
                keep = 0 if panic_flush else (5 if force_sell else min(qty, 10))
            else:
                keep = 0 if force_sell else 3

            sell_qty = qty - keep
            if sell_qty > 0:
                orders.append(["SELL", item, sell_qty])

        # BUY_LAND (prioridade alta, antes das sementes)
        # v12: NAO comprar terra durante o Opening Book (Tall Meta).
        # No mid/late game, so compra se tiver margem financeira confortavel.
        LAND_RESERVE = 600
        if day > 0 and n_quadrants < 4 and money > land_cost + LAND_RESERVE:
            orders.append(["BUY_LAND"])

        # HIRE adaptativo ao estagio do jogo
        urgent = (len(tasks.get("water_needed", []))
                  + len(tasks.get("feed_needed",   []))
                  + len(tasks.get("harvest_ready", [])))
        if day <= 5:
            hire_threshold, hire_reserve = 3, 200
        elif day <= 10:
            hire_threshold, hire_reserve = 6, 400
        else:
            hire_threshold, hire_reserve = 12, 500
        if urgent >= hire_threshold and money > hire_reserve and not farm.get("hands"):
            orders.append(["HIRE"])

        # Compra de Sementes
        valid_crops = self._get_valid_crops(day, op_flooding)
        if n_quadrants >= 3:
            seed_targets = {"MELON": 8, "WHEAT": 10, "CARROT": 6, "TOMATO": 4, "STRAWBERRY": 4}
        elif n_quadrants >= 2:
            seed_targets = {"MELON": 6, "WHEAT": 8,  "CARROT": 5, "TOMATO": 3, "STRAWBERRY": 3}
        else:
            seed_targets = {"MELON": 4, "WHEAT": 6,  "CARROT": 4, "TOMATO": 2, "STRAWBERRY": 2}

        pending_land = land_cost if n_quadrants < 4 else 0
        seed_reserve = max(200, pending_land // 2)

        for crop in PLANT_PRIORITY:
            if crop not in valid_crops:
                continue
            have = seeds.get(crop, 0)
            if have < seed_targets[crop] and len(orders) < MAX_MARKET_ORDERS:
                need = seed_targets[crop] - have
                cost = CROPS[crop]["seed_cost"] * need
                if money >= cost + seed_reserve:
                    orders.append(["BUY_SEED", crop, need])
                    money -= cost

        return orders[:MAX_MARKET_ORDERS]

    def _build_liquidation_orders(self, shed):
        return [
            ["SELL", item, qty]
            for item, qty in sorted(shed.items())
            if qty > 0 and item not in ("GOOSE", "COW", "SHEEP")
        ][:MAX_MARKET_ORDERS]

    def _track_prices(self, step, prices):
        for product, price in prices.items():
            if product not in self.price_history:
                self.price_history[product] = []
            self.price_history[product].append((step, price))
            if len(self.price_history[product]) > 10:
                self.price_history[product] = self.price_history[product][-10:]

    @staticmethod
    def _get_valid_crops(day, op_flooding_melon=False):
        crops = []
        if day <= 19 and not op_flooding_melon: crops.append("MELON")
        if day <= 18: crops.append("STRAWBERRY")
        if day <= 21: crops.append("TOMATO")
        if day <= 25: crops.append("WHEAT")
        if day <= 26: crops.append("CARROT")
        return crops

    def _plant_action(self, seeds, day):
        valid_crops = self._get_valid_crops(day)
        if day % 3 == 0 and seeds.get("MELON", 0) > 0 and "MELON" in valid_crops:
            return ["PLANT", "MELON"]
        if day % 2 == 0 and seeds.get("WHEAT", 0) > 0 and "WHEAT" in valid_crops:
            return ["PLANT", "WHEAT"]
        for crop in PLANT_PRIORITY:
            if seeds.get(crop, 0) > 0 and crop in valid_crops:
                return ["PLANT", crop]
        return ["PASS"]

    # -- Loop Principal --

    def __call__(self, obs):
        if not isinstance(obs, dict):
            return {"farmer": ["PASS"], "hands": [], "market": []}
        player = obs.get("player", 0)
        farms  = obs.get("farms", [])
        if not isinstance(farms, list) or player >= len(farms):
            return {"farmer": ["PASS"], "hands": [], "market": []}

        day = obs.get("day", 0)

        # Opening Book (Dia 0, horas 0-9)
        if self.opening.is_active(day):
            result = self.opening.execute(obs)
            if result is not None:
                return result
            # result == None -> fase COMPLETE, cair para engine dinamica

        # Engine Dinamica v11 (Mid/Late Game)
        farm        = farms[player] or {}
        private     = obs.get("private", {}) or {}
        shed        = private.get("shed",         {}) or {}
        seeds       = private.get("seeds",        {}) or {}
        inventories = private.get("inventories",  [])
        hour        = obs.get("hour", 0)

        if day != self.last_day:
            self.last_day         = day
            self.watered_this_day = set()
            self.fed_this_day     = set()

        tasks         = self._scan_tiles(farm, day)
        market_orders = self._build_market_orders(obs, tasks)
        assigned      = set()

        def get_worker_action(wpos, winv):
            x, y = wpos
            tile = self._tile_at(farm, (x, y))

            if self._is_empty_unlocked(tile):
                build_cmd = self._get_build_priority(day, shed, farm)
                if build_cmd:
                    return [build_cmd]
                # Passa hour para bloquear PLANT em hora 23 (FIX v11)
                action = self._decide_tile_action(tile, shed, seeds, day, winv, wpos, hour)
                if action and action[0] != "PASS":
                    return action

            if tile is not None and not self._is_empty_unlocked(tile):
                if self._is_animal_struct(tile) and tile.get("animal") is None and winv:
                    for item, qty in winv.items():
                        if qty > 0 and item in ANIMALS and ANIMALS[item]["needs"] == tile.get("kind"):
                            return ["PLACE", item]
                action = self._decide_tile_action(tile, shed, seeds, day, winv, wpos, hour)
                if action and action[0] != "PASS":
                    if action[0] == "WATER": self.watered_this_day.add((x, y))
                    elif action[0] == "FEED": self.fed_this_day.add((x, y))
                    return action

            if self._is_shed_adjacent((x, y)):
                for atype in ("GOOSE", "COW", "SHEEP"):
                    if shed.get(atype, 0) > 0 and (not winv or sum(winv.values()) == 0):
                        self.animals_bought += 1
                        return ["PICKUP", atype, 1]
                if winv and sum(winv.values()) > 5:
                    return ["DROP"]

            for condition in self._build_move_priorities(shed, day, winv):
                tx, ty, direction = self._bfs_nearest((x, y), condition, farm, assigned)
                if direction:
                    assigned.add((tx, ty))
                    return [direction]

            return ["PASS"]

        farmer_inv    = inventories[0] if inventories else {}
        farmer_action = get_worker_action(farm.get("farmer", [0, 0]), farmer_inv)

        hands_actions = []
        for i, hpos in enumerate(farm.get("hands", [])):
            h_inv = inventories[i + 1] if i + 1 < len(inventories) else {}
            hands_actions.append(get_worker_action(hpos, h_inv))

        return {"farmer": farmer_action, "hands": hands_actions, "market": market_orders}


# =============================================================================
# ENTRY POINTS (compatíveis com a arena Kaggle)
# =============================================================================
agent = KaggricultureAgentV12()
def agent_fn(observation, configuration=None):   return agent(observation)
def main_agent(observation, configuration=None): return agent(observation)