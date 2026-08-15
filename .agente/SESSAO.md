# SESSAO — Registro da Sessão Atual

> Gerenciado pelos comandos `/iniciar-sessao` e `/finalizar-sessao` (ou `Agente, inicie a sessão` / `Agente, finalize a sessão`).

## Estado da sessão atual

- **Status:** encerrada (15/08 00:30) — v10 (C95) 8V/2D real (rating 1896.5) + v11 (V16-RC5) deployado com 3V/0D real (rating 913.5); aguardando derrotas do v11 para próxima análise
- **Início:** 2026-08-14 19:28
- **Fim:** 2026-08-15 00:30
- **Objetivo:** Analisar partidas reais do v7 contra oponentes (via MCP/Kaggle CLI), estudar a meta atual e definir o que melhorar no próximo submission.py.

## Monitoramento do v10 (4 episódios reais) + descoberta do v11 (executados nesta sessão)

- **v10 real: 4V/0D** (bancos 83–157k), incluindo vitória sobre oponente forte (payoon 111k → 156.907).
- **v10 real completo (10 episódios): 8V/2D (80%)** — rating 600.0 → **1896.5**; derrotas por margens mínimas.
- **Head-to-head local v11/V16-RC5 vs v10/C95 = 38-10** (48 jogos) — market lead do V16 decide.
- **v11 validado:** pool 13/14 (+83.579) · stress 20 seeds 149k avg · bench local 150–163k.
- **v11 submetido 2026-08-15 00:06; real 3V/0D (99–153k), rating 600 → 913.5.** Aguardando derrotas.
- Farm final (seed 42): 9 COW + 4 SHEEP + 10 hands + NE+NW+SW = 158.448 (meta modal).
- Snapshot: `submission_v11.py` (v11) e `submission_v10.py` (C95).

## Validação do v10 (executada nesta sessão)

| Régua | v7 (melão-puro) | **v10 (pecuária open-loop)** |
|---|---|---|
| Bench local (12 seeds) | ~41.7–43.4k | **~146.5–157.8k (3.6x)** |
| Head-to-head vs v7 (4 seeds × 2 seats) | 0-8 | **8-0** (77–160k vs 27–32k) |
| Pool contrafactual (7 replays reais × 2 seats) | 4/14 · −33.834 | **13/14 · +81.886** |
| Stress 20 seeds vs pass | — | média 143k · min 103k · max 178k · 0 erros |
| Seeds aleatórios (3 jogos) | — | 115–155k, DONE/DONE |

- Farm final (seed 42): 9 COW + 4 SHEEP + 10 hands + NE+NW+SW = 158.448 (meta modal).
- Snapshot em `submission_v10.py`; `submission.py` = v10.

## Pesquisa MCP — novidades e segredos descobertos

- **MCP Kaggle não autenticado nesta máquina** (`kaggle_authorize` → Unauthorized); usei Kaggle CLI + webfetch + engine local (mesma versão dos replays: 1.32.6).
- Leaderboard 14/08: **カワシギ 3264.3** no topo (Kaito Fukami saiu do topo). Nossa submissão v7: publicScore **505.0**.
- 6 notebooks meta NOVOS baixados para `/tmp/kilo/meta/` (live-meta, adaptive-farming, rank-your-agent, structured-economic-policy, boatlee v16, adaptive-replay-agent).
- **Agente topo C95 extraído do findings** → `/tmp/kilo/c95_main.py` (75 KB, rota Lev Neganov + controller c17/c27) — vence v7 **6-0** local.
- Detalhe completo em `INTEL.md`.

## O que foi feito nesta sessão

- **Partidas reais do v7 (7 episódios 13–14/08): 1V/6D.** Vitória 39.476 (oponente fraco 19k);
  derrotas apertadas 34–35k (oponentes 36–50k); esmagamentos 30k vs **147–160k** (pecuária da meta).
- **Engine confirmado (1.32.6 = replays oficiais):** MELON max_yield 6 / max_yield_day 12 → fertilizar
  melão é desperdício; WHEAT precisa de fertilizante; FERTILIZER vendável ("free money"); SE=4k nunca.
- **Head-to-head local:** C95 vs v7 = **6-0** (77–178k vs 26–33k); C95 vs starter ~127k (v7 ~42k) → 3x.
- **Meta (live-meta, dados 08-11):** modal 9C/4S+1WHEAT · 10–12 mãos · NE+NW+SW · 84k mediano / 155k max.
- **Build order C95 documentado:** d0 4H+1C+1S+seeds+5W; d2 SELL FERTILIZER; d7–12 HIRE 6–14/dia +1C/dia;
  d10 BUY_LAND + SELL MELON 5; MILK d9+, WOOL d6+, STRAWBERRY d14+.

## Resultados / métricas

- Bench local v7 (12 seeds, 14/08): random 42.705 · starter 41.670 · pass 41.810 · Grok 43.387.
- v7 real: 1/7 vitórias, bancos 27,8k–39,5k. C95: 77–178k. Meta: 84k mediano / 155k max.
- **Pool contrafactual (7 replays reais × 2 seats = 14 jogos):**
  - v7 = **4/14 vitórias, margem média −33.834**
  - C95 = **13/14 vitórias, margem média +81.886** (+115k vs v7; única derrota −4.3k apertada)
- Conclusão: teto da arquitetura reativa ~42k é ~2–4x abaixo da meta. Fechar o gap exige rota open-loop.

## Decisões e próximos passos

1. **[FEITO] Migrar para pecuária open-loop** (9C/4S): submission.py = v10 (base C95 + aliases),
   validado no `bench_pool.py` (13/14 nos replays reais) e **submetido → publicScore 600.0 (novo máximo)**.
2. **[FEITO] Upgrado do market layer** — v11 = V16-RC5 (8C/4S + premium market lead): vence o v10 38-10
   no H2H local (48 jogos). Adotado como submission.py. Próximo passo: submeter o v11 ao Kaggle.
3. Se mantiver o reativo: FIXs — não fertilizar MELON; WATER 1º na janela 6–12; vender FERTILIZER cedo;
   mãos 10–12; batches pequenos + market lead.
4. Manter `bench_pool.py` como régua de aceite.

## Próximos passos (próxima sessão)

1. **Aguardar derrotas reais do v11** (já tem 3V/0D) — baixar replays das derrotas e analisar o mecanismo de falha.
2. Se o v11 perder para a meta (8C/4S hardcoded), considerar: mesclar market lead do V16 com rota 9C/4S do C95,
   ou adaptação de execução estilo Seb (LB #1) contra oponentes hardcoded.
3. Re-checar a meta (live-meta diário) — a meta evolui rápido (12 mãos é o novo padrão; pode mudar de novo).

---

## Histórico de sessões

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
