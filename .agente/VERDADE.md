# VERDADE — Estado Atual do Projeto (Kaggriculture)

> Fonte da verdade do agente. **SEMPRE atualizar este arquivo** no início e fim de cada sessão.
> Última atualização: 2026-08-15 23:20 (sessão iniciada — bench validado, pesquisa MCP completa, repo reestruturado)

> ⚠️ ATENÇÃO (2026-08-15): repo reestruturado — `submission.py` (v11), `bench.py`,
> `bench_pool.py`, etc. agora em `kaggriculture/`. Engine local = 1.32.6 mas o
> Kaggle já atualizou para **1.32.7** (balance change PR #1399: carrot/tomato/egg
> "hinge" demand curves → preços spike com alta shop demand + zero production).
> O bench local roda em 1.32.6 e NÃO reflete essa mudança. v11 não planta
> eggs/tomatoes/carrots → impacto marginal no nosso agente, mas oponentes que se
> adaptarem ganham edge. Recomendado atualizar local para 1.32.7.

## 1. Versão deployada e score

| Campo | Valor |
|-------|-------|
| Agente ativo | **GranjaAgent v15** (`submission.py`, v14 + FERTILIZER front-run) — **preparado, deploy agendado 16/08** (limite diário de 5 atingido 15/08) |
| Estratégia | Rota determinística 8 COW + 4 SHEEP (Nikita 55440039) + NE+NW+SW + market layer com leitura da demanda do TOWN + front-run 1 turno nas vendas premium + weed repair + terminal |
| Score local (12 seeds) | **158.5k média** (1.32.7): random 152.8k · starter 157.1k · pass 152.2k · Grok 162.9k — 12/12 wins vs todos |
| Partidas REAIS do v10 (10 episódios 14–15/08) | **8V/2D (80%)** — bancos 63k–157k; derrotas por margens mínimas (−2.184, −1.144) |
   - **Partidas REAIS do v11** (ref 55516028, submetido 15/08 00:06): **public_score 2075.5**
     (600 → 913.5 → 2075.5; rating subindo, mas ainda abaixo do top-50 LB que fica ~2886+).
   - **Partidas REAIS do v10** (ref 55514882, submetido 14/08 22:58): public_score **1996.7**
     (600 → 1896.5 → 1996.7). |
| Head-to-head local v11 vs v10 | **38-10** (48 jogos, 24 seeds × 2 seats) — market lead vence confronto direto da meta |
| Pool contrafactual v11 (7 replays reais × 2 seats = 14 jogos) | **13/14 vitórias, margem média +83.579** |
| Stress test (20 seeds vs pass) | média ~149k · min 101k · max 190k · zero erros |
| Último submission Kaggle | **Jairo/SimpleBrain (2026-08-15 16:19, ref 55531757, score 253.5 — DEPLOY ACIDENTAL, NÃO afeta leaderboard)** |
| Skill rating Kaggle | **v14 = 2299.0** (ref 55529953, rank 590) · v13 = 2245.6 · v12 = 2286.7 · **leaderboard usa o melhor score = v14** | |
| v11 H2H vs Reference Agents (1.32.7, 5 seeds) | **20/20 wins** vs T6-T9 meta-line agents. avg margin +24k–25k. v11 premium market lead > their SELL-reorder layers. |
| v11 vs Wheat Walter (baseline) | 116k–182k coins, avg ~150k (1.32.7) |
| **v12 (DEPLOYADO 15/08 03:56, ref 55519543, AGORA SUBSTITUÍDO)** | v11 + cash-flow fix no front-run. **vs v11: 20/20 (avg +292)** · vs ref T6-T9: 20/20 (~+25k) · **publicScore 2309.9** (70 jogos: 50W/20L = 71.4%). Backup em `submission_v12_deployed.py`. |
| **v15 (candidato validado, NÃO deployado)** | v14 + FERTILIZER nos 3 front-run sets (_PREMIUM/_V17_R5_ITEMS/_V17_MD_ITEMS). **vs v14: 20/20 (avg +168, min +153, max +183)** · vs ref T6-T9: 20/20 · stress PASS 30 seeds: idêntico ao v14 (154.9k, 0 erros). Em `submission_v15.py`. Deploy adiado — guardando 1ª submissão de 16/08. |
| **v14 (DEPLOYADO 2026-08-15 14:43, ref 55529953)** | V17-R1-RC2 boatlee (10C/4S, rota episódio 92557594) + market overlays MD/R5 + room guard + terminal liquidation + aliases. **vs v13: 34/40 (85%, avg +4.637)** · vs ref T6-T9: 20/20 (+11.5k-15k) · bench 12/12 (random 165k, max 204k) · **partidas reais: 30W/8L (78.9%)**, publicScore 2305.3. Em `submission_v14.py`. Backup do v13 em `submission_v13_deployed.py`. |
| **v13 (DEPLOYADO 15/08 08:23, ref 55523374, AGORA SUBSTITUÍDO)** | v12 + FERTILIZER no _FR_ITEMS. **vs v12: 37/40 (avg +208)** · **publicScore 2246.9** (40W/33L). |

**Veredito da sessão 14/08**: o v7 (melão-puro) estava OBSOLETO vs a meta de pecuária
determinística (84k mediano / 160k max). O **v10** (C95) foi submetido → 600.0. A análise
posterior encontrou o **v11** (V16-RC5, market lead do boatlee) que vence o v10 38-10 no
H2H local — adotado como submission.py, aguardando deploy.

## 2. Código

- `kaggriculture/submission.py` — agente principal (**GranjaAgent v14** = V17-R1-RC2 10C/4S boatlee).
  Contém aliases `agent`, `agent_fn`, `main_agent`.
- `kaggriculture/submission_v13_deployed.py` — backup do v13 que estava em produção antes do v14.
- `kaggriculture/submission_v14.py` — snapshot do v14 (fonte: `ref_agents/v17_main.py` do boatlee).
- `kaggriculture/submission_v15.py` — candidato v15 (v14 + FERTILIZER front-run), validado, não deployado.
- `kaggriculture/submission_v10.py` — snapshot do v10 (C95, substituído; teve 4V/0D reais e publicScore 600.0).
- `kaggriculture/submission_v7.py` — snapshot do v7 (melão-puro, substituído).
- `kaggriculture/bench.py` — benchmark local (12 seeds vs random/starter/pass/Grok). Uso: `python3 bench.py submission.py` (rodar de `kaggriculture/`).
- `kaggriculture/bench_replay.py` — contrafatorial strict-future de 1 replay (2 seats).
- `kaggriculture/bench_pool.py` — pool de replays × 2 seats (win rate + margem por oponentte real). Régua de aceite.
- `kaggriculture/replay_agent.py` — reproduz ações de um replay oficial por seat (índice k+1; seed em `info.seed`).
- `kaggriculture/submission_v3.py`–`submission_v9.py` — experimentos documentados.
- `kaggriculture/submission_by_grok.py`, `kaggriculture/simulate_local.py`, `kaggriculture/analyze_replay.py` — análise/oponente.
- **Origem do v11:** V16-RC5 do kernel `boatlee/v16-rc5-high-score-8c-4s-premium-market-lead`
  (rota 8C/4S reconstruída dos replays de Nikita Lugovoy, submission 55440039).
- **Origem do v10:** C95 do kernel `raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta`.

## 3. Regras de ouro consolidadas (detalhe em `REGRAS_DE_OURO.md`)

> ⚠️ ATENÇÃO (14/08): as regras 1–3 foram validadas na arquitetura REATIVA frágil (v1–v7)
> e ainda valem para ela. MAS a meta provou que PECUÁRIA DETERMINÍSTICA open-loop rende
> 3–5x mais. A nova diretriz: **migrar para rota open-loop** (C95/V16-RC5) — ver §9.

1. **Melão é o motor de dinheiro confiável** — maximize tiles de MELÃO (válido p/ reativo; obsoleto vs meta).
2. **Fazenda DENSA em 2 quadrants** vence espalhar em 4 (válido p/ reativo; topo usa NE+NW+SW com rota).
3. **Motor de animais é volatilidade** — REATIVO colapsa (fuga em 2 dias sem feed); open-loop não.
4. **Mão de obra contratada é barata e essencial** — nunca deixar colapsar; teto `4+min(4,day//5)` (v7); topo: 10–14 mãos com rota.
5. **Mercado: venda consciente** com cap por turno + liquidação total day≥27.
6. **Confiabilidade > complexidade** — floor alto ganha rating, não teto.
7. **Armadilhas já pisadas** — ver `REGRAS_DE_OURO.md` §7.

## 4. Parâmetros-chave do GranjaAgent v7

```python
TARGET_COOPS = 0            # animais DROPADOS
TARGET_PASTURES = 0
WHEAT_TARGET = 12
STRAWBERRY_TARGET = 10
MELON_TARGET = 24           # v7: melão cedo + volume (era 18 no v2)
PLANT_DEADLINE = {"MELON": 18, "STRAWBERRY": 21, "TOMATO": 19, "CARROT": 25, "WHEAT": 27}
LIQUIDATE_DAY = 27
# Hire: 4 + min(4, day//5)  (até 8 mãos)
# Land: só NE (quads 1→2), BUY_LAND se money >= 1600
# Seeds: WHEAT=10, STRAWBERRY=5, MELON=8 (estoque); venda cap MELON≤15/turno
# _choose_plant: MELON primeiro, depois STRAWBERRY, depois WHEAT (v2 plantava o menor déficit)
```

## 5. Como rodar validação local (RITUAL)

```bash
cd kaggriculture
python3 bench.py submission.py
```

- No Windows/local: `kaggle_environments` já está no path (1.32.6) — PYTHONPATH não necessário.
- 12 seeds vs random/starter/pass/Grok. Linha de base atual: média ~155-163k (v11).
- Pool real (30 jogos contrafactuais): `python3 bench_pool.py submission.py <replays_dir>`.
- Se média cair < 30k ou houver episódio de colapso → STOP e debugar antes de qualquer deploy.

## 6. Roteiro de deploy

```bash
export PYTHONPATH=/home/rtl/.local/lib/python3.14/site-packages
export KAGGLE_API_TOKEN=$(cat ~/.kaggle/access_token)
python3 -m kaggle competitions submit -c kaggriculture -f submission.py -m "<MSG>"
python3 -m kaggle competitions submissions -c kaggriculture
```

## 7. Armadilhas de ambiente

- `kaggle` CLI não está no PATH; usar `python3 -m kaggle` com `PYTHONPATH` + `KAGGLE_API_TOKEN`.
- `kaggle_environments` instalado em `/home/rtl/.local/lib/python3.14/site-packages` (precisa de `PYTHONPATH`).
- Python do sistema é 3.14; usar o mesmo PYTHONPATH para bench.
- Replays brutos em `replays/`; análises antigas (v15–v18) em `archive/analise_v15_v18/`. (`perdi/` removido em 2026-08-12.)

## 8. Controle de sessão

- Iniciar: ler `.agente/` → atualizar VERDADE → rodar bench → **pesquisa MCP (busca/relatório/chave-de-ouro)** para descobrir novidades e segredos de oponentes → registrar em `SESSAO.md`.
- Finalizar: resumir descobertas → atualizar `HISTORICO.md` e `VERDADE.md` → registrar em `SESSAO.md`.

## 9. META ATUAL E ENGINE — confirmados em 14/08 (engine local 1.32.6 = replays oficiais)

### Engine (constantes reais, `kaggle_environments/envs/kaggriculture/kaggriculture.py`)
- **ATUALIZADO LOCAL PARA 1.32.7** (2026-08-15). Engine oficial = 1.32.6 → 1.32.7 (PR #1399).
- MELON: seed 80, max_yield **6**, max_yield_day **12**, janela bônus de rega dias **6–12**;
  começa yield=1, +1/dia regado (ou +2 com fertilizante); cap 6 atingido ~dia 10 só com rega.
  → **FERTILIZAR MELÃO É DESPERDÍCIO**; prioridade é garantir rega nos dias 6–10.
- WHEAT: max_yield 6 — **NÃO atinge cap só com rega; precisa de fertilizante**.
- STRAWBERRY: max_yield 4, colhe a cada 2 dias (interval 2) — late-game earner.
- ANIMAIS: GOOSE 300/COOP (ovo d4, int 1) · COW 400/PASTURE (leite d8, int 2) · SHEEP 500/PASTURE (lã d6, int 3).
  Cada animal gera **1 fertilizante/dia** (boolean diário) → vender fertilizante = "free money".
- Glut (unid. até floor): MELON ~150 (quadrático) · MILK/WOOL quase tão rápido · WHEAT/EGG ~glut-proof.
- SE (4k) nunca compensa (0% do topo compra); rota topo = NE(1k)+SW(2k) = 3 quads.

### Meta do topo (Elo 3100+, dados 08-11/14)
- **Farm modal: 9 COW + 4 SHEEP + 1 WHEAT · 10–12 mãos · NE+NW+SW** (30% dos players).
- Dinheiro final: **mediano 84.151 · max 154.941** (nós: 27–43k).
- Build order (rota C95/Lev Neganov): d0 = 4 HIRE + 1COW+1SHEEP + sementes WHEAT/MELON + 5 WHEAT;
  d2 vende FERTILIZER; d7–12 HIRE 6–14/dia + 1 COW/dia até 8; d10 BUY_LAND + SELL MELON(5);
  vendas: FERTILIZER diário, MILK d9+ (a cada 2d), WOOL d6+ (a cada 3d), STRAWBERRY d14+.
- Venda metered em batches 4–8 unidades; "quem vende antes no mercado compartilhado pega preço melhor".
- Top players são **hardcoded** (traço de ações idêntico entre jogos) — edge é execução, não replanejamento.
  Exceção: Seb (LB #1) adapta execução (~35–66% idêntico).

### Onde estamos
- v7 = 1/7 vitórias reais; bancos 27–39k vs oponentes 36–160k.
- **v10 (submetido 14/08, ref 55514882):** bench local 146–158k · 13/14 pool (+81.886) ·
  real 8V/2D (80%) · publicScore **1996.7** (600→1896.5→1996.7).
- **v11 (submetido 15/08 00:06, ref 55516028):** H2H vs v10 38-10 · 13/14 pool (+83.579) ·
  stress 20 seeds 149k avg · **publicScore 2075.5** (600→913.5→2075.5; rating subindo,
  ~880 pts abaixo do top-50 LB). Bench 1.32.7: 12/12 wins, ~158.5k média.
- **Kiznaiver** (~3100 rating, rank ~3-4 no LB mas não visível no MCP top-50): venceu nosso
  agente em ep 91124143 (38026 vs 25576, 08/08). Objetivo: fechar gap de ~880 pts para top-20.
- **Path-dependency crítico** (INTEL §734000): agents idênticos divergem 1400+ pts por matchmaking.
  v11 caiu de 913.5→782 temporariamente por early losses; agora em recuperação (2075.5).

### Próximo submission.py (recomendações) — atualizado 2026-08-15
1. **[FEITO] Migrar para rota open-loop de pecuária** (v10 = C95 9C/4S, submetido → 600→1996.7).
2. **[FEITO] Upgrado do market layer** — v11 = V16-RC5 8C/4S + premium market lead (lê demanda do TOWN,
   vende 1 turno antes): vence o v10 38-10 no H2H local. Submetido 15/08 00:06 → publicScore 2075.5.
3. **Monitorar Kiznaiver (~3100)** — venceu nosso agente em 91124143. Observar se seu próximo
   submission incorpora o balance change 1.32.7 (eggs/tomatoes/carrots hedge).
4. **Adaptar-se ao balance change 1.32.7** (carrot/tomato/egg "hinge" curve): agentes que lêem
   `unlocked_shops` e flexam produção (ex: notebook Indar Karhana, 66 votos) ganham edge.
   v11 não produz eggs/tomatoes/carrots → imune ao change direto, mas vulnerável a oponentes adaptados.
5. **Path-dependency**: rating sobe lento após early losses. Agente continua forte (bench 12/12).
   Não reenviar por impulso — coletar mais games e derrotas reais primeiro.
6. Manter `bench_pool.py` como régua de aceite (30 jogos). Atualizar engine local para 1.32.7 ✓.
