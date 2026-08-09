# Kaggriculture - Autonomous AI Agent 🚜🤖

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![Kaggle Competition](https://img.shields.io/badge/Kaggle-Kaggriculture-20BEFF?logo=kaggle&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?logo=open-source-initiative&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?logo=statuspage&logoColor=white)
![Score](https://img.shields.io/badge/Skill_Rating-637.0-success?logo=trending&logoColor=white)
![Version](https://img.shields.io/badge/Current_Version-v17.3_A.10-blueviolet?logo=git&logoColor=white)

> Um agente autônomo em Python, desenvolvido iterativamente para a competição de simulação **Kaggriculture** da Kaggle. Projeto construído com auxílio do **KiloCode CLI** e versionado via Git.

---

## 📋 Sumário

1. [Sobre a Competição](#-sobre-a-competição)
2. [Histórico de Evolução e Versões](#-histórico-de-evolução-e-versões)
3. [Arquitetura e Fluxo do Agente](#-arquitetura-e-fluxo-do-agente)
4. [Instruções de Uso e CLI](#-instruções-de-uso-e-cli)
5. [Tecnologias Utilizadas](#-tecnologias-utilizadas)
6. [Licença](#-licença)

---

## 🌾 Sobre a Competição

A **Kaggriculture** é uma competição de simulação em turnos onde o seu agente assume o controle de uma fazenda virtual e **disputa head-to-head contra outro agente**. Cada partida executa ao longo de **720 turnos**, equivalentes a **30 dias** de operação (24 turnos por dia), dentro de um ambiente dinâmico e estocástico.

Cold start: fazenda vazia, 1 fazendeiro principal e **US$ 3.000** de capital inicial (`startingMoney = 3000`). Novos quadrantes de terra podem ser comprados por **US$ 1k / 2k / 4k** (`BUY_LAND`).

### 🎯 Objetivos do Agente

| Domínio | Descrição |
|---------|-----------|
| 🌱 **Gestão de Culturas** | Plantio, rega, fertilização e colheita de 5 culturas: Wheat, Carrot, Tomato, Strawberry, Melon. |
| 🐄 **Pecuária** | Cuidar de animais (Goose/Cow/Sheep) — alimentação diária com trigo, `CARE` para bonus, `COLLECT_FERTILIZER` diário e coleta de ovos/leite/lá. |
| 🏪 **Mercado Dinâmico** | Preços base fixos para sementes/animais; preços de venda variam com o inventário do mercado (função de scarce/glut). |
| 🏚️ **Gestão do Galpão (Shed)** | Capacidade de 100 itens (sementes não contam). Overflow descarta — controle de vendas é essencial. |
| 👨‍🌾 **Mão de Obra** | Contratar trabalhadores temporários (`HIRE`) com custo crescente de Fibonacci por dia. |
| 🗺️ **Expansão** | Compra de quadrantes vizinhos com `BUY_LAND`. |
| 💰 **Vitória** | **Vence quem tiver mais moedas no banco** ao final dos 720 turnos (itens não vendidos não contam). |

> ⚙️ **Métrica de leaderboard:** skill rating (estilo Elo via Bradley-Terry). Ao jogar um episódio contra um oponente de skill similar, ganhar **aumenta** o rating, perder **diminui**. O skill rating sobe com a taxa de vitórias — não é um "score de moedas" direto. Itens não vendidos ao final do jogo **não contam** para a vitória, então vender antes do fim é crucial.

> 📝 **Evolução:** v1 a v6 foram construídas a partir de um schema de observação assumido (não o oficial), o que limitou muito seu desempenho na arena real. A **v7** é a primeira versão escrita contra o schema oficial documentado em `AGENTS.md`/`README.md` da competição, abraçando todos os blocos: movimento, shed (`PICKUP`/`DROP`/`PLACE`), mercado, animais, fertilizante, cuidado e expansão de terra.

---

## 📈 Histórico de Evolução e Versões

O agente atravessou nove iterações principais. As versões **v1–v6** foram construídas contra um schema de observação assumido (não o oficial da competição), o que resultou em grande parte das ações sendo silenciosamente invalidadas (`no-ops`) pela engine. A **v7** é a primeira reescrita contra o schema documentado. A **v8** introduziu BFS para pathfinding e contratação de peões. A **v9** adiciona táticas avançadas de espionagem, flush noturno e horizonte de eventos.

| Versão | Estratégia principal | Ações-chave introduzidas | Skill rating | Tendência |
|:------:|----------------------|---------------------------|:------------:|:--------:|
| **v1** *(Baseline)* | Estrutura inicial *rule-based* focada em colheita, rega e cenouras. | Colheita + rega básica | `364.5` | — |
| **v2** | Controle inteligente de capacidade do galpão (*shed*) e diversificação de plantio. | Prevenção de *overflow* + plantio alternado Trigo/Cenoura | `218.7` | ▼ |
| **v3** | Suporte a animais, alimentação diária de trigo e culturas de alto valor. | `FEED` + `HARVEST` animal + plantio de **Melão** | `195.5` | — |
| **v4** | Compra ativa de sementes e lógica automatizada de uso de fertilizantes. | `BUY_SEED` + `FERTILIZE` | `263.6` | — |
| **v5** | Otimização de fluxo de caixa, estoque de trigo e foco expandido em Melão. | Reabastecimento condicional | `225.4` | — |
| **v6** | Venda curativa de overflow, plantio por valor, fertilizante reservado p/ Melão, correção de bug do tile vazio. | Threshold duplo shed + parse robusto | `300.6` | — |
| **v7** | **Reescrita completa contra o schema oficial** — 5 culturas, pecuária completa, vendas com reserva. | Schema oficial + decisões one-time vs ongoing | **`390.3`** | ▲ |
| **v8** | BFS pathfinding, expansão agressiva, contratação inteligente de peões, construção de estruturas. | `BUILD_COOP`/`BUILD_PASTURE` + `HIRE` + `BUY_LAND` + BFS | TBD | — |
| **v9** | **Táticas Avançadas**: Espionagem industrial, Horizonte de Eventos (corte de plantio), Flush Noturno preventivo. | Espionagem de oponente + corte fim-de-temporada + flush hour≥22 | TBD | — |
| **v10** *(Atual)* ⭐ | **Early Game Acelerado**: BUY_LAND com custo real, HIRE adaptativo por fase, seed_targets escalados por quadrante, reserva de capital dinâmica. | `LAND_COST` table + HIRE threshold por dia + seeds escalonados | TBD | — |
| **v15** *(Baseline vencedor)* | **Fixed Asset Engine**: flywheel MILK/WOOL com 8 COW + 6 SHEEP, PLANT priority MELON>STRAWBERRY>WHEAT, BFS bidirecional, state integrity layer. | Schema oficial + animal survival fix + worker_targets persistence | **`502.6`** | ▲ |
| **v17** *(Estratégia)* | **Scarcity Rancher**: abertura MELON 9 + STRAWBERRY 3, WATER priority #1, PICKUP gate por empty_past, wheat_price real. | STRAWBERRY early + WATER top + feed buffer dinâmico | **`537.3`** | ▲ |
| **v17.3** *(Arquitetura)* | **Worker Persistence**: `worker_targets` com persistência entre turnos, `assigned` como reservation table, telemetria de claims/releases/persistence. | worker_targets dict + target_claims/releases + circuit breaker | **`502.6`** | — |
| **A.9** *(Estável)* | **Revert + Fix**: retorno a v17.3 baseline com correção de stale reservation — `release_target()` antes de DROP/forced return. | release_target() em 3 pontos + revert A.6/A.7/A.8 | **`637.0`** | ▲ |
| **A.10** *(Deployed)* | **CARE Timing Filter**: CARE apenas se expected days to yield < 3 (~57 passos). COW sempre qualifies, SHEEP only if producing, GOOSE sempre qualifies. | _expected_days_to_yield() + _is_care_valuable() | pending | — |
| **A.11** *(In Progress)* | **Seb Meta Copy**: STRAWBERRY expansion (15 seeds), FERTILIZER buying + collection priority, consistent hiring every day, DROP frequency increase, endgame liquidation. | STRAWBERRY_TARGET + BUY_PRODUCT FERTILIZER + endgame rules | dev | — |

> 🔎 **Nota técnica:** skill rating é um valor Elo-like. A relação com "uma versão mais complexa = mais rating" **não é linear** — depende de quem o bot enfrenta naquele momento. Scores aqui são o rating **publicado** pela Kaggle no leaderboard, não o desempenho direto de moedas.

> 🏆 **Melhor skill rating apurado: A.9 = `637.0`** (máximo histórico). A revert para baseline v17.3 + fix de stale reservation superou todos os experimentos anteriores. A.10 introduz CARE timing filter baseado em forensics de oponentes topo.

### 🔍 Detalhamento das Versões

<details>
<summary><b>v1 — Baseline Rule-Based</b> <i>(Skill: 364.5)</i></summary>

Primeira iteração estabelecendo o esqueleto de percepção e ação. Foco exclusivo em manter plantas vivas: colher o que estivesse pronto e regar quando necessário. Cultivo limitado à Cenoura.
</details>

<details>
<summary><b>v2 — Gestão de Shed e Diversificação</b> <i>(Skill: 218.7)</i></summary>

Introdução do controle de inventário: o agente passa a monitorar o total de itens no galpão e a liquidar excedentes no mercado antes do *overflow*. Plantio alternado entre **Trigo** e **Cenoura** para equilibrar oferta e demanda.
</details>

<details>
<summary><b>v3 — Pecuária e Alto Valor</b> <i>(Skill: 195.5)</i></summary>

Adição do ramo pecuário: detecção de animais no *tile*, alimentação diária (`FEED`) e coleta de produtos prontos. Inauguração do cultivo de **Melão** — cultura de maior valor unitário — em ciclos de 3 dias.
</details>

<details>
<summary><b>v4 — Sementes e Fertilização</b> <i>(Skill: 263.6)</i></summary>

Adoção de compras estratégicas (`BUY_SEED MELON` / `BUY_SEED WHEAT`) com base em saldo de moedas e espaço de ações no turno. Lógica automatizada de `FERTILIZE` que dobra o rendimento de plantas quando há fertilizante disponível no inventário.
</details>

<details>
<summary><b>v5 — Fluxo de Caixa e Foco em Melão</b> <i>(Skill: 225.4)</i></summary>

Otimização do reabastecimento condicional de sementes, com prioridade a Melão e estoque de trigo para alimentação dos animais. Refinamento do fluxo de caixa para evitar desperdício de moedas.
</details>

<details>
<summary><b>v6 — Correções Estruturais e Robustez</b> <i>(Skill: 300.6)</i></summary>

> A versão atual, presente no arquivo <code>submission.py</code>.

- **Venda curativa de overflow**: threshold duplo no galpão. *Crowded* (`>70`) vende metade; *critical* (`>80`) esvazia o shed respeitando valor (vende o de menor valor primeiro).
- **Plantio por valor**: escolhe a cultura de maior valor disponível em sementes (Melão > Trigo > Cenoura), com fallback na rotação por dia.
- **Fertilizante reservado**: `FERTILIZE` agora só dispara em culturas de alto valor (Melão), evitando desperdício em cenouras.
- **Reabastecimento condicional**: só compra sementes quando o inventário está abaixo dos limites definidos; compra `FERTILIZER` somente se houver caixa suficiente (`coins > 600`).
- **Bug crítico corrigido**: tiles vazios (`{}`) eram tratados como inexistentes pela v4, impedindo o plantio em solo recém-limpo. Agora `_pertile_state` distingue tile inexistente (`None`) de tile vazio.
- **Robustez**: helpers `_as_int`/`_as_dict` toleram campos `None`, ausentes ou de tipos inválidos, evitando crashes em environments malformados.
</details>

<details>
<summary><b>v7 — Reescrita Contra o Schema Oficial</b> <i>(Skill: 390.3)</i> ⭐ — <i>versão atual</i></summary>

> A versão atual, presente no arquivo <code>submission.py</code>. Primeira versão escrita contra o schema de observação oficial documentado em <code>AGENTS.md</code>/<code>README.md</code> da competição.

**Mudança de base:**
- O schema real usa <code>obs["farms"][player]["tiles"][y][x]</code>, <code>obs["private"]["shed"]</code>, <code>obs["private"]["seeds"]</code>, <code>obs["market"]["prices"]</code>, <code>obs["town"]</code> — não os campos <code>units</code>/<code>board</code>/<code>inventory</code>/<code>coins</code> assumidos nas versões anteriores.
- As ações agora retornam o dict oficial <code>{"farmer": [op,...], "hands": [[op,...],...], "market": [[op,...],...]}</code> — não uma lista flat de strings.

**Decisões por unidade (farmer e hands):**
- **Plantio por valor**: <code>MELON > STRAWBERRY > TOMATO > CARROT > WHEAT</code>, conforme sementes disponíveis.
- **Colheita inteligente one-time vs ongoing**:
  - *One-time* (Wheat/Carrot/Melon): rega+fertiliza na janela de bonus para maximizar yield; colhe quando <code>age >= max_yield_day</code> (ou 1 dia antes, se já estiver tratado).
  - *Ongoing* (Tomato/Strawberry): colhe assim que <code>age >= first_yield_day</code> e há <code>yield_units</code> — a planta continua produzindo.
- **Fertilização**: só dispara em culturas de alto valor (Melão/Morango) e se houver fertilizante no shed.
- **Pecuária completa**: para tiles com animal, executa em prioridade `FEED -> COLLECT_FERTILIZER -> CARE -> HARVEST`.
- **Limpeza**: `DIG` em weeds; respeita tiles `LOCKED` com `PASS`.

**Mercado**:
- Vende produtos colhidos do shed, reservando WHEAT (estoque para alimentação) e FERTILIZER (insumo).
- Venda emergencial quando <code>total > 80</code> itens (para evitar descarte no overflow de capacidade 100).
- Reabastecimento de sementes por cultura com targets distintos (Melon 5, Wheat 8, Carrot 6, Tomato 3, Strawberry 3), respeitando margem de caixa.

**Compatibilidade**: mantem os aliases <code>agent()</code>, <code>agent_fn(obs, configuration)</code> e <code>main_agent(obs, configuration)</code> para garantir aceitação por variações do runtime Kaggle.
</details>

<details>
<summary><b>v8 — BFS + Expansao + Pecuaria + Arbitragem Municipal</b> <i>(Skill: TBD)</i></summary>

**Pathfinding com BFS:**
- <code>_bfs_nearest(start, condition, farm, exclude)</code>: varredura em largura a partir da posição atual, retornando direção do primeiro passo para o alvo mais próximo que satisfaz a condição.
- <code>_build_move_priorities()</code>: 8 lambdas de prioridade ordenada (água → comida → colheita → fertilizante → coleta_fert → care → place_animal → weed → plantio), cada uma servindo como <code>condition</code> para o BFS.
- Evita overbooking com <code>assigned</code> set, impedindo que dois peões disputem o mesmo tile.

**Construção e Expansão:**
- <code>_get_build_priority()</code>: constrói COOP se 0 gansos + 0 coops vagos (dia<5), ou se <2 gansos com animais comprados (dia<10). Constrói PASTURE quando há ≥2 gansos e 0 vacas (dia≥8).
- <code>BUY_LAND</code> quando <code>money > 1500 × quadrantes_desbloqueados</code> e há quadrantes a comprar.
- <code>HIRE</code> quando <code>urgent_tasks > 12</code> e <code>money > 500</code> e sem peões contratados.

**Arbitragem Municipal:**
- Monitoramento de preços via <code>_track_prices()</code> (histórico rolling de 10 passos).
- Utiliza <code>SHOP_DEMAND</code> mapeado para referência de quais lojas consomem quais produtos.

**Pecuária completa:**
- Suporte a GOOSE/COW/SHEEP com <code>PICKUP</code> do shed, <code>PLACE</code> na estrutura correta, <code>FEED</code> (consome WHEAT do shed), <code>COLLECT_FERTILIZER</code>, <code>CARE</code>, <code>HARVEST</code>.
- Worker inventory tracking para decidir entre PICKUP/DROP/PLACE.
</details>

<details>
<summary><b>v9 — Horizonte de Eventos + Espionagem + Flush Noturno + Fix LSP</b> <i>(Skill: TBD)</i> ⭐ — <i>versão atual</i></summary>

> A versão atual, presente no arquivo <code>submission.py</code>.

**Tática 1 — Horizonte de Eventos (Corte de Plantio):**
- Método estático <code>_get_valid_crops(day, op_flooding_melon=False)</code> consolida as janelas de plantio em um único ponto de verdade.
- Culturas só são plantadas se houver tempo hábil para colher antes do fim da temporada: MELON até dia 19, STRAWBERRY até dia 18, TOMATO até dia 21, WHEAT até dia 25, CARROT até dia 26.
- Aplicado tanto nas ordens de compra de sementes (<code>_build_market_orders</code>) quanto na ação de plantio (<code>_plant_action</code>).

**Tática 2 — Espionagem Industrial:**
- <code>_build_market_orders</code> inspeciona a fazenda do oponente (<code>op_farm</code>) contando melões plantados.
- Se <code>op_melons > 8</code> (oponente inundando o mercado de melão), o agente vende **todo** o estoque de MELON imediatamente, antes que o preço desabe.
- Também bloqueia novas compras de semente de MELON quando o oponente está floodando.

**Tática 3 — Flush Noturno Preventivo:**
- Detecta <code>hour >= 22</code> e <code>projected_shed >= 95</code> (shed + inventórios dos peões): ativa <code>panic_flush</code>.
- Em pânico, mantém apenas 2 WHEAT e 0 FERTILIZER; vende todo o resto.
- Fora de pânico, se <code>shed > 75</code> (soft cap), força venda com reservas reduzidas (5 WHEAT, 5 FERTILIZER).

**Correções de Código (Fix LSP):**
- <code>self.animals_bought</code> agora é incrementado em cada <code>PICKUP</code> de animal do shed, destravando a lógica de construção de COOPs adicionais.
- Variável não utilizada <code>town_shops</code> removida.
- Lógica <code>valid_crops</code> extraída para <code>_get_valid_crops()</code>, eliminando duplicação.
</details>

<details>
<summary><b>v10 — Early Game Acelerado</b> <i>(Skill: TBD)</i> ⭐ — <i>versão atual</i></summary>

> A versão atual, presente no arquivo <code>submission.py</code>.

**Problema resolvido:** o agente v9 perdia no Dia 6 para oponentes que escalavam mais rápido, por três ineficiências no early game.

**Mudança 1 — BUY_LAND com custo real:**
- Tabela `LAND_COST = {1: 1000, 2: 2000, 3: 4000}` substitui a fórmula imprecisa `1500 × quadrantes`.
- Threshold: `money > land_cost + 500` (reserva pós-compra).
- BUY_LAND é emitido **antes das ordens de semente**, garantindo prioridade máxima dentro do limite de 10 ordens.

**Mudança 2 — HIRE adaptativo:**
- Dias 0–5: contrata com ≥ 3 tarefas urgentes e $200 no caixa (Fibonacci ≈ 1–3 moedas).
- Dias 6–10: threshold de 6 tarefas e $400 de reserva.
- Dias 11+: comportamento original (12 tarefas, $500).

**Mudança 3 — Seed targets escalados por quadrante:**
- 1 quadrante: targets originais (MELON=4, WHEAT=6, ...).
- 2 quadrantes: MELON=6, WHEAT=8, CARROT=5, TOMATO=3, STRAWBERRY=3.
- ≥3 quadrantes: MELON=8, WHEAT=10, CARROT=6, TOMATO=4, STRAWBERRY=4.

**Mudança 4 — Reserva de capital dinâmica:**
- `seed_reserve = max(200, land_cost // 2)` — guarda metade do custo do próximo quadrante antes de comprar seeds.
- Garante que o capital não fique preso em sementes quando a compra de terra está iminente.

</details>

---

## 🧠 Arquitetura e Fluxo do Agente

O agente está encapsulado na classe `KaggricultureAgentV9` (em `submission.py`) e opera como uma função de estado → ações, invocada pela Kaggle a cada turno, retornando o dict oficial `{"farmer": [...], "hands": [[...], ...], "market": [[...], ...]}`.

```text
┌─────────────────────────────────────────────────────────────┐
│   observation (schema oficial Kaggle)                       │
│   farms[player].tiles[y][x], farmer, hands                  │
│   farms[1-player] (espionagem)                              │
│   private.shed, private.seeds, private.inventories          │
│   market.prices, market.inventory, town.unlocked_shops       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────┐
        │       1. PERCEPÇÃO DE ESTADO             │
        │  • player, day, hour, step               │
        │  • farms[player].money                   │
        │  • private.shed / private.seeds          │
        │  • scan_tiles → water/feed/harvest tasks │
        │  • op_farm (espionagem do oponente)     │
        └──────────────────────┬───────────────────┘
                               ▼
        ┌──────────────────────────────────────────┐
        │     2. GESTÃO DE MERCADO & GALPÃO        │
        │  • Tática 3: Flush Noturno (hour≥22)     │
        │  • Tática 2: Espionagem (op_melons>8)    │
        │  • Tática 1: Horizonte de Eventos        │
        │     (corte de sementes por deadline)     │
        │  • SELL produtos (reserva dinâmica)      │
        │  • BUY_SEED (só culturas válidas)        │
        │  • HIRE se urgente + BUY_LAND expansão   │
        │  • max 10 orders/turno                   │
        └──────────────────────┬───────────────────┘
                               ▼
        ┌──────────────────────────────────────────┐
        │    3. TOMADA DE AÇÃO (por unidade)       │
        │  farmer + cada hand independente         │
        │  BFS pathfinding p/ tile mais próximo    │
        │                                          │
        │  P0 -> EMPTY TILE -> BUILD_COOP/PASTURE  │
        │  P1 -> EMPTY TILE -> PLANT (prioridade)  │
        │  P2 -> WEED -> DIG                       │
        │  P3 -> PLANT one-time:                   │
        │      age>=max -> HARVEST                 │
        │      first<=age<max: WATER/FERTILIZE    │
        │  P3b -> PLANT ongoing (TOM/STR):        │
        │      age>=first -> HARVEST              │
        │  P4 -> ANIMAL (COOP/PASTURE):           │
        │      PLACE -> FEED -> COLLECT_FERT      │
        │      -> CARE -> HARVEST                  │
        │  P5 -> SHED ADJACENT:                    │
        │      PICKUP animal / DROP overflow       │
        │  fallback -> BFS para próxima tarefa     │
        │  fallback -> PASS                        │
        └──────────────────────┬───────────────────┘
                               ▼
        ┌──────────────────────────────────────────┐
        │  return {"farmer":[op], "hands":[...],  │
        │          "market":[[op,...], ...]}      │
        └──────────────────────────────────────────┘
```

### Blocos Lógicos

#### 1. Percepção de Estado
```python
player = obs["player"]
farm = obs["farms"][player]
op_farm = obs["farms"][1 - player]   # espionagem
private = obs["private"]
money = farm["money"]
tile = farm["tiles"][y][x]           # None | "LOCKED" | dict
shed = private["shed"]
seeds = private["seeds"]
inventories = private["inventories"]
prices = obs["market"]["prices"]
day = obs["day"]; hour = obs["hour"]
```
Cada tile é interpretado pelo campo `kind` (`"PLANT"`, `"WEED"`, `"COOP"`/`"PASTURE"`), com `None` representando solo livre desbloqueado e `"LOCKED"` representando quadrante não comprado.

#### 2. Gestão de Mercado e Galpão (com Táticas Avançadas)

**Tática 1 — Horizonte de Eventos:**
```python
valid_crops = self._get_valid_crops(day, op_flooding_melon)
# MELON só até dia 19, STRAWBERRY até 18, TOMATO até 21, etc.
```

**Tática 2 — Espionagem Industrial:**
```python
op_melons = count(op_farm tiles where crop == "MELON")
op_flooding_melon = op_melons > 8
if op_flooding_melon: vende TODO o MELON e bloqueia compra
```

**Tática 3 — Flush Noturno:**
```python
projected_shed = total_shed + sum(worker inventories)
panic_flush = (hour >= 22 and projected_shed >= 95)
force_sell = panic_flush or (total_shed > SHED_SOFT_CAP)  # 75
```
- **Venda seletiva:** em pânico mantém só 2 WHEAT; força venda mantém 5 WHEAT e 5 FERTILIZER; normal mantém buffer proporcional a animais.
- **Reabastecimento:** compra sementes conforme alvo por cultura, apenas para culturas em `valid_crops`.
- **Reabastecimento:** compra sementes conforme alvo por cultura (Melon 4, Wheat 6, Carrot 4, Tomato 2, Strawberry 2), apenas para culturas em `valid_crops`, mantendo margem de ≥ 200 moedas.

#### 3. Tomada de Ação na Fazenda (prioridades encadeadas com BFS)

| Ordem | Ação | Condição de disparo |
|:-----:|------|---------------------|
| P0 | `BUILD_COOP` / `BUILD_PASTURE` | Tile `None`: build se condições de `_get_build_priority()` satisfeitas |
| P1 | `PLANT` | Tile `None`: escolhe cultura de maior valor disponível em `seeds`, só se `crop in valid_crops` |
| P2 | `DIG` | Tile `kind == "WEED"` |
| P3 | `WATER` | Planta presente e `!watered_today` |
| P3b | `FERTILIZE` | Planta de alto valor (MEL/STR), não fertilizada hoje, `shed[FERTILIZER] > 0` |
| P4 | `HARVEST` | Planta one-time com `age >= max_yield_day` (ou ongoing com `age >= first` e `yield_units > 0`) |
| P5 | `FEED` / `COLLECT_FERTILIZER` / `CARE` / `HARVEST` | Animal presente no tile; prioridade FEED → COLLECT_FERT → CARE → HARVEST |
| P6 | `PICKUP` / `DROP` | Worker adjacente ao shed: PICKUP de animal sem inventory, DROP se inventory > 5 |
| — | `BFS movement` | Nenhuma ação no tile atual: BFS para o tile mais próximo com tarefa pendente |
| — | `PASS` | Nenhuma condição atendida (incl. `LOCKED`) |

> 🔬 **Culturas one-time vs ongoing**: para Wheat/Carrot/Melon, o agente adia a colheita até `max_yield_day` para capturar o bônus máximo; para Tomato/Strawberry, colhe assim que produz (pois continuam produzindo em intervalos fixos).

> 🕵️ **Espionagem**: se oponente tem >8 MELONs plantados, vende-se TODO o estoque de MELON imediatamente e bloqueia-se novas compras da semente.

> 🌙 **Flush Noturno**: a partir das 22h, se shed + inventórios ≥ 95 itens, ativa `panic_flush` vendendo tudo exceto 2 WHEAT.

---

## 🚀 Instruções de Uso e CLI

### 1. Configuração das Credenciais

Autentique a CLI do Kaggle. Recomenda-se o **OAuth** (sem gerenciar tokens manualmente):

```bash
# Opção A — OAuth (recomendado)
kaggle auth login
```

Alternativa com token de API gerado em https://www.kaggle.com/settings/api:

```bash
# Opção B — variável de ambiente
export KAGGLE_API_TOKEN=SEU_TOKEN_AQUI

# Opção C — arquivo de token
mkdir -p ~/.kaggle
echo "SEU_TOKEN_AQUI" > ~/.kaggle/access_token
chmod 600 ~/.kaggle/access_token
```

> ⚠️ **Segurança:** nunca faça commit do seu token. Mantenha `~/.kaggle/` fora do controle de versão.

### 2. Submissão Oficial

A partir da raiz do repositório:

```bash
kaggle competitions submit -c kaggriculture -f submission.py -m "Mensagem descritiva da versão"
```

Exemplo — reprodutível da última submissão (v9):

```bash
kaggle competitions submit -c kaggriculture \
  -f submission.py \
  -m "v9 Masterpiece: Espionagem Industrial + Corte Fim-de-Temporada + Flush Noturno + Fix LSP"
```

### 3. Monitoramento de Submissões

```bash
# Acompanhar status e skill rating das últimas tentativas
kaggle competitions submissions -c kaggriculture

# Verificar o leaderboard global
kaggle competitions leaderboard -c kaggriculture -s

# Baixar logs de debug de um episódio específico
kaggle competitions logs <EPISODE_ID> 0
```

---

## 🎓 Aula de Estratégia — Como o Agente Funciona

### O jogo em 1 frase

Você e um oponente controlam fazendas idênticas, lado a lado, por **30 dias** (720 turnos). No final, **quem tem mais dinheiro no banco vence**. Itens que sobraram no galpão não contam.

### O ciclo econômico real

```
Dia 0-5:  Early Game — construir infraestrutura (PASTURE/COOP), contratar mão de obra, plantar sementes baratas (WHEAT/CARROT)
Dia 6-15: Mid Game — escalar produção animal (COW/SHEEP), regar/fertilizar plantas, colher MELON/STRAWBERRY
Dia 16-25: Late Game — colheitas massivas, vender no pico de preço, manter apenas reservas estratégicas
Dia 26-30: End Game — vender TUDO (flush), animais contam mais que plantas porque produzem todo dia
```

### Dinheiro: onde entra e onde sai

| Entrada | Saída |
|---------|-------|
| Venda de produtos (MILK, WOOL, MELON, EGG, STRAWBERRY) | Compra de sementes (WHEAT=$10, MELON=$80, STRAWBERRY=$100) |
| Venda de animais | Compra de animais (COW=$400, SHEEP=$500, GOOSE=$300) |
| | BUY_LAND ($1k/$2k/$4k) |
| | HIRE (Fibonacci: 1,1,2,3,5,8,13...) |
| | WHEAT para FEED (custo variável pelo mercado) |

**Regra de ouro:** o galpão cabem 100 itens. Se encher, **o excesso desaparece**. Vender antes de encher é obrigatório.

### Disputa: não é PvP direto, é disputa de mercado

Você não ataca o oponente. A disputa é **econômica**:

1. **Preços reagem à oferta/demanda global**: se todo mundo vender MELON, o preço cai. Se ninguém tiver WHEAT, o preço sobe.
2. **Town Center compra 1 de cada produto por dia**: é uma âncora de demanda.
3. **Shops aleatórios**: a cada 3 dias, uma nova loja abre comprando produtos específicos.
4. **Oponente é um concorrente de mercado**: se ele plantar 10 MELONs e vender tudo, o preço do MELON desaba e seu MELON vale menos.

### Exemplo prático: agente vs oponente

**Cenário:** Ambos começam com $3.000, 1 farmer, 25 tiles.

**Oponente "meta":**
- Dia 0-2: compra 8 COW + 6 SHEEP, constrói 14 PASTURE
- Dia 3-10: rega/fertiliza MELON e STRAWBERRY
- Dia 10-20: colhe MELON (250/unit) e STRAWBERRY (120/unit), vende no pico
- Dia 20-30: colhe produtos animais infinitos (MILK=160, WOOL=200)

**Nosso agente (A.10):**
- Dia 0-2: mesmo plano, mas com **WATER priority #1** (não deixar plantas virar weed)
- Dia 3-10: **CARE timing filter** — só faz CARE em animais próximos do yield (COW a cada 2 dias, SHEEP só se produzindo)
- Dia 10-20: colhe no **momento certo** (max yield), não antes
- Dia 20-30: mantém animal flywheel, vende tudo no final

**Por que nosso agente ganha?**
- Oponente pode fazer ações similares, mas **no momento errado**
- Nosso CARE timing filter garante que cada CARE gere +18% mais downstream value
- Nosso release_target() evita stale reservation — workers não disputam o mesmo tile
- Nosso WATER priority garante que nenhuma planta morra virando weed

### Os 3 segredos que aprendemos com os oponentes topo

1. **RPA (Revenue Per Action) é tudo**: top players geram $126 por ação, nós gerávamos $41. Não é fazer MAIS ações, é fazer cada ação VALER MAIS.
2. **CARE timing é o maior differentiator**: fazer CARE 42% mais rápido e próximo ao yield gera +18% DS5. É o equivalente a "acertar o timing de um combo" num jogo de luta.
3. **Seletividade > Volume**: winners plantam -14.6% menos, water -9.3% menos, mas colhem no PICO. Menos ações, mais valor por ação.

### Estado atual do agente

| Submissão | Score | Estratégia |
|-----------|-------|------------|
| A.9 | 637.0 | Baseline v17.3 + fix stale reservation |
| A.10 | pending | + CARE timing filter (TTY < 57 steps) |
| A.5 | 537.3 | WATER priority #1 |
| V17.3 | 502.6 | Worker persistence architecture |

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Uso no projeto |
|------------|----------------|
| ![Python](https://img.shields.io/badge/Python-3.x-blue) | Linguagem do agente e lógica de decisão |
| ![Kaggle CLI](https://img.shields.io/badge/Kaggle_API/CLI-2.x-20BEFF) | Submissão automatizada e consulta de *leaderboard* |
| ![KiloCode CLI](https://img.shields.io/badge/KiloCode_CLI-Agent-orange) | Desenvolvimento assistido por IA |
| ![Git](https://img.shields.io/badge/Git-Versioning-F05032) | Controle de versão do código |

---

## 📄 Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [`LICENSE`](./LICENSE) para detalhes.

---

<p align="center">
  <i>Desenvolvido iterativamente para a Kaggriculture • Powered by KiloCode CLI 🚀</i>
</p>
