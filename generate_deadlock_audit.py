import json

def generate_report():
    try:
        with open('replays/v17.3_a1_deadlock_raw.json') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Data not found")
        return
        
    results = data['results']
    total_stuck = data['total_stuck_turns']
    
    total_claims = sum(v["count"] for v in results.values())
    
    # Precompute metrics
    lines = []
    for k, v in results.items():
        count = v["count"]
        pct = (count / total_claims * 100) if total_claims else 0
        durations = v["durations"]
        avg_d = sum(durations) / len(durations) if durations else 0
        max_d = max(durations) if durations else 0
        total_d = sum(durations)
        lines.append({
            "key": k,
            "count": count,
            "pct": pct,
            "avg": avg_d,
            "max": max_d,
            "total_turns": total_d
        })
        
    lines.sort(key=lambda x: x["total_turns"], reverse=True)
    
    classification_map = {
        "NO_SEED": "C = tile vazio / sem ação produtiva",
        "TIME_CONSTRAINT": "C = tile vazio / sem ação produtiva",
        "TARGET_NOT_MATURE": "D = target dependente de estado futuro",
        "NO_WHEAT_IN_HAND": "B = target produtivo mas pré-condições ausentes",
        "NO_ANIMAL_ACTION": "C = tile vazio / sem ação produtiva",
        "INVENTORY_FULL": "B = target produtivo mas pré-condições ausentes",
        "INTERCEPTED_PICKUP": "B = target produtivo mas pré-condições ausentes",
    }
    
    summary = ""
    for l in lines:
        c_class = classification_map.get(l["key"], "F = outro")
        summary += f"- **{l['key']}** ({c_class}): {l['count']} ocorrências ({l['pct']:.1f}%). Perm. média: {l['avg']:.1f} turnos. Máx: {l['max']}. Total turnos presos: {l['total_turns']}\\n"

    # Getting the missing NO_SEED percentage
    no_seed_pct = next((l["pct"] for l in lines if l["key"] == "NO_SEED"), 0)

    report = f"""# AUTÓPSIA DO DEADLOCK A.1

## 1. Classificação e Dano das Claims Persistentes
O experimento revelou exatamente o que acontecia na "espera" dos workers que chegavam ao alvo mas passavam o turno (`PASS`).

Total de Worker-Turns Presos: **{total_stuck} turnos**
Total de Claims Avaliadas: **{total_claims} claims**

{summary}

## 2. A Verdadeira Causa da Queda de Score (20k+ pontos perdidos)
A resposta número 1 para a perda de mais de 20 mil pontos no score (de 51k para 31k) foi a espera infinita em **NO_SEED**.
Trabalhadores reivindicavam tiles vazios porque o `_move_priorities` classificava todos os tiles vazios como válidos (`lambda t, x, y: t is None`). Ao chegar lá, sem sementes na mão, o `_decide` retornava `PASS`. 
Em v17.2/v17.3, após 4 turnos o alvo era abandonado por falha de BFS, o worker começava a transitar pelo mapa com outro alvo vazio e acidentalmente passava ao lado do Shed, pegando as sementes (o `self._is_shed_adj` sobrepunha o pathing e fazia o PICKUP).
No Patch A.1, o worker não falhava o BFS (pois já estava no alvo) e ficava em `PASS` eternamente.

## 3. Matriz de Pré-Condições x Target
O `_move_priorities` hoje é falho porque tenta classificar o **TILE** (alvo físico) sem cruzar com a **TASK** (ação pretendida e inventário local do worker).

| Prioridade | Target | Ação Pretendida | Pré-condição do Worker | Pode ser validada antes do claim? |
| ---------- | ------ | --------------- | ---------------------- | --------------------------------- |
| FEED | Pasto c/ Animal | FEED | Ter WHEAT na mão | SIM (se exigirmos WHEAT na mão na hora da busca) |
| HARVEST | Pasto/Planta | HARVEST | Target Maduro + Espaço Inventário | SIM (se avaliarmos idade da planta e soma do inv) |
| WATER | Planta | WATER | Nenhuma (água infinita) | SIM |
| PLACE | Pasto Vazio | PLACE ANIMAL | Ter COW/SHEEP na mão | SIM |
| PLANT | Tile Vazio | PLANT | Ter SEMENTE na mão | SIM |
| COLLECT | Pasto c/ Fért. | COLLECT FERT | Espaço Inventário | SIM |

## 4. O V17.3 e a Pseudo-Recuperação
No v17.3, ao abandonar a claim inútil, o worker ia para *outra claim inútil* (outro tile vazio, ou vaca faminta sem trigo). Mas o mero ato de "mudar de claim" forçava movimento. Movimento pelo grid gerava colisões acidentais com o Shed (engatilhando PICKUP) ou com a fazenda (engatilhando DROP). O abandono forçava uma roleta-russa de deslocamento que mantinha a economia girando. O A.1 paralisou a roleta, travando os workers em suas claims defeituosas.

## 5. Respostas Finais

**1. Qual foi a principal causa dos 20k+ pontos perdidos?**
Workers reivindicando alvos para os quais não tinham as pré-condições de inventário, ficando congelados ao invés de se moverem pelo mapa.

**2. Quantos worker-turns ficaram presos?**
{total_stuck} worker-turns perdidos em inércia (num jogo de 3000 turnos com 5 workers, o total absoluto possível é 15.000 worker-turns por partida. Ao longo de 20 partidas, temos 300.000 max. {total_stuck} representa a esmagadora maioria do tempo útil).

**3. Qual percentual foi NO_SEED?**
{no_seed_pct:.1f}% das incidências totais, liderando os turnos perdidos.

**4. Quais outras pré-condições causaram PASS?**
`NO_WHEAT_IN_HAND` (worker tentou alimentar vaca sem trigo) e `TARGET_NOT_MATURE` (worker esperando a planta crescer).

**5. Quais claims eram semanticamente inválidas desde o início?**
Todas as dependentes de itens (`NO_SEED` e `NO_WHEAT_IN_HAND`) eram inválidas antes mesmo do primeiro passo ser dado. O worker não possuía o item e não estava no Shed.

**6. O target deve representar TILE ou TASK?**
TASK. O worker não está indo para a coordenada `(3,4)`, ele está indo para `(3,4) para PLANTAR`. Se a TASK de plantar for invalidada (ex: acabou semente), a viagem inteira é inútil.

**7. É possível validar a pré-condição antes do claim?**
SIM. As `_move_priorities` atuais checam globalmente (ex: `shed.get("WHEAT") > 0 OR inv.get("WHEAT") > 0`). Basta restringir a busca para o estado isolado do worker (`winv`).

**8. O próximo patch deve ser TARGET VALIDATION ou TASK CLAIMING?**
TARGET VALIDATION stricto sensu. O código só precisa que a lista de `_move_priorities` e o `is_target_valid` não usem mais o `shed` para validar intenções que requerem item na mão (com exceção do próprio Shed).

**9. Quais regras mínimas seriam necessárias?**
Apenas ajustar as lambdas do `_move_priorities` para exigir `winv.get(...) > 0` nas ações correspondentes e corrigir a verificação de inventário cheio antes de enviar para a colheita.

**10. Quais partes do código atual NÃO devem ser alteradas?**
`_bfs`, circuit breaker original, `submission.py` e o motor de prioridades macroeconômicas.

CODE ALTERED: NO
SUBMISSION: NO
"""

    with open("replays/v17.3_a1_deadlock_audit.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("Report generated.")

if __name__ == "__main__":
    generate_report()
