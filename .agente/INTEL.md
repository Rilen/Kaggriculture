# INTEL — Inteligência sobre Oponentes e Meta (via MCP)

> Alimentado na inicialização de cada sessão com pesquisa MCP (Kaggle): leaderboard,
> discussões, notebooks meta, relatórios de vencedores, datasets de análise.
> Atualizado: 2026-08-15 (sessão iniciada, bench validado, MCP completo)

## Resumo executivo

- Topo do leaderboard (2026-08-14): **カワシギ 3264.3** · Ueddy 3116.0 · researchstudio.site 3110.2 ·
  Utkarsh #2 3098.7 · somewhere after 3092.6 · Mohamed abdelrazik 3086.1. Kaito Fukami saiu do topo.
- Rating reflete vitórias/derrotas, não moedas. Moedas altas → vitórias → rating alto.
- **Meta atual: pecuária determinística ~9 COW + 4 SHEEP + 1 WHEAT + 10–12 mãos + NE+NW+SW,
  84k mediano / 155k max de moedas.** Nós (melão-puro v7): 27–43k, 1/7 vitórias reais.
- Top players são **hardcoded** (traço idêntico entre jogos; 3/3, 3/3, 5/6 nos testados).
  Exceção: Seb (LB #1) adapta execução (35–66% idêntico).

## Novidades / segredos capturados (2026-08-15)

### Balance change 1.32.7 (PR #1399, merged 2026-08-15 01:24)
- **Carrot, Tomato, Egg**: demand curve linear → "hinge". Preços spike quando há alta
  shop demand E produção é zero. Demanda legível via `town.unlocked_shops`.
- **Carrot** (T=450, hinge/1.00): $35→$906 no pico (vs linear quase plano).
- **Tomato** (T=200, hinge below, target 0.40): $60→$660 no pico (dias 12+).
- **Egg** (T=332, hinge below, target 0.40): $50→$250 no pico (vs linear $50→$90).
- Ordinary-season prices UNCHANGED (no-op para demanda normal); só diverge no "tail"
  (scarcity extrema). O novo meta pode valorizar agents que flexam produção de
  eggs/tomatoes/carrots quando a demanda shop é alta. **v11 não produce nenhum desses**
  → impacto marginal direto, mas oponentes adaptativos ganham edge.
- Engine local ainda em **1.32.6** (não reflete o change). `pip install
  kaggle-environments==1.32.7` disponível mas exige dependências pesadas (jax, gymnasium,
  open_spiel). Bench local roda em 1.32.6 → resultados válidos para v11 baseline mas
  não para o post-balance meta.

### Leaderboard atual (2026-08-15 23:20)
- #1 **カワシギ 3267.6** (Kaito Fukami, manteve liderança desde 08-12).
- Top-5: Ueddy 3121.3 · Utkarsh #2 3108.3 · Kostiantyn Isaienkov 3088.8 · researchstudio.site 3072.7.
- Muitos players no cluster 3000-3120 (atividade intensa em 13-14/08).
- User rank: **838/4495** equipes. v11 (submetido 15/08 00:06) ainda sem rating real
  (publicScore 600.0 → 913.5 em 3V/0D local; aguardando mais partidas no novo engine).

### Discussões recentes relevantes (2026-08-15)

#### Topic 734000 — "How path dependent is the current leaderboard rating?" (18 votos)
- **Rayk Kretzschmar (EXPERT, rank 329)**: submeteu dois agents byte-identicos 2h apart.
  O primeiro ficou ~1700, o segundo subiu >3000. Gap de 1400 pontos = **matchmaking luck**
  (seeds, posições de jogador, ordem de resultados iniciais), NÃO qualidade do agente.
- **Early losses = climbing extremamente lento**: um loss inicial no seeding define uma
  trajetória de rating que é difícil de reverter mesmo com win streak.
- **Stale agents do engine antigo (1.32.6−) ainda no pool de matchmaking** — agentes
  que jogaram no engine anterior continuam sendo emparelhados. Pós-1.32.7, estes agentes
  podem ser mais fáceis ou mais difíceis dependendo do que eles fazem.
- **Relevante para nós**: v11 caiu de 913.5 (3V/0D) → 782 — provavelmente early losses
  contra agentes do novo meta + path dependency. Não necessariamente indica que v11 é pior.

#### Topic 735209 — "4-players? 8-players?" (staff respondeu: "podia ser follow-up competition")
- Proposta: escalar para 4/8 players. Staff demonstrou interesse. Não afeta a competição atual.

### Kiznaiver (perfil MCP + replay)
- Kaggle: `kiznaiver`, tier CONTRIBUTOR, user_id 12266074.
- Earned "Simulation Competitor" badge 2026-08-05 (entrada tardia na competição).
- **Sem notebooks públicos** (kaggle_search_notebooks: 0 results).
- **Não aparece no top-50 do leaderboard MCP** — possívelmente submetido recentemente
  ou rating ainda se estabilizando. Usuário relata score ~3100 (≈ rank 3-4).
- **Replay local** (seb_episodes/91124143, 2026-08-08): Kiznaiver venceu **Rilen T. L.**
  (nosso agente) 38026 vs 25576 — foi uma derrota real nossa. Score 38026 é abaixo
  do meta atual (84k-155k), sugerindo fase inicial/pre-meta.
- 4 outros replays em `seb_episodes/` (91057328, 91077295, 91138327, 91150561) mostram
  "Seb (allegedly)" = **カワシギ / Kaito Fukami** (#1 LB) vencendo 3/4. Mohamed
  abdelrazik venceu 1/1 vs Seb nesses episódios.

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
| **(🌾) rank-top10-read-the-market-choose-the-farm** (Indar Karhana, 12/08, **66 votes**) | Mixture of estratégias; lê `unlocked_shops` no step 168 → wool vs balanced route |
| **wins-not-money** (destbreso, 15/08) | Vitória depende de market timing, não de moedas absolutas |
| **the-leaderboard-is-a-habitat-gradient** (destbreso, 15/08) | Análise de gradientes de rating no LB |

## Datasets de análise relevantes

| Dataset | Descrição |
|--------|-----------|
| `kaggle/kaggriculture-episodes-*` | Replays oficiais diários (até 2026-08-13); ~31MB cada, full trajectory |
| `kaggle/kaggriculture-episodes-index` | Índice de todos os datasets diários (v16, atualizado 2026-08-15) |
| **georgymamarin/kaggriculture-episodes** (4GB, 39v) | 720-turn bot duels da ladder: `episodes.csv` (team/bank/rating por seat), `replays.parquet` (20MB, todos os replays) |
| **raykkretzschmar/kaggriculture-reference-agents** (MIT, 20v) | 10 agentes como skill ladder (tier 0-9); tiers 6-9 = shared meta line; `cross_team_identity.py` detecta plans compartilhados; Bradley-Terry ranking |
| revanthtambisetty/kaggriculture-top-player-opening-fingerprints | 3 clusters de abertura (v23_fork, sheep_first_hybrid, counter_meta) |

### Cross-reference: CLIST standings (web, snapshot ~2026-08-14)
- #1 カワシギ 3235.7 · #2 researchstudio.site 3160.6 · #3 Furious Monk 3133 · #4 Mohamed 3115.6 ·
  #5 Aaweg 3098.5 · #6 jasonstillchasin 3092.2 · #7 Ak 3085.7 · #8 JALKARNA 3077.1 · #10 Ignat 3061.
- **Kiznaiver não aparece** em nenhum ranking (MCP top-50, CLIST top-10). Possívelmente
  submetido muito recentemente ou usando team name diferente. No replay de 91124143 (08-08),
  Kiznaiver venceu Rilen T. L. 38026 vs 25576 — mas 38k é abaixo do meta atual (84k-155k),
  sugerindo fase inicial.

### Skill ladder (raykkretzschmar reference agents)
- Tiers 0-5: authored agents (~3k a ~53k coins vs starter). Tier 5 "Rancher Rita" (53k) = competente.
- Tiers 6-9: **shared meta line** (~186k coins). Diferem apenas no market layer (sell-ordering).
- **104 teams** aparecem em grupos de plans compartilhados (29/15/8 teams idênticos). Meta convergiu.
- `cross_team_identity.py`: detecta agents clonados do mesmo plano. Útil para identificar
  oponents clonados no nosso matchmaking.

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

1. [x] Leaderboard atual (`kaggle_get_competition_leaderboard`) — 2026-08-15
2. [x] Discussões/queries recentes (`kaggle_list_competition_topics` + `kaggle_get_forum_topic`) — topic 735311 (balance change!), 734212 (Kaito), 735209, 735174
3. [x] Notebooks meta novos (`kaggle_search_notebooks`) — Indar Karhana (66 votos, Top 10)
4. [ ] Writeups de vencedores, se houver — competição ainda em andamento, sem writeup vencedor

### 2026-08-15 — Top meta deep-dive: Kaito V27, Rayk C71, boatlee V16, reference agents

#### Kaito Fukami V27 (`kaitofukami/25-27-strict-future-v27-midgame-meta-reset`, 155 votes)
- **Route source**: Ezzzzzekki (episode 91493566), NOT Nikita (v11's source episódios 92165990/92185587/92223213).
- **Production changes vs V26**: WHEAT 380→360 (less), MILK 218→241 (more), FERTILIZER 245→235 (less), SELL orders 171→168.
- **Market layer**: "SELL-slot price-impact ordering" — only reorders EXISTING SELL slots, never creates new ones. +1 outer win, +819 margin, no production change.
- **No opponent adaptation**: "no opponent name, team ID, submission ID, or private opponent inventory enters runtime."
- **Local eval**: 25/27 strict-future wins vs Top-30 replays. Beats V26 (87/90 LB) 25/27. Beats Kaito V26 14/27→25/27.
- **Engine**: 1.32.6. **No 1.32.7 adaptation** (no egg/tomato/carrot production).
- **Route**: 8 COW by step 192, 4 SHEEP from step 0. Same cow/sheep as v11.

#### Rayk Kretzschmar C71 (`raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta`, 83 votes)
- Educational notebook. Iterated c14 → C94+.
- Uses Kaito's "conditional memory" dataset (v21-1) → suggestive of adaptive logic in top meta.
- Loss fixes: C90-C92 (weed recovery), C93-C94 (opening feed denial + one-turn fertilizer preemption).
- Philosophy: "download current leaders, work out which moves repeat, turn repeatable part into local agent, beat it from both seats."

#### Boatlee V16-RC5 (= v11's source, `boatlee/v16-rc5-high-score-8c-4s-premium-market-lead`, 85 votes)
- Reconstructed from 3 Nikita replays. Claims 60/60 vs core, 24/24 vs Kaito V27/Rayk C71/llcc — but LOCAL sims vs "public executable artifacts", not LB scores.
- Market layer = our "premium market lead": moves premium SELLs (MELON/MILK/STRAWBERRY/WOOL) 1 turn early when no town demand.

#### Reference Agents H2H (kaggle-environments 1.32.7) — DOWNLOADED & TESTED
- Dataset: `raykkretzschmar/kaggriculture-reference-agents` (MIT, downloaded & extracted).
- Tiers 6-9 (shared meta line) play 8C/5S/6STRAWBERRY across 3 quadrants.
- v11 (8C/4S + premium market lead) beats ALL four **20/20** (avg margin +24k to +25k):
  - Broker Bea (T6): 5/5, avg +25,156 | Ledger Lena (T7): 5/5, avg +24,694
  - Slotter Silas (T8): 5/5, avg +24,736 | Closer Cleo (T9): 5/5, avg +24,833
- v11 vs Wheat Walter (baseline): 116k–182k coins (avg ~150k).
- Conclusão: v11's premium market lead é SUPERIOR aos market layers das reference agents (que diferem apenas em SELL reordering).

#### Critical gaps: v11 vs top meta

| Dimensão | v11 (V16-RC5) | Top meta (V27, ref agents) | Gap |
|---|---|---|---|
| **SEED source** | Nikita 55440039 (ep 92165990+) | Ezzzzzekki (ep 91493566) | V27: WHEAT-360/MILK-241/FERT-235 vs Nikita's mix |
| **SHEEP count** | 4 | 5 (ref agents) / 4 (V27) | Ref agents have +1 sheep |
| **Market lead method** | Cria NEW SELL orders (front_run adds to market list up to 10) | V27: reordena SELLs EXISTENTES apenas | v11 risks cash-flow break (see below) |
| **1.32.7 adaptation** | Nenhuma (production: WHEAT/STRAWBERRY/MELON/COW/SHEEP) | Nenhuma (todos usam 1.32.6) | VANTAGEM se adaptar primeiro |
| **Conditional logic** | Zero (pure replay) | C94: feed denial + fertilizer preemption; v21-1: conditional memory | v11 = open-loop, vulnerável a convergent agents |
| **Route length** | 720 actions (full season) | V27: 719 actions (ambos seats) | v11 may have 1 extra step |

#### **Closer Cleo cash-flow warning** (reference agents/manifesto)
- "Sells fund the buys that follow them in the queue; hoist sells out of original slots and BUY_PRODUCT WHEAT later fails on near-zero balance — farm loses more than reordering gained."
- **v11's front_run creates NEW SELL orders** (lines 220-239: `market.append(["SELL", item, quantity])`). This DISPLACES existing orders in the 10-slot queue → SAME cash-flow risk.
- **Fix**: Reorder only existing SELL slots (like V27), or cap new SELLs to after existing BUYs, or ensure sufficient cash reserve.

#### **1.32.7 opportunity** (unexplored by top meta!)
- Carrot/Tomato/Egg "hinge" curves: prices spike 10-70x when shop demand high + production zero.
  - Carrot: $35→$906 (25x), Tomato: $60→$660 (11x), Egg: $50→$250 (5x).
- Neither v11 nor Kaito V27/Rayk/boatlee produce these. **FIRST adapter gains edge**.
- Suggestion: Minimal injection — 1-2 GOOSE tiles when PET_CAFE demand high, or CARROT tiles when FARMERS_MARKET/PET_CAFE demand high.

#### Improvement suggestions (ranked by impact/effort):
1. **[HIGH impact, LOW effort] Market cash-flow fix**: Constrain front_run to not create SELLs that break subsequent BUY ordering. Test: run H2H vs ref agents with cash-flow-aware ordering. Expected: marginal improvement (we already win 20/20).
2. **[HIGH impact, MED effort] Route source swap**: Switch from Nikita's route to Ezzzzzekki's route (Kaito V27's source, ep 91493566). Production mix: WHEAT-360/MILK-241/FERT-235. Test locally: does it beat v11's current route?
3. **[MED impact, MED effort] Meta field plan alignment**: Change 8C/4S → 8C/5S/6STRAWBERRY (match ref agents). The extra SHEEP + 6 strawberry tiles is the meta standard. Local test needed.
4. **[HIGH impact, HIGH effort] 1.32.7 conditional production**: Add GOOSE (egg) or CARROT (tomato) tiles conditionally when town.shop demand is high. Hook into _town_demand_now(). Risk: small plan disruption, but 5-70x price spikes are enormous.
5. **[MED impact, MED effort] Conditional market timing**: Add minimal conditional logic on premium sell batch sizes based on observed town demand state (not full opponent adaptation, since Kago hides opponent private info).

### 2026-08-15 04:58 — FORENSE das 20 derrotas reais do v12 (ref 55519543, 70 jogos → 50W/20L = 71.4%)

**Estado do v12**: publicScore **2318.3** (subiu de 2103.0). Bench 12/12 (~158.5k). 70 episódios públicos analisados.

#### Padrão universal — TODOS os 7 oponentes vencedores (derrotas >5k moedas):
| Métrica | Nós (v12) | Oponentes vencedores |
|---|---|---|
| **1ª venda FERTILIZER** | step 48-49 | **step 43-47** (2-6 steps antes) |
| **1ª venda MILK** | step 233-234 | **step 194-229** (5-40 steps antes!) |
| **SELL orders** | 195 | 207-498 |
| **BUY_ANIMAL** | 6 | 8-11 (Família A) |
| **BUY_SEED** | 59 | 70-108 (Família A) |
| **FERTILIZER vendido** | 300 | 1.735-2.019 (Família A) |
| **WHEAT vendido** | 479 | 1.138-1.465 (Família A) |
| **WHEAT comprado** | 189 | 522-838 (Família A) |

#### Duas famílias de oponentes:
1. **Família A — "High-volume/scaler"** (Shuiys −14.461, Omer −8.082, Beaten_67 −7.426, Héctor −5.753):
   - 9-11 animais, 4 quads, 100+ seeds, 277 hires. FERTILIZER 1.7-2k + WHEAT 1.1-1.4k vendidos (flood).
   - Shed FERTILIZER sempre 0 → vendem tudo imediatamente (free money).
   - 2.5x mais SELL orders (483-498 vs 195).
2. **Família B — "Mesmo farm, market melhor"** (sci-shi −7.271, Jiajun −6.260, TIM −10.336):
   - **Fazenda IDÊNTICA à nossa (8C/4S, mesmos plants)** — edge é 100% timing de mercado.
   - Vender fertilizante no step 47 vs nosso 49, primeiro leite step 194-229 vs nosso 234.
   - 239-246 SELL orders vs 195 → vendas mais granulares, preços melhores (glut curve).
   - sci-shi day 7: money 3.294 vs nossos 156 com a MESMA fazenda → edge decide na 1ª semana.

#### Mecânica FERTILIZER confirmada (engine 1.32.7):
- `COLLECT_FERTILIZER` → +1 FERTILIZER/animal/dia (`fertilizer_available` reset diário).
- `BUY_PRODUCT` permite WHEAT + FERTILIZER. FERTILIZER preço base 100, linear, 493 até floor.
- Shed vazio = vendas imediatas. Flood de SELL orders com qty parcialmente não-realizada ainda
  captura preço (mercado resolve em ordem; 1ª unidade pega melhor preço).

#### Melhorias implementadas nesta sessão (v13):
- **v13 = v12 + FERTILIZER no _FR_ITEMS** (`('MELON','MILK','STRAWBERRY','WOOL','FERTILIZER')`).
  Front-run de 1 turno no fertilizante (sem gate de town demand, free money diário).
- **Validação v13 (1.32.7)**: vs v12 **20/20 (avg +236)** · vs v10 **12/12 (avg +3061)** ·
  vs ref T6-T9 20/20 (~+25k) · stress PASS 20 seeds avg 143.7k, 0 erros.
- Arquivo: `submission_v13.py`. NÃO deployado.

#### Sugestões estratégicas (atualizadas pela forense):
1. **[FEITO → v13]** Front-run de FERTILIZER (captura o timing que TODOS os vencedores usam).
2. **[ALTA] Flood de SELL orders**: aumentar granularidade das vendas (195 → 240+). Os vencedores
   vendem em MUITOS lotes pequenos, capturando melhor preço na glut curve. Vender mais cedo
   fertilizante (step 43-45 vs 48) e leite (step ~220 vs 234).
3. **[ALTA, Família A] Escala de produção**: 9-11 animais + 4 quads + 100 seeds + mais WHEAT
   (522-838 vs 189). Mais animais → mais fertilizante free money + leite/lã. Mudança estrutural
   (nova rota), mas é onde o topo (Beaten_67 145k, Shuiys 128k) está.
4. **[MÉDIA] Antecipar primeira venda de MILK**: rota vende leite no step 234; vencedores no 194-229.
   Milk tem glut rápida (76 unid até floor) → vender cedo = preço melhor.
5. **[MÉDIA] Manter 8C/4S + FERTILIZER front-run** como baseline seguro até testar a escala.
6. **[RESERVADO] Adaptação 1.32.7** (egg/tomato/carrot hinge) — ninguém no topo adaptou ainda.

### 2026-08-15 10:04 — Forense das 33 derrotas do v13 + descoberta do V17 (10C/4S)

**Estado do v13**: publicScore **2238.4** (40W/33L = 54.8% em 73 jogos — win rate menor que v12 mas o rating é path-dependency, não regressão; v13 vence v12 **37/40** localmente).

**Clone Tipo A1 identificado** (kitory −34k, Raef −20k, Artem −13.6k): **6C/12S/18 pastures/3 quads**.
- Assinatura: SELL=473-483, BUY_SEED=101, HIRE=277, ANIMAL=11, LAND=3.
- FERTILIZER 1.735 vendido, WHEAT 1.465 vendido + 838 comprado (vs nossos 300/479/189).
- Vende FERTILIZER step 43 (vs nosso 49), MILK step 194 (vs 234).
- **Confirmado: 0 diffs de farmer/hands entre 3 replays → rota determinística compartilhada**, mas NÃO portável como replay puro (agente tem lógica adaptativa de posição). Tentativa de extração de rota pura falhou (25k vs 160k vs pass).

**Clone Tipo A2** (motemen −12.9k, teraSurfer −9.2k, Scomics −10.5k): 9 animais, LAND=2, FERT 1.906-2.098, WHEAT 1.116-1.138 + 515-522 comprado.

**VENCEDOR DO DIA — boatlee V17-R1-RC2 (10C/4S Market & Storage)**:
- Rota 10 COW / 4 SHEEP, reconstruída do episódio público **92557594** (Kawashigi/MD-family), "twelve public traces".
- Market layer sofisticada: `_V17_MD_MARKETS`/`_V17_R5_MARKETS` overlays que pré-vendem MELON/MILK/STRAWBERRY/WOOL 1-2 turnos antes baseado na assinatura do oponente (COW/SHEEP/quads); `_rank_sell_slots` price-impact; `_v17_room_guard` (hour 21/23 shed capacity); `_terminal_liquidation`; `_repay_shift`.
- Notebook afirma: **138-2/140 (98.6%), média +8.385** vs Kaito V27 (20-0, +10k), MDgogo (20-0), Salem (20-0), BL-V14 (20-0), V16-R6 (18-2).
- SHA-256 `ccf2aefd...`, 49.101 bytes, engine 1.32.6.
- FERTILIZER NÃO está nos front-run items (só MELON/MILK/STRAWBERRY/WOOL) — diferente do nosso v13.

**Validação local do V17 (v14, engine 1.32.7)**:
- **vs v13: 34/40 wins (85%), avg +4.637** (min −4.668, max +13.604).
- vs Reference Agents T6-T9: 20/20, margens 2x maiores (avg +11.5k a +15k).
- vs PASS: ~158-195k; bench 12/12: random 165k, max 204k, sem colapso.
- **submission_v14.py criado** = V17 + aliases agent_fn/main_agent. NÃO deployado ainda.

**Implicação estratégica**: a escala 10C/4S + market overlay por família de oponente é o meta atual. O V17 vence consistentemente os clones A1/A2 que nos derrotavam. Adotar V17 como base é o caminho.

### 2026-08-15 17:45 — Forense derrotas v14 + top-10 replay analysis

**Estado do v14**: publicScore **2305.3** (subiu de 2215.8). 38 jogos: **30W/8L (78.9%)**.

**8 derrotas do v14 analisadas**:
- **Haozhe Wang −20.900** (o maior): 6C/12S + **4 quads** + CARROT/TOMATO/EGG condicionais (100 cada).
  Day 10: 6C/6S; day 14: 6C/10S + 4 quads; compra 839 WHEAT. Termina 106k vs nossos 89k.
- **Benjamin −4.666**: 8C/4S "compacto" melon-first — day 2 = 1C/4S + WHEAT (melão cedo), day 7 money 3.099 vs nossos 966. Terminal liquidation agressiva (26 plants no day 29 vs nossos 17).
- **HealthStone −2.268**: BUY_SEED=158 (mais seeds), CARROT=109, day 1st SELL step 49 (tarde).
- **John Park −1.765, Exposed −1.210, Tran H −1.047, Amer −813, Rômulo −480**: **clones do nosso v14** (mesma assinatura SELL=501-502/ANIMAL=9/FERT=1906/WHEAT=1138) — espelhos perfeitos, decide seed+timing.

**TOP-10 replay analysis (engine 1.32.6 — ninguém adaptou ao 1.32.7)**:
- **Kawashigi #1 (3285), GUGUGAGA #8, Thomas #3 = MESMA rota high-volume 6C/12S + 4 quads**:
  ANIMAL=11, LAND=3, FERT=1.735, WHEAT=1.465+838 comprado, FERT step 43 + MILK step 194.
  Day 10: 6C/6S → day 14: 6C/10S + 4 quads → day 29: 100.5k. É o clone Tipo A1 (kitory) e o Haozhe.
- **Ueddy #5 / Junichiro #6 = TRADER de WHEAT**: SELL WHEAT 4.952-5.037 + BUY 4.927-4.986 (compra barato, vende caro em volume), BUY_SEED=22 (pouco plantio), ANIMAL=8.
- **Egor Trushin (oponente comum em 3 replays) = IDÊNTICO ao nosso v14**: SELL=501, ANIMAL=9, LAND=2, FERT=1906, WHEAT=1138. Confirma que nosso v14 é o "pool" 10C/4S dominante no ladder.

**Notebook "Two Private Bots Beating Meta" (Revanth, 08/09) — 3 clusters de abertura**:
| Cluster | Abertura | ELO ceiling | Estratégia |
|---|---|---|---|
| **v23_fork** (3 top-5) | 5 hires · 2C+2S · 7W/12M seeds | 3117-3131 | = nosso v14/Kawashigi (mesma abertura) |
| **sheep_first_hybrid** (HealthStone) | 3 hires · 1C+4S · 5W/5M | 3132.9 | CARE compounding em ovelhas |
| **counter_meta** (Seb, rank-1) | **14 hires · 3C+2S · 14W/3M** | 3201 | **4 quads + 20 animais**, cash cushion |

**INSIGHT CRÍTICO**: nosso v14 (10C/4S, abertura 2C/2S+WHEAT7+MELON12) é uma variação do **v23_fork com teto de ELO ~3130**. Para passar do teto:
1. **counter_meta (Seb)**: 4 quads + 20 animais (6C/12S+...) + cash cushion no opening. É o que Haozhe/Kawashigi evoluíram.
2. **sheep_first_hybrid (HealthStone)**: CARE compounding em ovelhas com opening 1C/4S.

**Melhorias recomendadas para v15+** (próximo deploy):
1. **[FEITO v15] FERTILIZER no front-run** — já validado (20/20 vs v14, avg +168).
2. **[CRÍTICO] Migrar para rota 6C/12S + 4 quads** (Kawashigi/Haozhe) — o teto do v23_fork exige o 4º quadrante + rebanho maior. Mais ovelhas = mais WHEAT comprado (838 vs 522) + mais fertilizante.
3. **[ALTA] Antecipar MILK step 194** (vs nosso 198) — 4 steps de edge no leite.
4. **[MÉDIA] Adaptação 1.32.7** — nenhum top-10 adaptou; primeiro a adaptar ganha edge.
5. [x] Datasets de análise (`kaggle_search_datasets`) — georgymamarin (4GB, 39v), raykkretzschmar (MIT)
