# VERDADE — Estado Atual do Projeto (Kaggriculture)

> Fonte da verdade do agente. **SEMPRE atualizar este arquivo** no início e fim de cada sessão.
> Última atualização: 2026-08-17 (sessão final: deploy v15 — V17-R1-RC2 10C/4S + FERTILIZER front-run)

## 1. Versão deployada e score

| Campo | Valor |
|-------|-------|
| Agente ativo | **GranjaAgent v15** (`submission.py`, V17-R1-RC2 10C/4S + FERTILIZER front-run — preempt habilitado p/ FERTILIZER nos sets 80–700) |
| Estratégia | Rota determinística 10 COW + 4 SHEEP (ep 92557594, boatlee V17-R1-RC2) + NE+NW+SW + weed repair + room guard + terminal liquidation + FERTILIZER front-run (vende 2–6 steps antes da demanda). |
| Score local (12 seeds, 17/08, engine 1.32.7) | random ~157.1k · starter ~158.4k · pass ~156.1k · Grok ~166.5k (12/8 vitórias; min 102.675) |
| Score local (12 seeds, 17/08, engine 1.32.7, v11 simplificado) | random ~165.2k · starter ~157.1k · pass ~152.2k · Grok ~162.9k (12/12 vitórias; min do random subiu p/ 144.7k = robustez melhorada) |
| Score local (12 seeds, 17/08, engine 1.32.7, v11 original) | random ~163.4k · starter ~157.1k · pass ~152.2k · Grok ~162.9k (12/12 vitórias; min do random 109.1k) |
| Score local (12 seeds, 14/08, engine 1.32.6) | random ~150.7k · starter ~157.1k · pass ~152.2k · Grok ~162.9k |
| Partidas REAIS do v10 (10 episódios 14–15/08) | **8V/2D (80%)** — bancos 63k–157k; derrotas por margens mínimas (−2.184, −1.144) |
| Partidas REAIS do v11 (3 episódios 15/08) | **3V/0D** — bancos 99k–153k (incl. vitória vs oponente de 80k) |
| Head-to-head local v11 vs v10 | **38-10** (48 jogos, 24 seeds × 2 seats) — market lead vence confronto direto da meta |
| Pool contrafactual v11 (7 replays reais × 2 seats = 14 jogos) | **13/14 vitórias, margem média +83.579** |
| Pool contrafactual v15 (33 replays reais × 2 seats = 76 jogos) | **65/76 vitórias (85.5%), margem média +35.293** |
| Stress test (20 seeds vs pass) | média ~149k · min 101k · max 190k · zero erros |
| Último submission Kaggle | **GranjaAgent v15 (2026-08-18 00:46) — pending (anterior 17/08 12:57 = publicScore 2334.6, rank 437)** |
| Skill rating Kaggle | **v15 = 2334.6** (submetido 17/08 12:57, rank 437) · **v11 = 2117.0** (submetido 15/08 00:06, rating 913.5) · v10 = 1977.9 · v7 = 505.0 |

**Veredito da sessão 14/08**: o v7 (melão-puro) estava OBSOLETO vs a meta de pecuária
determinística (84k mediano / 160k max). O **v10** (C95) foi submetido → 600.0. A análise
posterior encontrou o **v11** (V16-RC5, market lead do boatlee) que vence o v10 38-10 no
H2H local — adotado como submission.py, aguardando deploy.

## 2. Código

- `submission.py` — agente principal (**GranjaAgent v15** = V17-R1-RC2 10C/4S + FERTILIZER front-run). Contém aliases `agent`, `agent_fn`, `main_agent`.
- `submission_v15.py` — snapshot do v15 (submissão ativa, publicScore 2334.6).
- `submission_v11_clean.py` — snapshot do v11 simplificado (market lead removido por ablation).
- `submission_v11.py` — snapshot do v11 original (V16-RC5 8C/4S + premium market lead).
- `submission_v10.py` — snapshot do v10 (C95, substituído; teve 4V/0D reais e publicScore 600.0).
- `submission_v7.py` — snapshot do v7 (melão-puro, substituído).
- `bench.py` — benchmark local (12 seeds vs random/starter/pass/Grok). Uso: `python3 bench.py submission.py`.
- `bench_replay.py` — contrafactual strict-future de 1 replay (2 seats).
- `bench_pool.py` — pool de replays × 2 seats (win rate + margem por oponente). Régua de aceite.
- `replay_agent.py` — reproduz ações de um replay oficial por seat (índice k+1; seed em `info.seed`).
- `submission_v3.py`–`submission_v9.py` — experimentos documentados (v3/v6 refutados; v7 = antigo deploy).
- `simulate_local.py`, `analyze_replay.py`, `submission_by_grok.py` — análise/oponente de referência.
- **Origem do v15:** `/tmp/kilo/v17_rc2/main_v17_rc2.py` — V17-R1-RC2 do kernel `boatlee/v17-r1-rc2-high-score-10c-4s-market-storage` (rota 10C/4S reconstruída dos replays de boatlee, episode 92557594) + FERTILIZER front-run (`_PREEMPT_ENABLED=True`, FERTILIZER em `_PREMIUM`, janela 80–700).
- **Origem do v11:** `/tmp/kilo/v16_rc5_main.py` — V16-RC5 do kernel `boatlee/v16-rc5-high-score-8c-4s-premium-market-lead`
  (rota 8C/4S reconstruída dos replays de Nikita Lugovoy, submission 55440039).
- **Origem do v10:** `/tmp/kilo/c95_main.py` — C95 do kernel `raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta`.

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
export PYTHONPATH=/home/rtl/.local/lib/python3.14/site-packages
python3 bench.py submission.py
```

- 12 seeds vs random/starter/pass/Grok. Linha de base atual (v11, 1.32.7): média ~159k.
- Pool real (30 jogos contrafactuais): `python3 bench_pool.py submission.py /tmp/kilo/top_replays`.
- Se média cair < 30k ou houver episódio de colapso → STOP e debugar antes de qualquer deploy.
- ⚠️ Engine local já está em **1.32.7** (balance change de 15/08) — replays antigos (1.32.6) continuam
  válidos p/ contrafactual (destbreso: 0/224 vencedores mudam trocando o build), mas bancos podem variar.

## 6. Roteiro de deploy

```bash
export PYTHONPATH=/home/rtl/.local/lib/python3.14/site-packages
export KAGGLE_API_TOKEN=$(cat ~/.kaggle/access_token)
python3 -m kaggle competitions submit -c kaggriculture -f submission.py -m "<MSG>"
python3 -m kaggle competitions submissions -c kaggriculture
```

## 7. Armadilhas de ambiente

- `kaggle` CLI não está no PATH; usar `python3 -m kaggle` com `PYTHONPATH` + `KAGGLE_API_TOKEN`.
- ⚠️ (17/08) **Sem credenciais nesta máquina**: `~/.kaggle/` vazio e MCP Kaggle Unauthenticated →
  leaderboard/submissões/episódios reais INDISPONÍVEIS via API. Só pesquisa de discussões/webfetch funcionam.
- `kaggle_environments` instalado em `/home/rtl/.local/lib/python3.14/site-packages` (precisa de `PYTHONPATH`).
- Atualizar o engine: `python3 -m pip install --upgrade --no-deps --target=... kaggle-environments` (pygame falha
  sem `--no-deps`); remover o `.dist-info` antigo se o `importlib.metadata` continuar pegando a versão velha.
- Python do sistema é 3.14; usar o mesmo PYTHONPATH para bench.
- Replays brutos em `replays/`; análises antigas (v15–v18) em `archive/analise_v15_v18/`. (`perdi/` removido em 2026-08-12.)

## 8. Controle de sessão

- Iniciar: ler `.agente/` → atualizar VERDADE → rodar bench → **pesquisa MCP (busca/relatório/chave-de-ouro)** para descobrir novidades e segredos de oponentes → registrar em `SESSAO.md`.
- Finalizar: resumir descobertas → atualizar `HISTORICO.md` e `VERDADE.md` → registrar em `SESSAO.md`.

## 9. META ATUAL E ENGINE — confirmados em 17/08 (engine local **1.32.7** = replays oficiais atuais)

### Engine 1.32.7 (atualizado 17/08; balance change "Small balance change" 15/08 = PR #1399)
- **BALANCE CHANGE (1.32.7)**: CARROT, TOMATO e EGG tiveram a curva de escassez (scarcity side) trocada de
  linear → **hinge**: `f(x) = u + 8·max(0, u−1)²` com u=x/T (HINGE_GAIN=8.0). Abaixo do knee (T) é
  bit-idêntico à linear antiga; acima do knee sobe QUADRATICAMENTE (preço dispara com escassez real).
  - CARROT: hinge, below_target **1.00** (era 0.20 — mudança NÃO anunciada!), T=450
  - TOMATO: hinge, below_target 0.40, T=200
  - EGG: hinge, below_target 0.40, T=332
  - Frequência de disparo (sem produção): tomato 50% dos jogos · carrot 26% · egg 22% (medido: 55/28/26%).
  - Jogos medianos quase intocados (mediana da scarcity fica logo abaixo do knee); tail abre (p90 ~2x).
  - **EGG não alcança dinheiro em percentis típicos** (1.00x mediana, 1.06x p90) → geese seguem inviáveis.
  - **MELON intocado**: em 0 de 8 menus de shop, demanda 30/season, knee 300 → scarcity jamais alcança.
  - Vencedores não mudam entre builds (destbreso: 0/224); bancos variam (dispersão, não expectativa).
- MELON: seed 80, max_yield **6**, max_yield_day **12**, janela bônus de rega dias **6–12**;
  começa yield=1, +1/dia regado (ou +2 com fertilizante); cap 6 atingido ~dia 10 só com rega.
  → **FERTILIZAR MELÃO É DESPERDÍCIO**; prioridade é garantir rega nos dias 6–10.
- WHEAT: max_yield 6 — **NÃO atinge cap só com rega; precisa de fertilizante**.
- STRAWBERRY: max_yield 4, colhe a cada 2 dias (interval 2) — late-game earner.
- ANIMAIS: GOOSE 300/COOP (ovo d4, int 1) · COW 400/PASTURE (leite d8, int 2) · SHEEP 500/PASTURE (lã d6, int 3).
  Cada animal gera **1 fertilizante/dia** (boolean diário) → vender fertilizante = "free money".
- **FERTILIZER (confirmado 17/08)**: `_daily_refresh_animals` seta `fertilizer_available=True` em TODO animal
  sobrevivente **mesmo sem alimentar**, e não acumula → stream vale ~2.900/season vs 1.300–1.760 dos produtos
  → pecuária subvalorizada ~3x quando se conta só leite/lã/ovo. Glut branch ~$98/un (sem town drain).
- Drain da TOWN por season (medição nekkon/destbreso, 1.32.7): wheat 525 · strawberry 426 · carrot 327 ·
  milk 327 · tomato 228 · egg 228 · wool 228 · melon 30 · fertilizer 0. Strawberry = maior mercado, vale 24x
  vendido no timing certo (melhor para VENDER, mediano para CULTIVAR).
- Glut (unid. até floor): MELON ~150 (quadrático) · MILK/WOOL quase tão rápido · WHEAT/EGG ~glut-proof.
- SE (4k) nunca compensa (0% do topo compra); rota topo = NE(1k)+SW(2k) = 3 quads.
- Shop draw NÃO é independente do play (trap de benchmark): mesma seed, bots diferentes → shops diferentes;
  editar seu próprio bot mantém a town como controle (muda em ~1/12 seeds).

### Meta do topo (Elo 3100+, dados 08-11/14; confirmado ainda atual em 17/08)
- **Farm modal: 9 COW + 4 SHEEP + 1 WHEAT · 10–12 mãos · NE+NW+SW** (30% dos players).
- Dinheiro final: **mediano 84.151 · max 154.941** (nós: 27–43k).
- Build order (rota C95/Lev Neganov): d0 = 4 HIRE + 1COW+1SHEEP + sementes WHEAT/MELON + 5 WHEAT;
  d2 vende FERTILIZER; d7–12 HIRE 6–14/dia + 1 COW/dia até 8; d10 BUY_LAND + SELL MELON(5);
  vendas: FERTILIZER diário, MILK d9+ (a cada 2d), WOOL d6+ (a cada 3d), STRAWBERRY d14+.
- Venda metered em batches 4–8 unidades; "quem vende antes no mercado compartilhado pega preço melhor".
- Top players são **hardcoded** (traço de ações idêntico entre jogos) — edge é execução, não replanejamento.
  Exceção: Seb (LB #1) adapta execução (~35–66% idêntico).
- 17/08: topo = **linhagem clone da rota pública do Kaito** (prerecorded, determinística, só flex p/ weeds e
  sell order). Interatividade limitada → rotas fixas funcionam. **Flag hoarding**: times top guardam soluções
  melhores p/ a última semana → meta pode evoluir até o deadline (30/09; new entrant 23/09).

### Onde estamos
- v7 = 1/7 vitórias reais; bancos 27–39k vs oponentes 36–160k.
- **v10 (submetido 14/08):** bench local 146–158k (3.6x v7) · 13/14 pool (+81.886) ·
  **real 8V/2D (80%) em 10 episódios, rating 600.0 → 1896.5** · derrotas só por margens mínimas.
- **v11 (submetido 15/08 00:06):** H2H vs v10 38-10 (48 jogos) · 13/14 pool (+83.579) ·
  stress 20 seeds média 149k · bench 1.32.7 ~152–163k (12/12) · **real 3V/0D (99–153k), rating 913.5**.
- **v15 (submetido 17/08 12:57):** V17-R1-RC2 10C/4S + FERTILIZER front-run (`_PREEMPT_ENABLED=True`,
  FERTILIZER em `_PREMIUM`, janela 80–700). Bench 1.32.7 ~157–166k (12/8) · reconstruído do kernel
  `boatlee/v17-r1-rc2-high-score-10c-4s-market-storage` (ep 92557594). Submissão ativa no LB:
  **publicScore 2334.6, rank 437**.
- Análise real do v11 (18 episódios): win rate 60% (9W/6L), bancos avg 106k, min 40.989, max 164.982.
  Derrotas por margens grandes associadas a vendas massivas de WHEAT no final.
- Análise real do v15 (10 episódios): win rate 70% (7W/3L), bancos avg ~70k, min 37.283, max 101.026.
  Derrotas por margens menores (−281 a −5.428). Prioriza consistência (baixa variância).

### Próximo submission.py (recomendações)
1. **[FEITO] Migrar para rota open-loop de pecuária** (v10 = C95 9C/4S, submetido → 600.0 → 1787.1 real 8V/2D).
2. **[FEITO/DESCARTADO] Market lead do V16-RC5** — ablation provou que não contribui mensuravelmente no 1.32.7
    (0 diff em 7 seeds vs starter/Grok, 22/22 pool, 10/12 H2H vs v10). Removido do `submission.py` em 17/08.
    A vantagem do v11 sobre o v10 vem da rota 8C/4S, não do market layer.
3. **[FEITO] Adotar V17-R1-RC2 10C/4S + FERTILIZER front-run como v15** — reconstruído do kernel público do boatlee,
    preempt habilitado p/ FERTILIZER. Submetido 17/08 12:57 → publicScore 2334.6, rank 437.
4. **[FEITO] Validar v15 no pool contrafactual** — 33 replays reais × 2 seats = 76 jogos: 65/76 vitórias (85.5%),
    margem média +35.293. Derrotas por margens pequenas (menos de 6k).
5. Manter `bench_pool.py` como régua de aceite (30 jogos).
