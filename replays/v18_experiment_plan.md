# Plano Experimental v18 (Crop-Heavy)

## Hipótese Central
A estratégia dominante no ecossistema Kaggle baseia-se na máxima eficiência espacial (receita/movimento) focada em culturas de altíssimo valor agregado (Melon e Strawberry) com ciclo fechado (PLANT -> WATER -> HARVEST -> SELL), dispensando totalmente a imobilização de capital, área e tempo exigida pelo Animal Flywheel (COW/SHEEP).

## Objetivo do Experimento
Verificar se uma mutação do nosso baseline robusto (`v17.2`), mantendo o State Integrity e o BFS, porém desativando os animais e migrando 100% do capital para agricultura de alto valor, consegue quebrar a barreira dos `$50k` contra o starter e simular os top players observados nos replays.

---

## 1. Variantes do Experimento

### v18-A (Pure Crop)
- **Animais:** 100% Desativados (`BUY_ANIMAL` bloqueado).
- **Abertura:** Sementes de MELON e STRAWBERRY em massa, poupando os $1.800 que iriam para Vacas e Ovelhas.
- **WHEAT:** Apenas plantado no *Early Game* (Dias 0-5) se o caixa apertar, servindo como "girador de capital".
- **Comportamento Espacial:** Trabalhadores formam clusters nas plantações.

### v18-B (Crop + Animal Reserve)
- **Animais:** Limite drástico (Máx 2 COW, 0 SHEEP).
- **Objetivo:** Descobrir se um minúsculo rebanho fornece um piso seguro de renda (via MILK) para financiar mais MELON/STRAWBERRY no *mid-game*, ou se ele atrapalha o pathing e o capital.

### v18-C (Adaptive ROI)
- **Animais vs Crops:** Nenhuma restrição *hardcoded*. O agente decide dinamicamente calcular o `crop_efficiency = expected_profit / turns_required` e compara com o ROI do animal.
- **Capital Discipline:** Só compra pasto ou animais se a rentabilidade por tile justificar a perda de mobilidade.

---

## 2. Modificações Econômicas Globais

1. **Desacoplamento Agrícola:** WHEAT deixa de ser prioridade no `_decide`. STRAWBERRY e MELON recebem prioridade máxima, escalando com o capital livre.
2. **Nova Métrica `crop_efficiency`:** O agente passará a avaliar `(market_price - seed_cost) / dias_para_crescer` ao decidir qual semente priorizar no mercado.
3. **Expansão Otimizada:** O `BUY_LAND` e `HIRE` só ocorrerão se o agente tiver sementes em estoque e demanda não atendida pelos tiles atuais.

---

## 3. Preservação Arquitetural
As três variantes herdam **SEM MODIFICAÇÃO**:
- BFS Bidirecional
- State Integrity Layer (`_validate_action_preconditions`)
- Circuit Breaker
- Worker Fail-safes
- Telemetria

---

## 4. Cronograma de Testes
1. **Desenvolvimento:** Implementar os 3 arquivos `submission_v18a.py`, `submission_v18b.py` e `submission_v18c.py` sem deletar o `submission.py` atual (v17.2).
2. **Execução Local:** Rodar 20 sementes (mesma matriz do v17.2) de cada variante contra o `starter`.
3. **Análise de Causalidade:** Geração do `v18_forensics_20seeds.md` medindo `revenue/distance` para isolar se a vitória do *Pure Crop* vem de maior receita ou menor movimento.
4. **Decisão:** Avaliação pelo usuário se a variante vendedora avança para o Kaggle (Shadow Trial real).
