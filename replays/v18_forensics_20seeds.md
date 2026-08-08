# Kaggriculture — Laboratório v18 (Forensics e Causalidade)
## Verificação de Integridade
- Todas as 20 seeds rodaram para os 4 agentes.
- Instâncias independentes: Sim.
- State Integrity Layer mantido: Sim.

## 1. Performance Global (Score) vs v17.2
| Variante | Score Médio | Mediana | Std Dev | Mín | Máx | W/L/T | Mean Delta | Median Delta | Std Delta | Min Delta | Max Delta |
|---|---|---|---|---|---|---|---|---|---|---|---|
| v17.2 | 54478 | 54260 | 13464 | 31787 | 79516 | - | - | - | - | - | - |
| v18A | 9691 | 9150 | 3576 | 1851 | 16689 | 0/20/0 | -44786 | -44233 | 15779 | -72803 | -15266 |
| v18B | 24215 | 24894 | 5486 | 15397 | 33287 | 0/20/0 | -30263 | -28717 | 14961 | -51140 | -987 |
| v18C | 311 | 328 | 45 | 201 | 354 | 0/20/0 | -54166 | -53927 | 13471 | -79188 | -31447 |

## 2. Economia e Movimento (Médias)
| Variante | Receita Total | Custo Animais | Custo Sementes | Lucro Bruto | Distância | Receita/Mov |
|---|---|---|---|---|---|---|
| v17.2 | 97308 | 6995 | 2824 | 87489 | 6724 | 14.47 |
| v18A | 17643 | 0 | 4620 | 13023 | 7511 | 2.35 |
| v18B | 53607 | 800 | 4398 | 48409 | 7947 | 6.75 |
| v18C | 4022 | 0 | 5326 | -1304 | 5319 | 0.76 |

## 3. Eficiência Operacional e Produção
| Variante | Total Actions | PASS Rate | PLANT | WATER | HARVEST | FEED | CARE |
|---|---|---|---|---|---|---|---|
| v17.2 | 9103 | 3.7% | 102 | 52 | 564 | 338 | 253 |
| v18A | 7902 | 2.9% | 363 | 340 | 301 | 0 | 0 |
| v18B | 9221 | 0.2% | 703 | 283 | 339 | 57 | 61 |
| v18C | 6024 | 0.3% | 219 | 83 | 969 | 0 | 0 |

## 4. Análise Causal (Matchmaking vs Laboratório)
A premissa do v18 era que *abandonar o animal flywheel* (0 COW, 0 SHEEP) reduziria o movimento, eliminaria o gargalo de FEED/CARE e permitiria um spam massivo de crops de alto valor (como visto no topo do matchmaking).

**Por que v18A (Pure Crop) perdeu do v17.2?**
1. **Queda de Receita**: A receita caiu de 97k para 17k. O motor econômico de cultivos de alto valor depende do adubo gerado pelos animais e/ou do capital inicial gerado pelos produtos animais para comprar sementes caras (Strawberry). Sem vacas, o agente entra em estagnação financeira.
2. **Aumento de Movimento**: Ironicamente, o movimento do v18A foi *maior* (7511) do que o v17.2 (6724). Isso destrói a hipótese espacial. Sem rotinas locais de FEED/CARE, os workers gastaram pathing rodando o mapa atrás de lotes isolados ou plantando culturas ineficientes por falta de dinheiro.

**Por que v18B (2 Cows) superou v18A?**
Ao reintroduzir 2 vacas, a receita subiu para 53k (Score 24k). As 2 vacas geraram capital suficiente via MILK/FERTILIZER para destravar as compras agrícolas. Isso confirma que **Kaggriculture possui um mínimo múltiplo comum econômico**: animais não são apenas fontes de lucro, são **enableds de liquidez**. Zero animais causa *deadlock financeiro* no early game.

**O problema do Matchmaking Ranking**
Se o Top 3 do matchmaking não tem animais e faz $50k, por que o v18A não conseguiu? Porque os jogadores de matchmaking provavelmente utilizam **pathing altamente otimizado (DFS/TSP local) para agricultura** e estratégias agressivas de mercado (manipulação de preço). A infraestrutura de pathing do v17.2 foi otimizada para *sinergia animal/crop*. Quando tiramos os animais, expomos a ineficiência do algoritmo de colheita/plantio do v17.2 em modo puramente extensivo.

**A Catástrofe do v18C (Adaptive ROI)**
A adaptação falhou completamente (Score 311). Ao considerar apenas preço/tempo, o agente tentou fazer compras de sementes sem avaliar a liquidez diária, resultando em mais de 10.000 triggers de Circuit Breaker. O ROI econômico real requer computar custo de oportunidade de movimento.