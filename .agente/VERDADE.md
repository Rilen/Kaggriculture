# VERDADE — Estado Atual do Projeto (Kaggriculture)

> Fonte da verdade do agente. **SEMPRE atualizar este arquivo** no início e fim de cada sessão.
> Última atualização: 2026-08-15 00:30 (encerramento da sessão de migração pecuária open-loop + deploy v11; aguardando derrotas reais do v11)

## 1. Versão deployada e score

| Campo | Valor |
|-------|-------|
| Agente ativo | **GranjaAgent v11** (`submission.py`, V16-RC5 8C/4S + premium market lead) — **substituiu o v10 (C95 9C/4S) em 14/08** |
| Estratégia | Rota determinística 8 COW + 4 SHEEP (Nikita 55440039) + NE+NW+SW + market layer com leitura da demanda do TOWN + front-run 1 turno nas vendas premium + weed repair + terminal |
| Score local (12 seeds, 14/08) | random ~150.7k · starter ~157.1k · pass ~152.2k · Grok ~162.9k |
| Partidas REAIS do v10 (10 episódios 14–15/08) | **8V/2D (80%)** — bancos 63k–157k; derrotas por margens mínimas (−2.184, −1.144) |
| Partidas REAIS do v11 (3 episódios 15/08) | **3V/0D** — bancos 99k–153k (incl. vitória vs oponente de 80k) |
| Head-to-head local v11 vs v10 | **38-10** (48 jogos, 24 seeds × 2 seats) — market lead vence confronto direto da meta |
| Pool contrafactual v11 (7 replays reais × 2 seats = 14 jogos) | **13/14 vitórias, margem média +83.579** |
| Stress test (20 seeds vs pass) | média ~149k · min 101k · max 190k · zero erros |
| Último submission Kaggle | **GranjaAgent v11 (2026-08-15 00:06) — em partidas (rating 913.5)** |
| Skill rating Kaggle | **v10 = 1896.5** (subiu 600.0 → 1896.5 em ~2h) · **v11 = 913.5** (600 → 913.5, 3V/0D) · A.9 = 539.6 · v7 = 505.0 |

**Veredito da sessão 14/08**: o v7 (melão-puro) estava OBSOLETO vs a meta de pecuária
determinística (84k mediano / 160k max). O **v10** (C95) foi submetido → 600.0. A análise
posterior encontrou o **v11** (V16-RC5, market lead do boatlee) que vence o v10 38-10 no
H2H local — adotado como submission.py, aguardando deploy.

## 2. Código

- `submission.py` — agente principal (**GranjaAgent v11** = V16-RC5 8C/4S + premium market lead).
  Contém aliases `agent`, `agent_fn`, `main_agent`.
- `submission_v11.py` — snapshot do v11.
- `submission_v10.py` — snapshot do v10 (C95, substituído; teve 4V/0D reais e publicScore 600.0).
- `submission_v7.py` — snapshot do v7 (melão-puro, substituído).
- `bench.py` — benchmark local (12 seeds vs random/starter/pass/Grok). Uso: `python3 bench.py submission.py`.
- `bench_replay.py` — contrafactual strict-future de 1 replay (2 seats).
- `bench_pool.py` — pool de replays × 2 seats (win rate + margem por oponente). Régua de aceite.
- `replay_agent.py` — reproduz ações de um replay oficial por seat (índice k+1; seed em `info.seed`).
- `submission_v3.py`–`submission_v9.py` — experimentos documentados (v3/v6 refutados; v7 = antigo deploy).
- `simulate_local.py`, `analyze_replay.py`, `submission_by_grok.py` — análise/oponente de referência.
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

- 12 seeds vs random/starter/pass/Grok. Linha de base atual: média ~42k (v7).
- Pool real (30 jogos contrafactuais): `python3 bench_pool.py submission.py /tmp/kilo/top_replays`.
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
- **v10 (submetido 14/08):** bench local 146–158k (3.6x v7) · 13/14 pool (+81.886) ·
  **real 8V/2D (80%) em 10 episódios, rating 600.0 → 1896.5** · derrotas só por margens mínimas.
- **v11 (submetido 15/08 00:06):** H2H vs v10 38-10 (48 jogos) · 13/14 pool (+83.579) ·
  stress 20 seeds média 149k · **real 3V/0D (99–153k), rating 913.5**. Aguardando derrotas p/ análise.

### Próximo submission.py (recomendações)
1. **[FEITO] Migrar para rota open-loop de pecuária** (v10 = C95 9C/4S, submetido → 600.0 → 1787.1 real 8V/2D).
2. **[FEITO] Upgrado do market layer** — v11 = V16-RC5 8C/4S + premium market lead (lê demanda do TOWN,
   vende 1 turno antes): vence o v10 38-10 no H2H local. Submetido 15/08, aguardando rating.
3. FIX no reativo (se mantido): não fertilizar MELON; fertilizar WHEAT/STRAWBERRY; WATER 1º na janela 6–12;
   vender FERTILIZER desde cedo; teto de mãos 10–12; batches pequenos + "premium market lead" (1 turno antes).
4. Manter `bench_pool.py` como régua de aceite (30 jogos).
