class KaggricultureAgentV4:
    def __init__(self):
        self.current_day = 0
        
    def __call__(self, observation):
        actions = []
        
        # 1. Controle de Turno e Dia
        turn = observation.get('step', 0)
        self.current_day = turn // 24
        
        # 2. Gestão de Mercado, Caixa e Galpão (Shed)
        inventory = observation.get('inventory', {})
        coins = observation.get('coins', 1000)
        total_items_in_shed = sum(inventory.values())
        is_shed_crowded = total_items_in_shed > 75
        
        # Liquidar excessos no mercado para gerar caixa
        for item, count in inventory.items():
            if count > 5:
                if is_shed_crowded or count > 20:
                    sell_amount = count if is_shed_crowded else (count // 2)
                    actions.append(f"SELL {item} {sell_amount}")
                    
        # Compras estratégicas se tivermos saldo positivo e espaço nas ações do turno
        if coins > 400 and len(actions) < 8:
            # Se faltar trigo para os animais ou sementes básicas, compramos
            actions.append("BUY_SEED MELON 2")
            actions.append("BUY_SEED WHEAT 5")
        
        # 3. Ações na Fazenda para cada Peão/Fazendeiro
        farmers = observation.get('units', [])
        
        for farmer in farmers:
            f_pos = farmer.get('position')
            tile_state = observation.get('board', {}).get(str(f_pos), {})
            
            # Prioridade 1: Colher o que estiver pronto
            if tile_state.get('has_plant') and tile_state.get('is_ready_to_harvest'):
                actions.append("HARVEST")
                continue
                
            # Prioridade 1.1: Tratar dos animais (Alimentar / Coletar produtos)
            if tile_state.get('has_animal'):
                if not tile_state.get('fed_today'):
                    actions.append("FEED")
                    continue
                if tile_state.get('ready_to_produce'):
                    actions.append("HARVEST")
                    continue
                
            # Prioridade 2: Regar plantas que precisam de água hoje
            if tile_state.get('has_plant') and not tile_state.get('watered_today'):
                actions.append("WATER")
                continue
                
            # Prioridade 2.1: Usar fertilizante se disponível para dobrar o rendimento
            if tile_state.get('has_plant') and not tile_state.get('fertilized_recently') and inventory.get('FERTILIZER', 0) > 0:
                actions.append("FERTILIZE")
                continue
                
            # Prioridade 3: Limpar mato (weed)
            if tile_state.get('has_weed'):
                actions.append("DIG")
                continue
                
            # Prioridade 4: Plantar caso o terreno esteja vazio
            if not tile_state.get('has_plant') and not tile_state.get('has_weed') and not tile_state.get('has_structure'):
                if self.current_day % 3 == 0:
                    actions.append("PLANT MELON")
                elif self.current_day % 2 == 0:
                    actions.append("PLANT WHEAT")
                else:
                    actions.append("PLANT CARROT")
                continue
                
            actions.append("PASS")
            
        return actions

# Instância da Versão 4
agent = KaggricultureAgentV4()

def agent_fn(observation, configuration=None):
    return agent(observation)