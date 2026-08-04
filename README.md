# Kaggriculture - Autonomous AI Agent 🚜🤖

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![Kaggle Competition](https://img.shields.io/badge/Kaggle-Kaggriculture-20BEFF?logo=kaggle&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?logo=open-source-initiative&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?logo=statuspage&logoColor=white)
![Score](https://img.shields.io/badge/Best_Score-600.0-success?logo=trending&logoColor=white)

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

A **Kaggriculture** é uma competição de simulação em turnos onde o seu agente assume o controle de uma fazenda virtual. Cada partida executa ao longo de **720 turnos**, equivalentes a **30 dias** de operação (24 turnos por dia), dentro de um ambiente dinâmico e estocástico.

### 🎯 Objetivos do Agente

| Domínio | Descrição |
|---------|-----------|
| 🌱 **Gestão de Culturas** | Plantio, rega, fertilização e colheita de culturas (Cenoura, Trigo, Melão). |
| 🐄 **Pecuária** | Cuidar de animais — alimentação diária com trigo e coleta de produtos prontos. |
| 🏪 **Mercado Dinâmico** | Compra estratégica de sementes e fertilizantes, venda de excedentes para gerar caixa. |
| 🏚️ **Gestão do Galpão (Shed)** | Prevenção de *overflow* do inventário, mantendo fluxo de produção estável. |
| 💰 **Maximização de Lucro** | Otimizar a função de recompensa — **minimizar o erro absoluto (lower = melhor)**. |

> ⚙️ **Métrica de avaliação:** a pontuação final é o erro absoluto em relação a um alvo ótimo. Quanto **menor** o número, melhor o desempenho. Score de referência atual: **`600.0`**.

---

## 📈 Histórico de Evolução e Versões

O agente foi refinado em quatro iterações principais. Cada versão adicionou uma camada de inteligência sobre a anterior, reduzindo progressivamente o erro absoluto.

| Versão | Estratégia principal | Ações-chave introduzidas | Score | Tendência |
|:------:|----------------------|--------------------------|:-----:|:--------:|
| **v1** *(Baseline)* | Estrutura inicial *rule-based* focada em colheita, rega e cenouras. | Colheita + rega básica | `364.5` | — |
| **v2** | Controle inteligente de capacidade do galpão (*shed*) e diversificação de plantio. | Prevenção de *overflow* + plantio alternado Trigo/Cenoura | `218.7` | ▼ |
| **v3** | Suporte a animais, alimentação diária de trigo e culturas de alto valor. | `FEED` + `HARVEST` animal + plantio de **Melão** | `480.1` | ▼ |
| **v4** *(Atual)* | Compra ativa de sementes e lógica automatizada de uso de fertilizantes. | `BUY_SEED` + `FERTILIZE` | **`600.0`** | ▼ |

### 🔍 Detalhamento das Versões

<details>
<summary><b>v1 — Baseline Rule-Based</b> <i>(Score: 364.5)</i></summary>

Primeira iteração estabelecendo o esqueleto de percepção e ação. Foco exclusivo em manter plantas vivas: colher o que estivesse pronto e regar quando necessário. Cultivo limitado à Cenoura.
</details>

<details>
<summary><b>v2 — Gestão de Shed e Diversificação</b> <i>(Score: 218.7)</i></summary>

Introdução do controle de inventário: o agente passa a monitorar o total de itens no galpão e a liquidar excedentes no mercado antes do *overflow*. Plantio alternado entre **Trigo** e **Cenoura** para equilibrar oferta e demanda.
</details>

<details>
<summary><b>v3 — Pecuária e Alto Valor</b> <i>(Score: 480.1)</i></summary>

Adição do ramo pecuário: detecção de animais no *tile*, alimentação diária (`FEED`) e coleta de produtos prontos. Inauguração do cultivo de **Melão** — cultura de maior valor unitário — em ciclos de 3 dias.
</details>

<details>
<summary><b>v4 — Sementes e Fertilização</b> <i>(Score atual: 600.0)</i></summary>

> A versão atual, presente no arquivo <code>submission.py</code>.

Adoção de compras estratégicas (`BUY_SEED MELON` / `BUY_SEED WHEAT`) com base em saldo de moedas e espaço de ações no turno. Lógica automatizada de `FERTILIZE` que dobra o rendimento de plantas quando há fertilizante disponível no inventário.
</details>

---

## 🧠 Arquitetura e Fluxo do Agente

O agente está encapsulado na classe `KaggricultureAgentV4` (em `submission.py`) e opera como uma função de estado → ações, invocada pela Kaggle a cada turno.

```text
┌─────────────────────────────────────────────────────────────┐
│                    observation (Kaggle)                      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────┐
        │       1. PERCEPÇÃO DE ESTADO             │
        │  • Turno/Dia (step // 24)                │
        │  • Inventário & Moedas                   │
        │  • Posição dos fazendeiros (units)        │
        │  • Estado do board por tile               │
        └──────────────────────┬───────────────────┘
                               ▼
        ┌──────────────────────────────────────────┐
        │     2. GESTÃO DE MERCADO & GALPÃO        │
        │  • Conta itens no shed (overflow > 75)   │
        │  • SELL excedentes quando lotado         │
        │  • BUY_SEED se coins > 400 e space < 8   │
        └──────────────────────┬───────────────────┘
                               ▼
        ┌──────────────────────────────────────────┐
        │    3. TOMADA DE AÇÃO NA FAZENDA          │
        │  (por fazendeiro, com prioridades)       │
        │                                          │
        │  P1 → HARVEST (planta pronta)            │
        │  P1.1 → FEED / HARVEST (animal)          │
        │  P2 → WATER (planta sem água)            │
        │  P2.1 → FERTILIZE (dobra rendimento)     │
        │  P3 → DIG (limpeza de mato/weed)         │
        │  P4 → PLANT (MEA / WHEAT / CARROT)       │
        │  fallback → PASS                          │
        └──────────────────────┬───────────────────┘
                               ▼
        ┌──────────────────────────────────────────┐
        │            return actions[]              │
        └──────────────────────────────────────────┘
```

### Blocos Lógicos

#### 1. Percepção de Estado
```python
turn = observation.get('step', 0)
self.current_day = turn // 24
inventory = observation.get('inventory', {})
coins = observation.get('coins', 1000)
```
Determina o **dia atual** (24 turnos = 1 dia) e extrai inventário e saldo para decisões de mercado.

#### 2. Gestão de Mercado e Galpão
```python
total_items_in_shed = sum(inventory.values())
is_shed_crowded = total_items_in_shed > 75   # evita overflow
```
- **Venda preventiva:** se o galpão estiver lotado (`>75`) ou houver coluna com `>20` unidades, vende no mercado.
- **Compra estratégica:** com `coins > 400` e espaço de ações (`<8`), reposi sementes de Melão e Trigo.

#### 3. Tomada de Ação na Fazenda (prioridades encadeadas)

| Ordem | Ação | Condição de disparo |
|:-----:|------|---------------------|
| P1 | `HARVEST` | Planta presente e pronta para colher |
| P1.1 | `FEED` / `HARVEST` | Tile com animal; alimenta se ainda não foi alimentado, colhe se pronto para produzir |
| P2 | `WATER` | Planta presente e sem água no dia |
| P2.1 | `FERTILIZE` | Planta presente, não fertilizada recentemente, e fertilizante no inventário |
| P3 | `DIG` | Presença de mato (*weed*) no tile |
| P4 | `PLANT` | Tile vazio; rotação Melão → Trigo → Cenoura conforme `current_day` |
| — | `PASS` | Nada a fazer neste turno |

> 🔁 A rotação de plantio segue o dia: `MELON` a cada 3 dias, `WHEAT` em dias pares e `CARROT` nos demais.

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

Exemplo — reprodutível da última submissão (v3):

```bash
kaggle competitions submit -c kaggriculture \
  -f submission.py \
  -m "Versão 3: Adicionada lógica de suporte a animais, alimentação e culturas de maior valor como Melão."
```

### 3. Monitoramento de Submissões

```bash
# Acompanhar status e pontuação das últimas tentativas
kaggle competitions submissions -c kaggriculture
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
