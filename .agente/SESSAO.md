# SESSAO — Registro da Sessão Atual

> Gerenciado pelos comandos `/iniciar-sessao` e `/finalizar-sessao` (ou `Agente, inicie a sessão` / `Agente, finalize a sessão`).

## Estado da sessão atual

- **Status:** finalizada — deploy v15 efetuado; submissão ativa no LB com publicScore 2327.5 (rank 437)
- **Início:** 2026-08-17 19:50
- **Objetivo:** validar baseline no engine novo (1.32.7), pesquisar novidades (balance change + meta), reavaliar posição do v11 e definir próximos passos.

## Pesquisa MCP desta sessão (17/08) — novidades e segredos descobertos

- **MCP/CLI Kaggle seguem sem credenciais** (`kaggle_authorize` Unauthorized; `~/.kaggle/` vazio;
  API pública 401) → leaderboard, submissões, episódios reais e datasets INDISPONÍVEIS nesta sessão.
  Só discussões (MCP) e webfetch funcionam.
- **Engine local atualizado 1.32.6 → 1.32.7** (pip --no-deps + remoção do dist-info antigo).
  Params confirmados no código: CARROT hinge/1.00/T450 · TOMATO hinge/0.40/T200 · EGG hinge/0.40/T332 · HINGE_GAIN 8.0.
- **Bench v11 no 1.32.7 (12 seeds):** random 163.394 · starter 157.114 · pass 152.202 · Grok 162.911 —
  **12/12 vitórias; sem regressão** (min do random caiu 129k → 109k = tail mais disperso, mediana intocada).
- **Balance change "Small balance change" (735311, PR #1399):** carrot/tomato/egg → curva de escassez
  hinge (preço dispara quadraticamente acima do knee com escassez real). Mediana intocada, p90 ~2x.
  Egg não alcança dinheiro em percentis típicos; melon intocado. Nossa rota 8C/4S não usa esses 3 produtos
  → impacto mínimo. Vencedores não mudam entre builds (0/224).
- **Insights de mercado (nekkon/destbreso/georgymamarin):** drain town/season wheat 525 · strawberry 426 ·
  carrot 327 · milk 327 · tomato 228 · egg 228 · wool 228 · melon 30 · fertilizer 0. Strawberry = maior
  mercado (24x vendido no timing certo). **Fertilizer: gerado por todo animal sobrevivente MESMO sem
  alimentar** (~2.900/season vs 1.300–1.760 dos produtos → pecuária subvalorizada ~3x). Walking é o
  gargalo (83%→55%). Shop draw NÃO é independente do play (trap de benchmark). Objetivo do LB =
  Pr[win]=Φ(μ/σ), não margem.
- **Meta 17/08 (istinetz/Michael Timbs):** topo = linhagem clone da rota pública do Kaito (prerecorded,
  determinística, só flex p/ weeds/sell order). Interatividade limitada → rotas fixas funcionam.
  **Flag hoarding**: times top guardam soluções melhores p/ a última semana (deadline 30/09, new entrant 23/09).
- **Rating path-dependent** (raykkretzschmar): byte-idênticos 1.700 vs 3.000 → não otimizar para rating
  inicial. Stale agents saindo do LB; possível reset pós-deadline.
- **PPO não compete** (5k–22k); hybrid (regras+RL) ~100k. hengck23: BC de replay high-reward (93311715).
- **Greedy scheduler = teto estrutural** (niraberman): 0/N vs tiers 6–9 por ~80–85k → confirma rota determinística.
- **Ablation do market lead (V16-RC5):** remover o front-run (`_FR_ITEMS = ()`) não causou regressão mensurável
  em nenhum teste: 0 diff em 7 seeds vs starter, 7 seeds vs Grok, 22/22 pool contrafactual e 10/12 H2H
  vs v10. Pelo contrário: no bench 1.32.7 a média contra random subiu de 163.394 → 165.181 e o min subiu
  de 109.074 → 144.747 (robustez melhorada). **Conclusão: market lead é código morto no 1.32.7.**
- `submission.py` simplificado em ~120 linhas (removidas `_fr_state`, `_town_demand_now`, `_future_quantity`,
  `_pickup_reserve`, `_existing_sell`, `_repay`, `_front_run`, `_FR_STATE`, `_SHOP_PRODUCTS`). Mantida:
  rota 8C/4S pré-computada + weed repair + align hands.

## Histórico de sessões

### 2026-08-17 21:53 — Encerramento: deploy v15 efetuado + validação contrafactual
- Credenciais Kaggle restauradas (`KGAT_db8619c9138b243aa16188cf21008d7a`); CLI `kaggle` habilitado via wrapper `/usr/local/bin/kaggle`.
- Leaderboard verificado: Rilen T. L. rank 437, publicScore 2334.6.
- Replays reais do v15 baixados (10 episódios) e do v11 (18 episódios). Análise:
  - v15: win rate 7W/3L (70%), bancos avg ~70k, min 37k, max 101k. Derrotas por margens pequenas.
  - v11: win rate 9W/6L (60%), bancos avg 106k, min 40k, max 165k. Derrotas por margens grandes (até -23k).
- Kernel `boatlee/v17-r1-rc2-high-score-10c-4s-market-storage` baixado; v15 reconstruído (V17-R1-RC2 + FERTILIZER front-run: `_PREEMPT_ENABLED=True`, FERTILIZER em `_PREMIUM`, janela 80–700).
- Bench v15: 12/8 vitórias, avg ~157k–166k. Smoke test: 142.540 vs starter.
- `submission.py` atualizado para v15; snapshot em `submission_v15.py`.
- **Validação contrafactual v15 (33 replays × 2 seats = 76 jogos): 65/76 vitórias (85.5%), margem média +35.293.**
- Submissão v15 no LB: ref 55588852 (pending), ref 55578757 (publicScore 2334.6, rank 437).
- Push para main efetuado (commits f331e8a + 00de4c0). GitHub auth OK.

### 2026-08-17 19:50 — Início de sessão: baseline 1.32.7 + balance change hinge
- Engine local atualizado para **1.32.7** (balance change "Small balance change" 15/08: CARROT/TOMATO/EGG
  → curva hinge de escassez). Params confirmados no código local.
- Bench v11 no 1.32.7: random 163.394 · starter 157.114 · pass 152.202 · Grok 162.911 — 12/12, sem regressão.
- Pesquisa MCP concluída: balance change (mediana intocada, p90 ~2x; egg não alcança dinheiro; melon intocado;
  0/224 vencedores mudam), insights de mercado (drain da town, fertilizer sem alimentar, shop draw trap,
  Pr[win]=Φ(μ/σ)), meta "clone do Kaito" + flag hoarding, rating path-dependent, PPO/greedy confirmam rota fixa.
- Credenciais Kaggle continuam indisponíveis → leaderboard/submissões/derrotas do v11 não verificáveis agora.

### 2026-08-15 00:30 — Encerramento: v10 8V/2D (1896.5) + v11 3V/0D (913.5)
- v10 real completo: 8V/2D (80%), rating 600 → 1896.5; derrotas por margens mínimas (−2.184, −1.144).
- v11 (V16-RC5) submetido 00:06; 3V/0D reais (99–153k), rating 913.5. Sem derrotas até agora.
- Docs atualizadas (VERDADE/HISTORICO/SESSAO); commits 4c53f02, a3b96a5, 9714b37, 72bd71a em main.

### 2026-08-14 — Monitoramento v10 (4V/0D) + v11 (V16-RC5) adotado
- v10 real: 4V/0D, bancos 83–157k (incl. vitória vs payoon 111k → 156.907).
- V16-RC5 (boatlee) e adaptive-farming (tetsutani) extraídos; H2H local: v11 vs v10 = 38-10 (48 jogos).
- v11 validado: pool 13/14 (+83.579) · stress 20 seeds 149k avg · bench 150–163k.
- submission.py = GranjaAgent v11; snapshots submission_v11.py / submission_v10.py. Aguardando deploy.

### 2026-08-14 — Migração v10 (pecuária open-loop) concluída, validada e submetida
- submission.py = GranjaAgent v10 (C95 extraído + docstring + aliases); snapshot submission_v10.py.
- Validação: bench local 146–158k (3.6x v7) · head-to-head 8-0 vs v7 · pool contrafactual 13/14 (+81.886) ·
  stress 20 seeds zero erros · seeds aleatórios DONE/DONE.
- Farm final: 9 COW + 4 SHEEP + 10 hands + NE+NW+SW = 158.448 (meta modal exata).
- **Submetido 2026-08-14 22:58 → publicScore 600.0 (novo máximo histórico; v7 505.0, A.9 539.6).**
- Commit 4c53f02 + push para main.

### 2026-08-14 — Análise de partidas reais v7 (1V/6D) + meta pecuária + C95 extraído
- Replays reais do v7 analisados (7 episódios): 1V/6D; oponentes top fazem 147–160k.
- Engine 1.32.6 confirmado = replays oficiais; fertilizar melão é desperdício; WHEAT precisa de fertilizante.
- Meta live (Furina): modal 9C/4S+1WHEAT · 10–12 mãos · NE+NW+SW · 84k mediano / 155k max.
- Agente C95 extraído do findings → `/tmp/kilo/c95_main.py`; vence v7 6-0 local (77–178k vs 26–33k).
- 6 notebooks meta novos baixados para `/tmp/kilo/meta/`.
- Decisão: migrar para rota open-loop de pecuária no próximo submission.py.

### 2026-08-11 — Sessão inicial (organização + sistema .agente)
- Configuração do sistema `.agente/` (VERDADE, REGRAS_DE_OURO, HISTORICO, INTEL, SESSAO), comandos `/iniciar-sessao` e `/finalizar-sessao`, agente `agente`, limpeza de 80+ arquivos obsoletos.
- GranjaAgent v2 é a versão corrente (drop de animais, fazenda densa, MELON max).
- Bench validado: 35.4k–39k média local.
