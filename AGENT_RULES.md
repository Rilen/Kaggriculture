# 🚜 Manual de Regras e Prioridades do Agente (Kaggriculture) — v10

Este documento define a Árvore de Decisão e as regras de negócio que o agente autônomo deve seguir a cada turno da simulação. Versão atual: **v10 Early Game Acelerado**.

---

## 🧭 0. Estratégia Global — 3 Táticas Avançadas

### Tática 1 — Horizonte de Eventos (Corte de Plantio)
- Culturas só são plantadas se houver tempo hábil para colher antes do dia 30.
- Janelas definidas em `_get_valid_crops(day, op_flooding_melon)`:
  - **MELON**: dia ≤ 19 (exceto se oponente floodando)
  - **STRAWBERRY**: dia ≤ 18
  - **TOMATO**: dia ≤ 21
  - **WHEAT**: dia ≤ 25
  - **CARROT**: dia ≤ 26
- Aplicado na compra de sementes (`_build_market_orders`) e na ação de plantio (`_plant_action`).

### Tática 2 — Espionagem Industrial (Scout do Oponente)
- A cada turno, o agente inspeciona a fazenda do oponente (`op_farm`) e conta quantos **MELON** ele tem plantados.
- Se `op_melons > 8`: o oponente está prestes a inundar o mercado de melão.
  - **Ação imediata:** vender **TODO** o estoque de MELON do shed.
  - **Bloqueio:** não comprar novas sementes de MELON.
- Isso evita que o preço do melão desabe para $1 e o agente fique com estoque encalhado.

### Tática 3 — Flush Noturno Preventivo
- A partir das **22h** (`hour >= 22`), o agente calcula o `projected_shed = total_shed + sum(inventories)`.
- Se `projected_shed >= 95`, ativa **`panic_flush`**: vende tudo, mantendo apenas 2 WHEAT.
- Fora do pânico, se `total_shed > 75` (SHED_SOFT_CAP), ativa `force_sell` com reservas reduzidas (5 WHEAT, 5 FERTILIZER).
- **Motivo:** evitar descarte de itens por overflow no fim do dia (shed cap = 100).

---

## 💰 1. Regras de Mercado e Galpão (Shed)

Antes de qualquer ação no campo, o agente organiza finanças e inventário.

### 1.1 — Venda de Produtos
- Itera sobre todos os itens do shed (exceto animais vivos: GOOSE, COW, SHEEP).
- **MELON + op_flooding_melon**: vende 100% imediatamente.
- **WHEAT**: mantém reserva proporcional a `animal_count * 3 + 5` (mín. 5), reduzida para 5 em `force_sell`, ou 2 em `panic_flush`.
- **FERTILIZER**: mantém 100% em modo normal, 5 em `force_sell`, 0 em `panic_flush`.
- **Demais produtos**: mantém 3 unidades de buffer (0 em force_sell).

### 1.2 — Compra de Sementes
- Targets por cultura: MELON=4, WHEAT=6, CARROT=4, TOMATO=2, STRAWBERRY=2.
- Só compra culturas presentes em `valid_crops` (Tática 1).
- Mantém ≥ 200 moedas de reserva após a compra.
- Respeita `MAX_MARKET_ORDERS = 10`.

### 1.3 — Expansão e Contratação

**BUY_LAND (v10 — custo real + prioridade):**
- Tabela `LAND_COST = {1: 1000, 2: 2000, 3: 4000}` mapeia n° de quadrantes já desbloqueados → custo exato do próximo.
- Condição de compra: `money > land_cost + 500` (reserva operacional de $500 pós-compra).
- **BUY_LAND é emitido ANTES das ordens de semente**, garantindo que nunca seja cortado pelo limite de 10 ordens.

**HIRE (v10 — threshold adaptativo ao estágio do jogo):**

| Fase | Dias | Threshold de tarefas urgentes | Reserva mínima de caixa |
|------|------|-------------------------------|-------------------------|
| Early | 0–5 | ≥ 3 tarefas | $200 |
| Mid-Early | 6–10 | ≥ 6 tarefas | $400 |
| Late | 11+ | ≥ 12 tarefas | $500 (comportamento v9) |

- Contrata apenas se não há hands ativos (`len(hands) == 0`).
- Fibonacci nos dias iniciais (custo 1–5 moedas) → ROI imediato com qualquer tarefa pendente.

**Seed Targets (v10 — escalados por quadrantes):**

| Quadrantes desbloqueados | MELON | WHEAT | CARROT | TOMATO | STRAWBERRY |
|--------------------------|-------|-------|--------|--------|------------|
| 1 (inicial) | 4 | 6 | 4 | 2 | 2 |
| 2 | 6 | 8 | 5 | 3 | 3 |
| ≥ 3 | 8 | 10 | 6 | 4 | 4 |

**Reserva de capital dinâmica:**
- `seed_reserve = max(200, land_cost // 2)` — guarda metade do custo do próximo quadrante antes de comprar sementes.
- Evita gastar tudo em seeds e ficar sem capital para a expansão iminente.

### 1.4 — Liquidação Fim-de-Temporada (dia ≥ 27)
- A partir do dia 27, vende **todos** os itens do shed (exceto animais vivos) sem reservas.

---

## 👨‍🌾 2. Pathfinding com BFS e Prioridades de Movimento

### 2.1 — BFS Nearest
- `_bfs_nearest(start, condition, farm, exclude)`: busca em largura a partir de `start`, retornando `(target_x, target_y, first_direction)` do tile mais próximo que satisfaz `condition(tile, x, y)` e não está em `exclude`.
- Direções testadas na ordem: NORTH, SOUTH, WEST, EAST.

### 2.2 — Prioridades de Movimento (lambdas ordenadas)
Quando o worker está em um tile sem ação imediata, o BFS busca o alvo mais próximo nesta ordem:

| Prioridade | Condição do tile alvo |
|:----------:|----------------------|
| 1 | PLANT não regada hoje e não na lista `watered_this_day` |
| 2 | COOP/PASTURE com animal não alimentado hoje, não na lista `fed_this_day`, e WHEAT disponível |
| 3 | PLANT pronta para harvest (`age >= max`) OU qualquer estrutura com `yield_units > 0` |
| 4 | PLANT de MELON/STRAWBERRY fertilizável (`fertilized_until_day < day`) e FERTILIZER disponível |
| 5 | COOP/PASTURE com `fertilizer_available == True` |
| 6 | COOP/PASTURE com animal e `!cared_today` |
| 7 | COOP/PASTURE vazia (sem animal) e worker tem animal compatível no inventário |
| 8 | WEED (mato) |
| 9 | Tile vazio (`None`) — para build ou plantio |

- Tiles já atribuídos (`assigned`) são excluídos para evitar que dois workers disputem o mesmo alvo.

---

## 🌱 3. Ações no Tile Atual (por Worker)

Para cada unidade (farmer/hand), avalia-se o tile em que ela se encontra:

### 3.1 — Tile Vazio (`None`)
1. **BUILD_COOP / BUILD_PASTURE** se `_get_build_priority()` retornar comando.
2. **PLANT**: escolhe a cultura de maior valor em `PLANT_PRIORITY` que tenha sementes disponíveis e esteja em `valid_crops`. Rotações: MELON em dias múltiplos de 3, WHEAT em dias pares.

### 3.2 — WEED
- `DIG` (limpa o mato).

### 3.3 — PLANT (cultura)
- **Colheita one-time** (WHEAT, CARROT, MELON):
  - `age >= max_day` → `HARVEST`
  - `first_day <= age < max_day`: WATER (se não regada) → FERTILIZE (se elegível) → HARVEST (se a 1 dia do max e já tratada)
- **Colheita ongoing** (TOMATO, STRAWBERRY):
  - `age >= first_day` e `yield_units > 0` → `HARVEST`
- **Antes do first_day**: WATER → FERTILIZE → PASS

### 3.4 — COOP / PASTURE (estrutura animal)
- **Sem animal**: `PLACE` se worker tem animal compatível no inventário.
- **Com animal** (prioridade):
  1. `FEED` se `!fed_today` e WHEAT no shed
  2. `COLLECT_FERTILIZER` se `fertilizer_available`
  3. `CARE` se `!cared_today`
  4. `HARVEST` se `yield_units > 0`
  5. `PASS`

---

## 🏗️ 4. Regras de Construção (`_get_build_priority`)

| Condição | Ação |
|----------|------|
| 0 gansos + 0 coops vazios + dia < 5 | `BUILD_COOP` |
| < 2 gansos + 0 coops vazios + `animals_bought > goose_count` + dia < 10 | `BUILD_COOP` |
| 0 vacas + ≥ 2 gansos + dia ≥ 8 + WHEAT > 15 + 0 pastagens vazias | `BUILD_PASTURE` |

---

## 🏚️ 5. Interação com o Shed

- **PICKUP**: worker adjacente ao shed, inventário vazio, e shed tem animal (GOOSE/COW/SHEEP) → pega 1. Incrementa `self.animals_bought`.
- **DROP**: worker adjacente ao shed com inventário > 5 itens → despeja tudo no shed.

---

## 🔄 6. Ciclo de Turno

```
1. Se novo dia: reseta watered_this_day e fed_this_day.
2. _scan_tiles(): varre todos os tiles, populando water_needed, feed_needed, harvest_ready.
3. _build_market_orders(): aplica Táticas 1/2/3, gera ordens de SELL/BUY_SEED/HIRE/BUY_LAND.
4. Para cada worker (farmer + hands):
   a. Se tile atual tem ação → executa.
   b. Senão, se adjacente ao shed → PICKUP/DROP.
   c. Senão, BFS para o tile mais próximo com tarefa pendente → movimento.
   d. Senão → PASS.
5. Retorna {"farmer": [...], "hands": [[...], ...], "market": [[...], ...]}.
```

---

## 📊 7. Constantes de Configuração

| Constante | Valor | Descrição |
|-----------|-------|-----------|
| `MAX_MARKET_ORDERS` | 10 | Máximo de ordens de mercado por turno |
| `SHED_SOFT_CAP` | 75 | Threshold para force_sell |
| `SHED_HARD_CAP` | 100 | Capacidade máxima do shed |
| `PREMIUM_THRESHOLD` | 100 | Preço base acima do qual o produto é considerado "premium" |
| `PLANT_PRIORITY` | MELON > STRAWBERRY > TOMATO > CARROT > WHEAT | Ordem de valor para escolha de plantio |
| `LAND_COST` | `{1: 1000, 2: 2000, 3: 4000}` | Custo real de BUY_LAND por quadrantes já desbloqueados |
