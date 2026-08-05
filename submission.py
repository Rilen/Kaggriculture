"""
Kaggriculture Autonomous AI Agent — Versão 7 (v7)

Reescrita completa utilizando o schema oficial de observação da Kaggriculture
(documentado em AGENTS.md / README.md da competição).

Schema da observacao (campos usados):
  obs["player"]                       -> 0 ou 1
  obs["step"], obs["day"], obs["hour"]
  obs["farms"][player]["money"]       -> saldo (coins) — vence quem tem mais
  obs["farms"][player]["tiles"][y][x] -> None | "LOCKED" | dict(PLANT/WEED/COOP/PASTURE)
  obs["farms"][player]["farmer"]      -> [x, y]
  obs["farms"][player]["hands"]       -> [[x, y], ...]
  obs["farms"][player]["unlocked_quadrants"]
  obs["private"]["shed"]             -> {item: count}  (produzido + animais + fertilizer)
  obs["private"]["seeds"]             -> {crop: count}  (consumido por PLANT)
  obs["private"]["inventories"]       -> [farmer_inv, hand1_inv, ...]
  obs["market"]["prices"]             -> {product: preco_venda atual}
  obs["town"]["unlocked_shops"]

Formato da acao retornada:
  {"farmer": [op, ...args], "hands": [[op, ...], ...], "market": [[op, ...], ...]}

Estrategia (v7):
  - Plantar culturas de alto valor (prioridade MELON > STRAWBERRY > TOMATO
    > CARROT > WHEAT) respeitando disponibilidade de sementes.
  - Regar todo dia (janela de bonus).
  - Fertilizar culturas de alto valor (dobra o bonus de rega p/ 3 dias).
  - Colher assim que a planta atinge first_yield_day (release p/ plantio novo)
    ou aguardar max_yield_day p/ maximizar yield (tradeoff simples: colhe no max).
  - Limpar mato (DIG) para liberar espaco.
  - Manter estoque de sementes e trigo (compra se faltar).
  - Vender produtos colhidos no mercado, respeitando o limite de ordens/turno.

A apresentacao final expoe:
  - agent(obs)            -> esperado pela Kaggle (schema novo)
  - agent_fn(obs, config) -> alias de compatibilidade (aceito historicamente)
"""

# ----------------------------- Constantes de culturas -----------------------
# first_yield_day, max_yield_day (colheita ideal), seed_cost, base_price
CROPS = {
    "WHEAT":      {"first": 2,  "max": 4,  "seed_cost": 10,  "price": 25},
    "CARROT":     {"first": 2,  "max": 3,  "seed_cost": 20,  "price": 35},
    "TOMATO":     {"first": 8,  "max": 11, "seed_cost": 50,  "price": 60},
    "STRAWBERRY": {"first": 10, "max": 16, "seed_cost": 100, "price": 120},
    "MELON":      {"first": 10, "max": 10, "seed_cost": 80,  "price": 250},
}

# Ordem de preferencia de plantio por valor (se sementes disponiveis).
PLANT_PRIORITY = ["MELON", "STRAWBERRY", "TOMATO", "CARROT", "WHEAT"]

# Animais — produzem continuamente; valor alto no longo prazo.
ANIMALS = {
    "GOOSE": {"buy_cost": 300, "needs": "COOP",    "product": "EGG",  "price": 50},
    "COW":   {"buy_cost": 400, "needs": "PASTURE", "product": "MILK", "price": 160},
    "SHEEP": {"buy_cost": 500, "needs": "PASTURE", "product": "WOOL", "price": 200},
}

# Limite de ordens de mercado por turno (default do ambiente).
MAX_MARKET_ORDERS = 10

# Limite suave do shed para acionar vendas preventivas.
SHED_SOFT_CAP = 80


class KaggricultureAgentV7:
    def __init__(self):
        self.last_day = -1

    # ----- helpers --------------------------------------------------------
    @staticmethod
    def _tile_at(farm, pos):
        """Retorna o tile na posicao [x, y] ou None se posicao invalida."""
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
        """Tile plantavel: None (vazio desbloqueado)."""
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

    # ----- logica principal ----------------------------------------------
    def __call__(self, obs):
        if not isinstance(obs, dict):
            return {"farmer": ["PASS"], "hands": [], "market": []}

        player = obs.get("player", 0)
        farms = obs.get("farms", [])
        if not isinstance(farms, list) or player >= len(farms):
            return {"farmer": ["PASS"], "hands": [], "market": []}

        farm = farms[player] or {}
        private = obs.get("private", {}) or {}
        market = obs.get("market", {}) or {}
        day = obs.get("day", 0)
        step = obs.get("step", 0)

        # Reset de flags no inicio do dia (nao usado para controle, mas mantemos
        # last_day para possivel logica futura de scheduling).
        if day != self.last_day:
            self.last_day = day

        shed = private.get("shed", {}) or {}
        seeds = private.get("seeds", {}) or {}
        money = farm.get("money", 0)
        prices = market.get("prices", {}) or {}

        # ---- 1. Mercado ---------------------------------------------------
        market_orders = self._build_market_orders(
            shed=shed, seeds=seeds, money=money, prices=prices, day=day
        )

        # ---- 2. Acao do fazendeiro principal ------------------------------
        farmer_pos = farm.get("farmer", [0, 0])
        tile = self._tile_at(farm, farmer_pos)

        main_action = self._decide_unit_action(
            tile=tile, seeds=seeds, shed=shed, day=day, prices=prices,
            farmer_pos=farmer_pos, farm=farm,
        )

        # ---- 3. Acoes dos farm hands (mesma logica) ------------------------
        hands_pos = farm.get("hands", []) or []
        hands_actions = []
        for hpos in hands_pos:
            htile = self._tile_at(farm, hpos)
            haction = self._decide_unit_action(
                tile=htile, seeds=seeds, shed=shed, day=day, prices=prices,
                farmer_pos=hpos, farm=farm,
            )
            hands_actions.append(haction)

        return {
            "farmer": main_action,
            "hands": hands_actions,
            "market": market_orders[:MAX_MARKET_ORDERS],
        }

    # ----- mercado -------------------------------------------------------
    def _build_market_orders(self, shed, seeds, money, prices, day):
        orders = []

        # (a) Vender produtos colhidos que estao no shed. Mantemos WHEAT e
        #     FERTILIZER como insumos operacionais (nao vendidos por defeito),
        #     exceto quando o shed esta lotado — nesse caso vende o excedente
        #     para evitar descarte no overflow (capacidade 100).
        total_shed = sum(shed.values()) if isinstance(shed, dict) else 0
        force_sell = total_shed > SHED_SOFT_CAP

        for item in sorted(shed.keys()):
            qty = shed.get(item, 0)
            if not isinstance(qty, (int, float)) or qty <= 0:
                continue

            if item == "WHEAT":
                # Reserva de trigo para alimentar animais. Se o shed nao estiver
                # lotado, guarda ate 20; se lotado, vende o excedente acima de 5.
                keep = 5 if force_sell else 20
                sell_qty = qty - keep
                if sell_qty > 0:
                    orders.append(["SELL", item, sell_qty])
                continue

            if item == "FERTILIZER":
                # Fertilizante e insumo; so vendemos quando o shed esta lotado
                # e o estoque passa de 5.
                if force_sell and qty > 5:
                    orders.append(["SELL", item, qty - 5])
                continue

            # Produtos normais (CARROT, MELON, EGG, MILK, WOOL, ...):
            # mantem um minimo de 3 unidades (buffer) a menos que lotado.
            keep = 0 if force_sell else 3
            sell_qty = qty - keep
            if sell_qty > 0:
                orders.append(["SELL", item, sell_qty])

        # (b) Reabastecimento de sementes — compra so o que falta, com orcamento
        #    controlado. Prioriza MELON, depois WHEAT (para vacas/aves), CARROT.
        seed_targets = {"MELON": 5, "WHEAT": 8, "CARROT": 6, "TOMATO": 3,
                         "STRAWBERRY": 3}
        for crop in ["MELON", "WHEAT", "CARROT", "TOMATO", "STRAWBERRY"]:
            have = seeds.get(crop, 0)
            target = seed_targets[crop]
            if have >= target or len(orders) >= MAX_MARKET_ORDERS:
                continue
            need = target - have
            cost = CROPS[crop]["seed_cost"] * need
            if money >= cost + 200:  # guarda margem de seguranca
                orders.append(["BUY_SEED", crop, need])
                money -= cost  # simulacao local de gasto p/ proximas ordens

        return orders

    # ----- acao por unidade (farmer ou hand) -----------------------------
    def _decide_unit_action(self, tile, seeds, shed, day, prices, farmer_pos, farm):
        # Nike Nacional: tile plantavel vazio? planta.
        if self._is_empty_unlocked(tile):
            return self._plant_action(seeds)

        # Weed -> limpa.
        if self._is_weed(tile):
            return ["DIG"]

        if self._is_plant(tile):
            crop = tile.get("crop")
            crop_info = CROPS.get(crop, {})
            first_day = crop_info.get("first", 2)
            max_day = crop_info.get("max", first_day)
            age = day - tile.get("planted_day", day)
            watered = bool(tile.get("watered_today"))
            fert_until = tile.get("fertilized_until_day", -1)
            can_fert = (crop in ("MELON", "STRAWBERRY", "TOMATO", "CARROT", "WHEAT")
                        and fert_until < day and shed.get("FERTILIZER", 0) > 0)
            is_ongoing = crop in ("TOMATO", "STRAWBERRY")

            # Colhe imediatamente ao atingir max_yield_day (lucro maximo).
            if age >= max_day:
                return ["HARVEST"]

            # Ja produz (passou do first_day):
            # - ongoing: colhe agora (continuara produzindo);
            # - one-time: rega/fertiliza para ganhar bonus, so colhe no max.
            if age >= first_day:
                if is_ongoing:
                    # Ongoing colhe assim que produz, ja tem yield_units.
                    return ["HARVEST"]
                # one-time: tenta melhorar o rendimento antes de colher.
                if not watered:
                    return ["WATER"]
                if can_fert and crop in ("MELON", "STRAWBERRY"):
                    return ["FERTILIZE"]
                # Ja regado (e fertilizado se possivel) e ainda falta um
                # dia ou mais p/ max -> espera. Se faltar <=1, ja colhemos.
                if max_day - age <= 1:
                    return ["HARVEST"]
                return ["PASS"]

            # Planta jovem (antes de first_day): regar todo dia e essencial.
            if not watered:
                return ["WATER"]
            # Fertiliza jovens de alto valor, se houver insumo.
            if can_fert and crop in ("MELON", "STRAWBERRY"):
                return ["FERTILIZE"]
            return ["PASS"]

        if self._is_animal_struct(tile):
            # Estrutura de animal: alimenta, cuida, colhe.
            if tile.get("animal") is None:
                # Sem animal — estrutura vazia. Nao ha acao alem de PASS.
                return ["PASS"]
            if not tile.get("fed_today") and shed.get("WHEAT", 0) > 0:
                return ["FEED"]
            if tile.get("fertilizer_available"):
                return ["COLLECT_FERTILIZER"]
            if not tile.get("cared_today"):
                return ["CARE"]
            # Animais produzem em intervalos: so colhe se houver yield_units.
            if tile.get("yield_units", 0) > 0:
                return ["HARVEST"]
            return ["PASS"]

        return ["PASS"]

    def _plant_action(self, seeds):
        """Escolhe a cultura de maior valor com sementes disponiveis."""
        for crop in PLANT_PRIORITY:
            if seeds.get(crop, 0) > 0:
                return ["PLANT", crop]
        # Sem sementes — PASS.
        return ["PASS"]


# ----------------------------- Instancia global -----------------------------
agent = KaggricultureAgentV7()


# ----------------------------- Funcoes publicas ----------------------------
def agent_fn(observation, configuration=None):
    """Alias de compatibilidade — algumas versoes da Kaggle chamam agent_fn."""
    return agent(observation)


def main_agent(observation, configuration=None):
    """Outro alias — algumas execucoes esperam main_agent."""
    return agent(observation)
