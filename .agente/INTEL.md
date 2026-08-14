# INTEL — Inteligência sobre Oponentes e Meta (via MCP)

> Alimentado na inicialização de cada sessão com pesquisa MCP (Kaggle): leaderboard,
> discussões, notebooks meta, relatórios de vencedores, datasets de análise.
> Atualizado: 2026-08-14

## Resumo executivo

- Topo do leaderboard (2026-08-14): **カワシギ 3264.3** · Ueddy 3116.0 · researchstudio.site 3110.2 ·
  Utkarsh #2 3098.7 · somewhere after 3092.6 · Mohamed abdelrazik 3086.1. Kaito Fukami saiu do topo.
- Rating reflete vitórias/derrotas, não moedas. Moedas altas → vitórias → rating alto.
- **Meta atual: pecuária determinística ~9 COW + 4 SHEEP + 1 WHEAT + 10–12 mãos + NE+NW+SW,
  84k mediano / 155k max de moedas.** Nós (melão-puro v7): 27–43k, 1/7 vitórias reais.
- Top players são **hardcoded** (traço idêntico entre jogos; 3/3, 3/3, 5/6 nos testados).
  Exceção: Seb (LB #1) adapta execução (35–66% idêntico).

## Notebooks meta baixados (`.agente/intel/kernels/` + `/tmp/kilo/meta/` novos)

| Kernel | Tese |
|--------|------|
| findings-from-zero-to-top-meta | Diário do topo C92–C95 (agente C95 extraído p/ `/tmp/kilo/c95_main.py`) |
| strawberry-pays-24x-what-the-price-table-says | Morango rende 24x o preço tabelado |
| weedproof-clone-market | Clone de mercado à prova de mato |
| dual-market-relay | Relé de mercado duplo |
| easy-bronse-in-lb-2628-2 | Bronze fácil no LB |
| **what-the-top-farms-do-a-live-meta** (Furina, 12/08, 70v) | Meta ao vivo: modal 9C/4S, sell rhythm, relatório diário 08-11 |
| **adaptive-farming-strategy** (tetsutani, 14/08, 108v) | 2 rotas completas 720 turnos selecionadas por demanda do town |
| **rank-your-agent** (raykkretzschmar, 13/08, 73v) | Ladder 10 agentes + Bradley-Terry; glut curves por produto |
| **structured-economic-policy** (pilkwang, 14/08, 88v) | Política econômica reativa; mãos 12→13; field antes de market |
| **adaptive-replay-agent** (flexonafft, 14/08, 68v) | Replay agent adaptativo |
| **v16-rc5-8c-4s-premium-market-lead** (boatlee, 12/08, 82v) | Rota 8C/4S reconstruída (Nikita 55440039) + market lead 1 turno |

## Novidades / segredos capturados (por sessão)

### 2026-08-12 — Perfil do líder (Kaito Fukami) e meta atual
- **Líder: Kaito Fukami** (@kaitofukami), Data Scientist na Financial Engineering Group
  (Tóquio), tier EXPERT. Fonte: `kaggle_get_user_profile` + `kaggle_search_content`.
- **Método (post "How I Keep Iterating Kaggriculture Agents", topic 734212):** loop fechado
  — derrotas reais → 1 mecanismo de falha → challengers → testa múltiplos times nos DOIS
  seats → rejeita a maioria → congela o vencedor → valida em episódios futuros. Usa Codex
  Sol Ultra como ferramenta, mas nunca confia quando ela chama a solução de "ótima".
- **Artefato v27** ("25/27 Strict-Future | v27 Midgame Meta Reset", 151 votos): rota
  DETERMINÍSTICA open-loop de **719 ações** em `main.py` (20.813 bytes, stdlib, hash público),
  clonada do replay público do Ezzzzzekki (episódio 91493566) + overlays de WEED repair e
  ordenação de SELL por price-impact. NÃO é RL de verdade; o tag é cosmético.
- **Abertura-meta do Top-30:** **26/30 times** usam o mesmo core `1 COW + 4 SHEEP + 5/5
  sementes + WHEAT 5 + HIRE4/5`. Abertura virou prior; o edge está na CONTINUAÇÃO (step ~161+).
- **Validação dele:** inner screen (30 casos) + development outer (30) + janela strict-future
  (27 casos, EpisodeId > cutoff). Rejeitou seat-router por resolver só 1/3 das derrotas reais.
- **Balance changes 2026-08-06 (PR #1394, engine ≥1.32.6):** Town Center compra 1x/dia (era
  2x com múltiplos no fim); shops sorteados COM reposição → mercado mais sensível a glut.
- **Avaliação final:** torneio único Bradley-Terry após 2 semanas de episódios pós-deadline.
- **Dataset oficial diário de replays:** `kaggle/kaggriculture-episodes-*` + índice
  `kaggle/kaggriculture-episodes-index` (útil para IL/BC/contrafactual).
- **Fingerprints de abertura dos top-5** (`revanthtambisetty/kaggriculture-top-player-opening-
  fingerprints`): 3 clusters — `v23_fork` (Mohamed/tao_wu11/mrgrishninsb, 2C+2S+5H),
  `sheep_first_hybrid` (HealthStone, 1C+4S+3H+CARE), `counter_meta` (Seb, 14H+4 quads).
- **Fraquezas do estilo do líder:** (a) open-loop — não reage em runtime; (b) rota clonada
  pública e previsível; (c) perdeu 2/27 strict-future por margens <1.000; (d) 1 caso
  wheat-heavy não resolvido; (e) iteração cara (snapshot/freeze) → lento a reagir; (f) cada
  submissão parte de rating baixo (path dependence).

### 2026-08-14 — Partidas reais do v7 (1V/6D) + live-meta + agente C95 extraído
- **v7 real: 1V/6D.** Vitória 39.476 (oponente 12 mãos+animais mal executado = 19.289);
  derrotas apertadas 34–35k (oponentes 36–50k, 5 vacas+morango+SW); derrotas por esmagamento
  30.238–30.383 (oponentes **147.936–160.285** — pecuária completa da meta).
- **Live-meta (Furina, dados 08-11):** modal farm 9C/4S+1WHEAT · 10 mãos · NE+NW+SW (30%);
  money mediano 84.151 / max 154.941. Evolução: 8c/6s·9-10m (08-07) → 8c/6s·11m (08-08/09) →
  9c/4s·10m (08-10/11). Sell rhythm: FERTILIZER d4 b4.9 · MELON d10 b7.7 · MILK d11 b7.7 ·
  STRAWBERRY d15 b15.4 · WHEAT d8 b11.6 · WOOL d6 b9.8.
- **Engine 1.32.x (confirmado no código local 1.32.6):** MELON max_yield **6**, max_yield_day 12,
  janela rega 6–12, cap 6 só com rega → **fertilizar melão é desperdício**; WHEAT max_yield 6
  exige fertilizante; STRAWBERRY max_yield 4 interval 2; animal = 1 fertilizante/dia vendável;
  glut: MELON ~150un (quadrático), MILK/WOOL ~rápidos, WHEAT/EGG glut-proof.
- **C95 (extraído do findings → `/tmp/kilo/c95_main.py`):** rota Lev Neganov ep 91587143 P1 +
  controller c17/c27; vence v7 **6-0** local (77–178k vs 26–33k); vs starter ~113–127k.
  Build order: d0 4H+1C+1S+seeds+5 wheat; d2 SELL FERTILIZER; d7–12 HIRE 6–14/dia +1 COW/dia;
  d10 BUY_LAND + SELL MELON 5; FERTILIZER diário, MILK d9+, WOOL d6+, STRAWBERRY d14+.
- **Rank-your-agent (raykkretzschmar):** versão do engine muda resultados (1.32.3 vs 1.32.6);
  "decidir O QUE vender importa mais do que o que plantar"; leite/lã rendem mais por ação com CARE.
- **Structured-economic-policy (pilkwang):** mãos ceiling 12 (d<20)/13 (d≥20), floor 10; vendas
  preenchidas unidade a unidade na curva → timing importa; lado quadrático do preço é violento.
- **V16-RC5 (boatlee):** rota 8C/4S reconstruída (Nikita 55440039, 99,91% idêntica entre replays);
  "premium market lead" = vender 1 turno antes da venda planejada quando há estoque.

## Ações do topo observadas em replays

- Water ~8.6x por planta vs nossa baseline 0.2x (fixado em v17.3/A.5).
- CARE timing próximo ao yield = +18% DS5.
- RPA (revenue per action): topo ~$126 vs nosso ~$41.

## Checklist de pesquisa a cada início de sessão

1. [ ] Leaderboard atual (`kaggle_get_competition_leaderboard` / `kaggle_search_competitions`)
2. [ ] Discussões/queries recentes da competição (`kaggle_list_competition_topics`, `kaggle_get_forum_topic`)
3. [ ] Notebooks meta novos (`kaggle_search_notebooks`, filtro por competição)
4. [ ] Writeups de vencedores, se houver (`kaggle_get_writeup_by_slug`, `kaggle_list_hackathon_write_ups`)
5. [ ] Datasets de análise (`kaggle_search_datasets`)
6. [ ] Registrar novidades abaixo e atualizar `VERDADE.md` / `REGRAS_DE_OURO.md` se aplicável
