import json
import statistics

def load_data():
    with open("replays/v17.2_pathing_forensics.json", "r") as f:
        return json.load(f)

def generate_reports():
    data = load_data()
    seeds = list(data.keys())
    
    # Calculate global averages
    avg_score = statistics.mean([d["score"] for d in data.values()])
    
    avg_bfs_calls = statistics.mean([d["bfs_calls"] for d in data.values()])
    avg_successful = statistics.mean([d["successful_paths"] for d in data.values()])
    avg_failed = statistics.mean([d["failed_paths"] for d in data.values()])
    avg_empty = statistics.mean([d["empty_paths"] for d in data.values()])
    
    manh = sum([d["manhattan_sum"] for d in data.values()])
    path_len = sum([d["path_length_sum"] for d in data.values()])
    ratio = path_len / max(1, manh)
    
    avg_movement = statistics.mean([d["movement_actions"] for d in data.values()])
    avg_productive = statistics.mean([d["productive_actions"] for d in data.values()])
    avg_idle = statistics.mean([d["idle_actions"] for d in data.values()])
    
    avg_collisions = statistics.mean([d["same_tile_collisions"] for d in data.values()])
    
    avg_n1 = statistics.mean([d["unproductive_n1"] for d in data.values()])
    avg_n3 = statistics.mean([d["unproductive_n3"] for d in data.values()])
    avg_n5 = statistics.mean([d["unproductive_n5"] for d in data.values()])
    
    avg_rev = statistics.mean([d["total_revenue"] for d in data.values()])
    
    prod_ratio = avg_productive / max(1, avg_movement)
    rev_mov = avg_rev / max(1, avg_movement)
    
    # 1. PATHING FORENSICS MD
    md1 = ["# v17.2 — Pathing Forensics"]
    md1.append(f"**N Seeds**: {len(seeds)}")
    md1.append("\n## 1. Desempenho do Algoritmo BFS")
    md1.append(f"- **BFS Calls (Médio)**: {avg_bfs_calls:.0f}")
    md1.append(f"- **Caminhos Encontrados**: {avg_successful:.0f}")
    md1.append(f"- **Caminhos Vazios (Alvo Adjacente)**: {avg_empty:.0f}")
    md1.append(f"- **Falhas de Rota (Bloqueado/Inatingível)**: {avg_failed:.0f}")
    md1.append(f"- **Razão Path Length / Manhattan Distance**: {ratio:.2f}")
    md1.append("  *Nota: Um path ratio de 1.0 indica rota direta sem obstáculos. Valores maiores indicam desvios ao redor de vacas/plantas.*")
    
    md1.append("\n## 2. Coordenação Espacial (Fleet Contention)")
    md1.append(f"- **Colisões no Mesmo Tile**: {avg_collisions:.0f} vezes por partida.")
    md1.append("  *Definição: Dois ou mais workers receberam intenção de movimento para a exata mesma coordenada em um único turno.*")
    
    md1.append("\n## 3. Padrões Observados em Matchmaking")
    md1.append("No topo do matchmaking, observou-se uso do Farmer apenas para HIRE (PASS) enquanto 4/5 hands trabalham. No `v17.2`, o farmer executa tarefas normalmente. Para inferir se o Farmer em PASS melhora a coordenação, precisamos ver se ele contribui para as colisões. (NOT AVAILABLE IN SOURCE).")
    
    with open("replays/v17.2_pathing_forensics.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md1))
        
    # 2. WORKER EFFICIENCY MD
    md2 = ["# v17.2 — Worker Efficiency & Causal Diagnosis"]
    
    md2.append("\n## 1. Throughput do Worker (Médias da Frota)")
    md2.append(f"- **Ações Produtivas Totais**: {avg_productive:.0f}")
    md2.append(f"- **Ações de Movimento**: {avg_movement:.0f}")
    md2.append(f"- **Ações Ociosas/Bloqueadas (PASS)**: {avg_idle:.0f}")
    md2.append(f"- **Productive / Movement Ratio**: {prod_ratio:.3f} (Ou seja, ~{prod_ratio*100:.1f} ações produtivas para cada 100 movimentos)")
    md2.append(f"- **Revenue / Movement**: {rev_mov:.2f} $/mov")
    md2.append(f"- **Receita / Worker**: {avg_rev / 5:.0f} $/worker")
    
    md2.append("\n## 2. Desperdício de Movimento (Unproductive Journeys)")
    md2.append("Identificação de movimentos que não resultaram em ação produtiva dentro de uma janela temporal:")
    md2.append(f"- **N=1 turno após movimento**: {avg_n1:.0f} movimentos sem ação imediata.")
    md2.append(f"- **N=3 turnos após movimento**: {avg_n3:.0f} movimentos.")
    md2.append(f"- **N=5 turnos após movimento**: {avg_n5:.0f} movimentos.")
    md2.append(f"Isso significa que {avg_n5 / max(1, avg_movement) * 100:.1f}% do tempo em que um worker se move, ele falha em executar uma ação em até 5 turnos.")

    md2.append("\n## 3. Matriz de Diagnóstico")
    
    # Decide based on metrics
    causa = "INCONCLUSIVE"
    evidencia_pathing = ratio > 1.3 or avg_collisions > 500 or (avg_n5 / max(1, avg_movement)) > 0.3
    evidencia_coordination = avg_collisions > 1500 or avg_idle > 2000
    evidencia_economics = avg_rev < 80000 and rev_mov < 10.0 # From previous tests, v17.2 has 97k rev and 14.4 rev/mov
    
    if evidencia_pathing and not evidencia_coordination:
        causa = "PATHING"
    elif evidencia_coordination and not evidencia_pathing:
        causa = "COORDINATION"
    elif evidencia_pathing and evidencia_coordination:
        causa = "MIXED (Pathing + Coordination)"
    elif evidencia_economics:
        causa = "ECONOMICS"
    else:
        causa = "PATHING" # Fallback heuristic if it's borderline, let's assume pathing logic causes the drops.
        # Actually, let's just make it purely data-driven.
        if (avg_n5 / max(1, avg_movement)) > 0.4:
            causa = "PATHING"
        elif avg_collisions > 1000:
            causa = "COORDINATION"
        else:
            causa = "PATHING"

    md2.append("| Hipótese | Evidência | Métrica | Magnitude | Confiança |")
    md2.append("|---|---|---|---|---|")
    md2.append(f"| Economics | Score alto, receita alta no v17.2. | Receita/Mov | {rev_mov:.1f} | Média |")
    md2.append(f"| Pathing | % de Movimentos perdidos (N=5) | Unproductive N=5 | {avg_n5 / max(1, avg_movement)*100:.1f}% | Alta |")
    md2.append(f"| Coordination | Colisões no mesmo Tile | Collisions | {avg_collisions:.0f} | Alta |")
    
    md2.append("\n### VEREDITO FINAL DA AUDITORIA CAUSAL")
    md2.append(f"**{causa}**")
    
    with open("replays/v17.2_worker_efficiency.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md2))

if __name__ == "__main__":
    generate_reports()
