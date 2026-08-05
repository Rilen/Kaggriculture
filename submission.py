class KaggricultureAgentV6:
    """

    Agente autônomo V6 para a competição Kaggriculture.

    Melhorias em relação à V5:
      - Orçamento de ações por turno evita inundar o motor e bloquear rega/colheita.
      - Venda "curativa" de overflow: esvazia o shed de vez quando lotado.
      - Prioridade de culturas por valor: MELON > WHEAT > CARROT.
      - Reabastecimento de sementes só quando o inventário está baixo.
      - Fertilizante reservado apenas para culturas de alto valor (MELON).
      - Bug crítico corrigido: tile vazio ({}) tratado como plantável.
      - Maior robustez contra campos ausentes/None e tipos inválidos.
    """

    SHED_SAFE_CAP = 70
    SHED_CRITICAL = 80
    LOW_COINS_THRESHOLD = 300
    BUY_BUDGET_ACTIONS = 4

    CROP_VALUE = {
        "MELON": 3,
        "WHEAT": 2,
        "CARROT": 1,
    }
    HIGH_VALUE_CROPS = ("MELON",)

    def __init__(self):
        self.current_day = 0

    @staticmethod
    def _as_int(value, default=0):
        """Converte com segurança para int, tratando None/tipos inválidos."""
        try:
            if value is None:
                return default
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _as_dict(value):
        return value if isinstance(value, dict) else {}

    def _pertile_state(self, farmer, board):
        """
        Lê o estado do tile atual do fazendeiro.
        Retorna None quando o tile não existe no board (position inválida),
        e um dict (possivelmente vazio) quando o tile existe mas está sem info.
        """
        if not isinstance(farmer, dict):
            return None
        f_pos = farmer.get("position")
        if f_pos is None:
            return None
        key = str(f_pos)
        if key not in board:
            return None
        raw = board.get(key)
        return raw if isinstance(raw, dict) else {}

    def __call__(self, observation):
        if not isinstance(observation, dict):
            return []

        actions = []

        # ---- 1. Controle de Turno e Dia -------------------------------------
        turn = self._as_int(observation.get("step", 0))
        self.current_day = turn // 24

        # ---- 2. Gestão de Mercado, Caixa e Galpão ----------------------------
        inventory = self._as_dict(observation.get("inventory", {}))
        coins = self._as_int(observation.get("coins", 0))

        # Filtra chaves inválidas de inventário
        inv = {}
        for k, v in inventory.items():
            iv = self._as_int(v)
            if iv > 0:
                inv[k] = iv
        total_items_in_shed = sum(inv.values())
        shed_critical = total_items_in_shed > self.SHED_CRITICAL
        shed_crowded = total_items_in_shed > self.SHED_SAFE_CAP

        # Ocupação parcial: caso lotado, vender tudo de cada coluna para
        # liberar espaço; caso só passe do limite por coluna, vender metade.
        # Priorizamos vender o que vale menos primeiro para preservar
        # culturas de alto valor (MELON/WHEAT) no galpão.
        for item in sorted(inv.keys(), key=lambda x: self.CROP_VALUE.get(x, 0)):
            count = inv[item]
            if count <= 1:
                continue
            if item in ("FERTILIZER", "SEED_MELON", "SEED_WHEAT", "SEED_CARROT"):
                # Não liquidar inventário de insumos; são operacionais.
                continue
            if shed_critical:
                # Venda total: esvazia o shed o máximo possível.
                actions.append(f"SELL {item} {count}")
                inv[item] = 0
                if len(actions) >= 6:
                    break
            elif shed_crowded and count > 8:
                # Venda parcial: libera espaço sem liquidar todo o estoque.
                half = count // 2
                actions.append(f"SELL {item} {half}")
                inv[item] = count - half
            # Caso normal (shed saudável): não vende para preservar receita
            # e deixar a colheita acumular até um lote maior/venda estratégica.

        # ---- Reabastecimento de sementes / fertilizante --------------------
        # Orçamento de ações reservado para mercado evita saturar o turno.
        if coins > self.LOW_COINS_THRESHOLD:
            budget_left = self.BUY_BUDGET_ACTIONS
            seed_melon = inv.get("SEED_MELON", 0)
            seed_wheat = inv.get("SEED_WHEAT", 0)
            seed_carrot = inv.get("SEED_CARROT", 0)
            fertiz = inv.get("FERTILIZER", 0)

            if seed_melon < 3 and budget_left > 0:
                qty = min(3 - seed_melon, 2)
                actions.append(f"BUY_SEED MELON {qty}")
                budget_left -= 1
            if seed_wheat < 6 and budget_left > 0:
                qty = min(6 - seed_wheat, 5)
                actions.append(f"BUY_SEED WHEAT {qty}")
                budget_left -= 1
            if seed_carrot < 4 and budget_left > 0:
                qty = min(4 - seed_carrot, 4)
                actions.append(f"BUY_SEED CARROT {qty}")
                budget_left -= 1
            if fertiz < 2 and budget_left > 0 and coins > 600:
                actions.append("BUY FERTILIZER 2")

        # ---- 3. Ações na Fazenda para cada Peão/Fazendeiro ------------------
        farmers = observation.get("units", []) or []
        board = observation.get("board", {}) or {}
        board = board if isinstance(board, dict) else {}

        for farmer in farmers:
            if not isinstance(farmer, dict):
                actions.append("PASS")
                continue

            tile = self._pertile_state(farmer, board)
            if tile is None:
                # Tile fora do tabuleiro / sem info -> não há nada a fazer.
                actions.append("PASS")
                continue

            has_plant = bool(tile.get("has_plant"))
            has_animal = bool(tile.get("has_animal"))
            has_weed = bool(tile.get("has_weed"))
            has_structure = bool(tile.get("has_structure"))

            # P1: Colher planta pronta
            if has_plant and tile.get("is_ready_to_harvest"):
                actions.append("HARVEST")
                continue

            # P1.1: Tratar animais (alimentar antes de coletar)
            if has_animal:
                if not tile.get("fed_today"):
                    actions.append("FEED")
                    continue
                if tile.get("ready_to_produce"):
                    actions.append("HARVEST")
                    continue

            # P2: Regar plantas
            if has_plant and not tile.get("watered_today"):
                actions.append("WATER")
                continue

            # P2.1: Fertilizar SOMENTE culturas de alto valor
            if has_plant and not tile.get("fertilized_recently"):
                crop_type = tile.get("crop_type") or tile.get("plant_type")
                if crop_type in self.HIGH_VALUE_CROPS and inv.get("FERTILIZER", 0) > 0:
                    actions.append("FERTILIZE")
                    continue

            # P3: Limpar mato
            if has_weed:
                actions.append("DIG")
                continue

            # P4: Plantar em solo limpo e vazio (rotação por valor)
            if not has_plant and not has_weed and not has_structure:
                plant_action = self._choose_crop_to_plant(inv)
                if plant_action:
                    inv[plant_action["seed"]] = max(0, inv.get(plant_action["seed"], 0) - 1)
                    actions.append(plant_action["action"])
                    continue

            actions.append("PASS")

        return actions

    def _choose_crop_to_plant(self, inv):
        """
        Seleciona a cultura de maior valor disponível em sementes.
        Fallback na rotação dia%3 / dia%2 quando não há sementes em estoque.
        """
        # Preferência por valor: MELON > WHEAT > CARROT
        if inv.get("SEED_MELON", 0) > 0:
            return {"action": "PLANT MELON", "seed": "SEED_MELON"}
        if inv.get("SEED_WHEAT", 0) > 0:
            return {"action": "PLANT WHEAT", "seed": "SEED_WHEAT"}
        if inv.get("SEED_CARROT", 0) > 0:
            return {"action": "PLANT CARROT", "seed": "SEED_CARROT"}

        # Sem sementes no inventário: rotação baseada no dia
        if self.current_day % 3 == 0:
            return {"action": "PLANT MELON", "seed": "SEED_MELON"}
        elif self.current_day % 2 == 0:
            return {"action": "PLANT WHEAT", "seed": "SEED_WHEAT"}
        return {"action": "PLANT CARROT", "seed": "SEED_CARROT"}


agent = KaggricultureAgentV6()


def agent_fn(observation, configuration=None):
    return agent(observation)
