# VERDADE — Estado Atual do Projeto (Kaggriculture)

> Fonte da verdade do agente. **SEMPRE atualizar este arquivo** no início e fim de cada sessão.
> Última atualização: 2026-08-14 (sessão de análise de partidas reais v7 + estudo de meta; decisão: migrar p/ pecuária open-loop)

## 1. Versão deployada e score

| Campo | Valor |
|-------|-------|
| Agente ativo | **GranjaAgent v10** (`submission.py`, rota open-loop de pecuária) — **substituiu o v7 (melão-puro) em 14/08** |
| Estratégia | Rota determinística (Lev Neganov) 9 COW + 4 SHEEP + 1-2 WHEAT + 10 mãos + NE+NW+SW + controller c17/c27 + weed repair + C94 (feed5 opening + split de vendas) |
| Score local (12 seeds, 14/08) | random ~157.772 · starter ~157.066 · pass ~146.464 · Grok ~157.040 (**3.6x o v7**) |
| Partidas REAIS do v7 (7 episódios 13–14/08) | 1V/6D — bancos 27.800–39.476; oponentes 36k–160k (linha de base ANTES da migração) |
| Head-to-head local v10 vs v7 | **8-0** (v10: 77k–160k vs v7: 27–32k) |
| Pool contrafactual v10 (7 replays reais × 2 seats = 14 jogos) | **13/14 vitórias, margem média +81.886** (v7: 4/14, −33.834) |
| Stress test (20 seeds vs pass) | média ~143k · min 103k · max 178k · zero erros/colapsos |
| Último submission Kaggle | **GranjaAgent v10 (2026-08-14 22:58) — publicScore 600.0 (NOVO MÁXIMO histórico)** |
| Skill rating Kaggle | **v10 = 600.0 (máx histórico)** · A.9 = 539.6 · v7 = 505.0 · A.16 = 70.4 (regressão) |

**Veredito da sessão 14/08**: o v7 (melão-puro) estava OBSOLETO vs a meta de pecuária
determinística (84k mediano / 160k max). O **v10** (C95 extraído + docstring/aliases) foi
adotado como submission.py e supera a régua de aceite: 13/14 no pool contrafactual.

## 2. Código

- `submission.py` — agente principal (**GranjaAgent v10** = rota open-loop de pecuária, base C95).
  Contém aliases `agent`, `agent_fn`, `main_agent`, `c94_submission_agent`.
- `submission_v10.py` — snapshot do v10 (cópia de submission.py).
- `submission_v7.py` — snapshot do v7 (melão-puro, substituído).
- `bench.py` — benchmark local (12 seeds vs random/starter/pass/Grok). Uso: `python3 bench.py submission.py`.
- `bench_replay.py` — contrafactual strict-future de 1 replay (2 seats).
- `bench_pool.py` — pool de replays × 2 seats (win rate + margem por oponente). Régua de aceite.
- `replay_agent.py` — reproduz ações de um replay oficial por seat (índice k+1; seed em `info.seed`).
- `submission_v3.py`–`submission_v9.py` — experimentos documentados (v3/v6 refutados; v7 = antigo deploy).
- `simulate_local.py`, `analyze_replay.py`, `submission_by_grok.py` — análise/oponente de referência.
- **Origem do v10:** `/tmp/kilo/c95_main.py` — agente topo C95 extraído do kernel
  `raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta` (rota Lev Neganov + controller c17/c27).

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
- **v10 (deployado como submission.py em 14/08):** bench local 146–158k (3.6x v7) · head-to-head 8-0 vs v7 ·
  13/14 no pool contrafactual (+81.886) · stress 20 seeds sem erros.
- **Submetido 2026-08-14 22:58 → publicScore 600.0 (NOVO MÁXIMO histórico; v7 era 505.0, A.9 539.6).**

### Próximo submission.py (recomendações)
1. **[FEITO] Migrar para rota open-loop de pecuária** (9C/4S): submission.py = v10 (C95 + aliases),
   validado no `bench_pool.py` (13/14 nos replays reais) e submetido (publicScore 600.0 = máx histórico).
2. FIX no reativo (se mantido): não fertilizar MELON; fertilizar WHEAT/STRAWBERRY; WATER 1º na janela 6–12;
   vender FERTILIZER desde cedo; teto de mãos 10–12; batches pequenos + "premium market lead" (1 turno antes).
3. Manter `bench_pool.py` como régua de aceite (30 jogos).
