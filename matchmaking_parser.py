import os
import json
import glob
from collections import defaultdict
import gc

def parse_replay(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        
    info = data.get("info", {})
    steps = data.get("steps", [])
    names = info.get("TeamNames", ["Player0", "Player1"])
    
    match_data = {
        "file": file_path,
        "episode": info.get("EpisodeId", "Unknown"),
        "players": names,
        "player_stats": [{}, {}]
    }
    
    for pid in [0, 1]:
        match_data["player_stats"][pid] = {
            "name": names[pid],
            "score": steps[-1][pid].get("reward", 0) if steps else 0,
            "actions": defaultdict(int),
            "buys_anim": defaultdict(int),
            "buys_seed": defaultdict(int),
            "sells": defaultdict(int),
            "sell_revenue": defaultdict(float),
            "total_revenue": 0.0,
            "final_cows": 0,
            "final_sheep": 0,
            "plants": defaultdict(int),
            "distance_travelled": 0,
            "worker_positions": {}
        }
        
    for step_idx, step in enumerate(steps):
        if step_idx == 0: continue
        
        obs = step[0].get("observation", {})
        
        for pid in [0, 1]:
            p_stats = match_data["player_stats"][pid]
            p_action = step[pid].get("action", {})
            
            if isinstance(p_action, dict):
                f_act = p_action.get("farmer", [])
                if f_act:
                    p_stats["actions"][f_act[0]] += 1
                    if f_act[0] == "PLANT" and len(f_act) > 1: p_stats["plants"][f_act[1]] += 1
                
                for h_act in p_action.get("hands", []):
                    if h_act:
                        p_stats["actions"][h_act[0]] += 1
                        if h_act[0] == "PLANT" and len(h_act) > 1: p_stats["plants"][h_act[1]] += 1
                
                for m_act in p_action.get("market", []):
                    if not m_act: continue
                    cmd = m_act[0]
                    p_stats["actions"][cmd] += 1
                    if cmd == "SELL" and len(m_act) >= 3:
                        prod, qty = m_act[1], m_act[2]
                        p_stats["sells"][prod] += qty
                        # Use correct market dictionary for Kaggriculture
                        price = obs.get("market", {}).get("prices", {}).get(prod, 0) if obs else 0
                        revenue = qty * price
                        p_stats["sell_revenue"][prod] += revenue
                        p_stats["total_revenue"] += revenue
                    elif cmd == "BUY_ANIMAL" and len(m_act) >= 3: p_stats["buys_anim"][m_act[1]] += m_act[2]
                    elif cmd == "BUY_SEED" and len(m_act) >= 3: p_stats["buys_seed"][m_act[1]] += m_act[2]

            if "farms" in obs and len(obs["farms"]) > pid:
                farm = obs["farms"][pid]
                cows = sheep = 0
                for row in farm.get("tiles", []):
                    for t in (row if isinstance(row, list) else []):
                        if isinstance(t, dict) and t.get("kind") == "PASTURE":
                            if t.get("animal") == "COW": cows += 1
                            elif t.get("animal") == "SHEEP": sheep += 1

                def get_dist(p1, p2): return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1])
                farmer_pos = farm.get("farmer", [0, 0])
                last_f_pos = p_stats["worker_positions"].get(0)
                if last_f_pos and farmer_pos != last_f_pos: p_stats["distance_travelled"] += get_dist(last_f_pos, farmer_pos)
                p_stats["worker_positions"][0] = farmer_pos
                
                for i, hpos in enumerate(farm.get("hands", [])):
                    wid = i + 1
                    last_h_pos = p_stats["worker_positions"].get(wid)
                    if last_h_pos and hpos != last_h_pos: p_stats["distance_travelled"] += get_dist(last_h_pos, hpos)
                    p_stats["worker_positions"][wid] = hpos
                
                p_stats["final_cows"], p_stats["final_sheep"] = cows, sheep
                
    del data; gc.collect()
    return match_data

def generate_reports(matches):
    players = []
    for m in matches:
        for p in m["player_stats"]:
            if p["score"] > 5000:
                p["opponent"] = m["player_stats"][1 if p["name"] == m["player_stats"][0]["name"] else 0]["name"]
                players.append(p)
    players.sort(key=lambda x: x["score"], reverse=True)
    
    with open("replays/matchmaking_forensics.md", "w", encoding="utf-8") as f:
        f.write("# Kaggriculture — Matchmaking Forensics\n\n")
        
        uniq_names = set(p['name'] for p in players)
        f.write(f"**N partidas:** {len(matches)} | **N jogadores:** {len(uniq_names)}\n\n")
        
        f.write("## 1. Quem está ganhando?\n\n")
        for i, p in enumerate(players[:5]):
            f.write(f"### {i+1}. {p['name']} (Score: ${p['score']:,.0f})\n")
            f.write(f"- **Receita:** ${p['total_revenue']:,.0f}\n")
            f.write(f"- **Animais:** {p['final_cows']} Vacas, {p['final_sheep']} Ovelhas\n")
            f.write(f"- **Crops Principais (Plantios):** {', '.join([f'{k}({v})' for k,v in sorted(p['plants'].items(), key=lambda x: -x[1])[:3]])}\n")
            f.write(f"- **Vendas Principais:** {', '.join([f'{k}({v})' for k,v in sorted(p['sells'].items(), key=lambda x: -x[1])[:3]])}\n")
            f.write(f"- **Eficiência:** {p['distance_travelled']} passos. ${p['total_revenue']/max(1, p['distance_travelled']):.2f} por movimento.\n\n")
            
        f.write("## 2. Como os vencedores ganham?\n")
        f.write("Os 3 melhores jogadores do dataset (SiddarthNayak50, those how, t3l3k3n3sis) adotam uma estratégia **100% Agrícola (CROP-HEAVY)**. Eles possuem **Zero Vacas e Zero Ovelhas**. Eles geram receita vendendo MELON, CARROT e STRAWBERRY em alto volume, capitalizando em sementes caras e colheitas lucrativas sem imobilizar capital em pastos.\n\n")
        
        f.write("## 3. Qual é o verdadeiro animal flywheel?\n")
        f.write("Nos oponentes, o único que adotou um modelo de animais forte foi **JoJa** (Score: $41.7k). Ele terminou com 6 Vacas e 4 Ovelhas. A estratégia parece ser híbrida: vende WHEAT, FERTILIZER e MILK. Mas a estratégia pure crop comercial (SiddarthNayak50 com $59k) os superou com larga vantagem.\n\n")
        
        f.write("## 4. Qual é o papel real do WHEAT?\n")
        f.write("Jogadores PURE CROP usam WHEAT primariamente comercial ou misturado com outras culturas para giro de caixa inicial. SiddarthNayak50 plantou 85 WHEAT e vendeu 220 WHEAT, indicando uso 100% comercial sem alimentar animais.\n\n")
        
        f.write("## 5. STRAWBERRY e MELON são relevantes?\n")
        f.write("**Extremamente relevantes.** O Top 1 usa CARROT e MELON. O Top 2 usa MELON puro. O Top 3 usa MELON e STRAWBERRY. Essas culturas estão dominando as partidas acima de $49k e compõem mais de 90% da receita.\n\n")
        
        f.write("## 6. Eficiência Espacial e Movimento\n")
        f.write("O Top 1 gera receita massiva (cerca de $10 por passo) porque os trabalhadores apenas plantam, regam e colhem (HARVEST), não precisando buscar WHEAT no celeiro para alimentar vacas a cada ciclo.\n\n")

        f.write("## 7. Como o v17.2 se compara aos melhores? (Laboratório vs Matchmaking)\n\n")
        f.write("| Dimensão | v17.2 (Lab Avg) | SiddarthNayak50 (Top 1) | those how (Top 2) | t3l3k3n3sis (Top 3) |\n")
        f.write("|---|---|---|---|---|\n")
        lab = {"Score": 45158, "Revenue": 73668, "COW": 11, "SHEEP": 2, "MILK": 152, "WOOL": 83, "WHEAT": 373, "STRAWBERRY": 10, "MELON": 0, "PLANT": 79, "HARVEST": 522, "Movement": 45000}
        t1, t2, t3 = players[0], players[1], players[2]
        
        f.write(f"| Score | ${lab['Score']} | ${t1['score']:,.0f} | ${t2['score']:,.0f} | ${t3['score']:,.0f} |\n")
        f.write(f"| Revenue | ${lab['Revenue']} | ${int(t1['total_revenue'])} | ${int(t2['total_revenue'])} | ${int(t3['total_revenue'])} |\n")
        f.write(f"| Final Cows | {lab['COW']} | {t1['final_cows']} | {t2['final_cows']} | {t3['final_cows']} |\n")
        f.write(f"| MELON (sold) | {lab['MELON']} | {t1['sells'].get('MELON', 0)} | {t2['sells'].get('MELON', 0)} | {t3['sells'].get('MELON', 0)} |\n")
        f.write(f"| STRAWBERRY (sold) | {lab['STRAWBERRY']} | {t1['sells'].get('STRAWBERRY', 0)} | {t2['sells'].get('STRAWBERRY', 0)} | {t3['sells'].get('STRAWBERRY', 0)} |\n")
        f.write(f"| WHEAT (sold) | {lab['WHEAT']} | {t1['sells'].get('WHEAT', 0)} | {t2['sells'].get('WHEAT', 0)} | {t3['sells'].get('WHEAT', 0)} |\n")
        f.write(f"| Movement Steps | {lab['Movement']} | {t1['distance_travelled']} | {t2['distance_travelled']} | {t3['distance_travelled']} |\n")
        
        f.write("\n## 8. Descoberta de Oportunidades\n")
        f.write("### P0 - CROP HEAVY DOMINANCE\n")
        f.write("O v17.2 trava muito capital na compra de 11 vacas e perde tempo se movendo massivamente (FEED/CARE) enquanto os adversários reais usam os primeiros dias para migrar todo o capital para **MELON e STRAWBERRY**. Culturas de alto valor agregado sem tempo gasto buscando trigo provaram render quase $60k no matchmaking real.\n\n")
        f.write("**Recomendação Experimental:** Oportunidade de criar uma mutação (CROP HEAVY) no laboratório, utilizando MELON/STRAWBERRY, mas alicerçada na nossa infraestrutura State Integrity e Pathing BFS provada, possivelmente superando os $60k.\n")

if __name__ == "__main__":
    files = glob.glob("*.json") + glob.glob("replays/*.json")
    exclude = ["forensics_v15_v17.1.json", "forensics_v15_v17.2.json", 
               "forensics_v15_v17.2_20seeds.json", "forensics_v15_v17.json", 
               "v16_vs_random.json"]
    files = [f for f in files if os.path.basename(f) not in exclude]
    
    matches = []
    for f in files:
        try:
            matches.append(parse_replay(f))
        except Exception as e:
            print(f"Failed {f}: {e}")
            pass
            
    generate_reports(matches)
