# Kaggriculture - Autonomous AI Agent 🚜🤖

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![Kaggle Competition](https://img.shields.io/badge/Kaggle-Kaggriculture-20BEFF?logo=kaggle&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?logo=open-source-initiative&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?logo=statuspage&logoColor=white)
![Score](https://img.shields.io/badge/Skill_Rating-390.3-success?logo=trending&logoColor=white)
![Version](https://img.shields.io/badge/Current_Version-v7-blueviolet?logo=git&logoColor=white)

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

O agente atravessou sete iterações principais. As versões **v1–v6** foram construídas contra um schema de observação assumido (não o oficial da competição), o que resultou em grande parte das ações sendo silenciosamente invalidadas (`no-ops`) pela engine — mesmo assim, ainda jogaram e ganhrarm algum skill rating. A **v7** é a primeira reescrita contra o schema documentado, abrindo espaço para integração completa de todos os recursos do jogo.

| Versão | Estratégia principal | Ações-chave introduzidas | Skill rating | Tendência |
|:------:|----------------------|---------------------------|:------------:|:--------:|
| **v1** *(Baseline)* | Estrutura inicial *rule-based* focada em colheita, rega e cenouras. | Colheita + rega básica | `364.5` | — |
| **v2** | Controle inteligente de capacidade do galpão (*shed*) e diversificação de plantio. | Prevenção de *overflow* + plantio alternado Trigo/Cenoura | `218.7` | ▼ |
| **v3** | Suporte a animais, alimentação diária de trigo e culturas de alto valor. | `FEED` + `HARVEST` animal + plantio de **Melão** | `195.5` | — |
| **v4** | Compra ativa de sementes e lógica automatizada de uso de fertilizantes. | `BUY_SEED` + `FERTILIZE` | `263.6` | — |
| **v5** | Otimização de fluxo de caixa, estoque de trigo e foco expandido em Melão. | Reabastecimento condicional | `225.4` | — |
| **v6** | Venda curativa de overflow, plantio por valor, fertilizante reservado p/ Melão, correção de bug do tile vazio. | Threshold duplo shed + parse robusto | `300.6` | — |
| **v7** *(Atual)* ⭐ | **Reescrita completa contra o schema oficial** — novas 5 culturas, pecuária completa (`FEED`/`CARE`/`COLLECT_FERTILIZER`), vendas com reserva, plantio por valor MEL>STR>TOM>CAR>WHE. | Schema oficial + decisões one-time vs ongoing + manutenção de animais | **`390.3`** | — |

> 🔎 **Nota técnica:** skill rating é um valor Elo-like. A relação com "uma versão mais complexa = mais rating" **não é linear** — depende de quem o bot enfrenta naquele momento. Scores aqui são o rating **publicado** pela Kaggle no leaderboard, não o desempenho direto de moedas. A v7 é a primeira versão a operar contra o schema autêntico, capturando recursos antes inacessíveis.

> 🏆 **Melhor skill rating apurado: v7 = `390.3`** (máximo histórico). A reescrita contra o schema oficial (`farms`/`tiles`/`private`/`market`) foi decisiva: saiu de 300.6 (v6) para 390.3 (+30% de rating) ao integrar pecuária completa, fertilizante, culturas ongoing (Tomato/Strawberry) e vendas estrategicamente limitadas.

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

---

## 🧠 Arquitetura e Fluxo do Agente

O agente está encapsulado na classe `KaggricultureAgentV7` (em `submission.py`) e opera como uma função de estado → ações, invocada pela Kaggle a cada turno, retornando o dict oficial `{"farmer": [...], "hands": [[...], ...], "market": [[...], ...]}`.

```text
┌─────────────────────────────────────────────────────────────┐
│   observation (schema oficial Kaggle)                       │
│   farms[player].tiles[y][x], farmer, hands                  │
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
        │  • tile = farms[player].tiles[y][x]     │
        └──────────────────────┬───────────────────┘
                               ▼
        ┌──────────────────────────────────────────┐
        │     2. GESTÃO DE MERCADO & GALPÃO        │
        │  • SELL produtos (reserva WHEAT/FERT)   │
        │  • SELL excedente se shed > 80          │
        │  • BUY_SEED reabastece alvos por cultura│
        │  • max 10 orders/turno                  │
        └──────────────────────┬───────────────────┘
                               ▼
        ┌──────────────────────────────────────────┐
        │    3. TOMADA DE AÇÃO (por unidade)       │
        │  farmer + cada hand independente         │
        │                                          │
        │  P1 -> EMPTY TILE -> PLANT por valor     │
        │     (MEL > STR > TOM > CAR > WHE)       │
        │  P2 -> WEED -> DIG                       │
        │  P3 -> PLANT one-time:                   │
        │      age>=max -> HARVEST                 │
        │      first<=age<max: WATER/FERTILIZE    │
        │  P3b -> PLANT ongoing (TOM/STR):        │
        │      age>=first -> HARVEST              │
        │  P4 -> ANIMAL (COOP/PASTURE + animal):  │
        │      FEED -> COLLECT_FERTILIZER         │
        │      -> CARE -> HARVEST                  │
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
private = obs["private"]
money = farm["money"]           # saldo (coins) - vence quem tem mais
tile = farm["tiles"][y][x]       # None | "LOCKED" | dict(PLANT/WEED/COOP/PASTURE)
shed = private["shed"]          # produtos colhidos + fertilizer
seeds = private["seeds"]        # sementes (consumidas por PLANT)
prices = obs["market"]["prices"]
day = obs["day"]; hour = obs["hour"]
```
Cada tile é interpretado pelo campo `kind` (`"PLANT"`, `"WEED"`, `"COOP"`/`"PASTURE"`), com `None` representando solo livre desbloqueado e `"LOCKED"` representando quadrante não comprado.

#### 2. Gestão de Mercado e Galpão
```python
total_shed = sum(shed.values())
force_sell = total_shed > 80   # venda emergencial evita overflow (cap=100)
```
- **Venda seletiva:** mantem WHEAT (estoque p/ alimentar animais) acima de 20 unidades (ou 5 se lotado) e FERTILIZER acima de 5 (se lotado); demais produtos guardam 3 unidades como buffer.
- **Reabastecimento:** compra sementes conforme alvo por cultura (Melon 5, Wheat 8, Carrot 6, Tomato 3, Strawberry 3), mantendo margem de ≥ 200 moedas de reserva após a compra.

#### 3. Tomada de Ação na Fazenda (prioridades encadeadas)

| Ordem | Ação | Condição de disparo |
|:-----:|------|---------------------|
| P1 | `PLANT` | Tile `None`: escolhe cultura de maior valor disponível em `seeds` |
| P2 | `DIG` | Tile `kind == "WEED"` |
| P3 | `WATER` | Planta presente e `!watered_today` |
| P3b | `FERTILIZE` | Planta de alto valor (MEL/STR), não fertilizada hoje, e `shed[FERTILIZER] > 0` |
| P4 | `HARVEST` | Planta one-time com `age >= max_yield_day` (ou ongoing com `age >= first` e `yield_units > 0`) |
| P5 | `FEED` | Animal presente, `!fed_today`, `shed[WHEAT] > 0` |
| P5b | `COLLECT_FERTILIZER` | Animal com `fertilizer_available == True` |
| P5c | `CARE` | Animal com `!cared_today` |
| P5d | `HARVEST` | Animal com `yield_units > 0` |
| — | `PASS` | Nenhuma das condições (incl. `LOCKED`) |

> 🔬 **Culturas one-time vs ongoing**: para Wheat/Carrot/Melon, o agente adia a colheita até `max_yield_day` para capturar o bônus máximo; para Tomato/Strawberry, colhe assim que produz (pois continuam produzindo em intervalos fixos).

#### 3. Tomada de Ação na Fazenda (prioridades encadeadas)

| Ordem | Ação | Condição de disparo |
|:-----:|------|---------------------|
| P1 | `HARVEST` | Planta presente e pronta para colher |
| P1.1 | `FEED` / `HARVEST` | Tile com animal; alimenta se ainda não foi alimentado, colhe se pronto para produzir |
| P2 | `WATER` | Planta presente e sem água no dia |
| P2.1 | `FERTILIZE` | Planta presente, não fertilizada recentemente, e fertilizante no inventário |
| P3 | `DIG` | Presença de mato (*weed*) no tile |
| P4 | `PLANT` | Tile vazio (sem planta/estrutura/mato); escolhe a cultura de maior valor disponível em sementes |
| — | `PASS` | Nada a fazer neste turno |

> 🔁 A seleção de plantio prioriza **valor**: Melão > Trigo > Cenoura, conforme disponibilidade de sementes. Quando não há sementes em estoque, cai na rotação por dia (Melão a cada 3 dias, Trigo em dias pares, Cenoura nos demais).

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

Exemplo — reprodutível da última submissão (v7):

```bash
kaggle competitions submit -c kaggriculture \
  -f submission.py \
  -m "Versão 7: Reescrita completa usando schema oficial - plantio por valor, pecuaria completa, vendas com reserva."
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
