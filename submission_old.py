class KaggricultureAgentV3:
    def __init__(self):
        self.current_day = 0
        
    def __call__(self, observation):
        actions = []
        
        # 1. Controle de Turno e Dia
        turn = observation.get('step', 0)
        self.current_day = turn // 24
        
        # 2. Gestão de Mercado e Galpão (Shed)
        inventory = observation.get('inventory', {})
        total_items_in_shed = sum(inventory.values())
        is_shed_crowded = total_items_in_shed > 75
        
        # Liquidar excessos no mercado para evitar descarte por lotação
        for item, count in inventory.items():
            if count > 5:
                if is_shed_crowded or count > 20:
                    sell_amount = count if is_shed_crowded else (count // 2)
                    actions.append(f"SELL {item} {sell_amount}")
                    
        # Se tivermos bastante dinheiro e poucos animais/sementes, podemos comprar via mercado
        coins = observation.get('coins', 1000)
        if coins > 500 and 'WHEAT' not in inventory and len(actions) < 10:
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
                
            # Prioridade 1.1: Coletar produtos de animais ou alimentar animais, se houver na tile
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
                
            # Prioridade 3: Limpar mato (weed)
            if tile_state.get('has_weed'):
                actions.append("DIG")
                continue
                
            # Prioridade 4: Plantar caso o terreno esteja vazio
            if not tile_state.get('has_plant') and not tile_state.get('has_weed') and not tile_state.get('has_structure'):
                # Alternância estratégica: Trigo (para alimentar futuros animais) e Melão/Cenoura (lucro)
                if self.current_day % 3 == 0:
                    actions.append("PLANT MELON")
                elif self.current_day % 2 == 0:
                    actions.append("PLANT WHEAT")
                else:
                    actions.append("PLANT CARROT")
                continue
                
            # Caso padrão
            actions.append("PASS")
            
        return actions

# Instância da Versão 3
agent = KaggricultureAgentV3()

def agent_fn(observation, configuration=None):
    """
    Função principal exigida pela Kaggle.
    """
    return agent(observation)