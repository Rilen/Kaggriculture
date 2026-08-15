# Histórico de Experimentos — Kaggriculture

Banco de dados histórico para não repetir erros. Cada entrada: estratégia,
o que funcionou, o que regrediu, e métrica (moedas médias locais, 12 seeds,
vs random/starter/pass/Grok-v17; win = 12/12 salvo indicado).

---

## v9 "Masterpiece" (estado inicial no disco)
- BFS + Expansão + Pecuária + Arbitragem + Espionagem + Flush Noturno.
- Score de leaderboard (rating) histórico: ~374.9. Vs random local: ~6.484.
- Problema: frágil vs oponentes reais.

## A.1 – A.16 (trabalho do outro agente, no remoto origin/main A.12)
- Série de tentativas (opening book, crew targets, strawberry expansion, etc).
- Melhores ratings históricos: A.9 ~539.6, A.5 ~537.3, A.13 ~543.7.
- Pior: A.16 = **70.4** (regressão — o agente colapsava: gastava tudo em
  animais que morriam, passava 345 turnos em PASS, regava só 10 vezes).
- Lição: mais features ≠ melhor; regridam fácil sem teste.

## GranjaAgent v1 (primeira reescrita do zero, neste agente)
- Mão de obra contratada + motor trigo→ganso (ovos ~$40 estáveis) + plantio
  paralelo WHEAT/STRAWBERRY/MELON + expansão de terra + venda consciente.
- Corrigiu os 4 bugs do colapso (hire-buffer, navegação p/ vazios, paralelismo
  de plantio, prioridade alimentar).
- Métricas: random ~5.054, starter 7/8 ~4.940, pass ~5.559, Grok-v17 16/16
  ~4.269. Sem colapsos.
- **Head-to-head vs Grok v17: 16/16 vitórias** (média ~4.557 vs ~632).
  O Grok usava vacas/ovelhas (leite/lã) que despencam → perdia feio.

## GranjaAgent v2 (atual — MELHOR)
- Lição-chave de oponente real: bot ocioso de melão (PASS 685/720, 3 melões)
  marcou 5.549 e venceu a v1 (5.105). → Animais = volatilidade; melão =
  motor confiável.
- Mudanças:
  - DROPOU animais (TARGET_COOPS=0, TARGET_PASTURES=0).
  - MELON_TARGET=18, STRAWBERRY_TARGET=10, WHEAT_TARGET=12.
  - Fazenda DENSA em 2 quadrants (só compra NE).
  - Hire: 4 + min(4, day//5) (até 8 mãos).
- Métricas: **random ~37.124, starter ~37.840, pass ~37.928, Grok-v17
  ~39.021** (média 12 seeds). Floor ~30.000. Self-play (guerra de melão):
  ~25k–31k.
- Submetido como GranjaAgent v2.

### Tentativas que REGREDIAM (não repetir)
- Expandir p/ 3º/4º quadrant: ~3.900 (viagem anula ganho).
- Mais mãos (5+min(5,day//4)=10): ~7.710.
- Misturar melão com 12 coops + 18 trigo + land agressivo: ~3.900–5.000
  (animais sem comida + spread).

---

## Sessão 2026-08-12 — pesquisa de meta + harness contrafactual + série v3→v9

### Infraestrutura nova (harness contrafactual "strict-future")
- `replay_agent.py`: reproduz ações de um replay oficial por seat.
- `bench_replay.py`: contrafactual de 1 replay (2 seats). `bench_pool.py`: pool de
  15 replays × 2 seats = **30 jogos**, com win rate + margem por oponente real.
- Descobertas: o seed real fica em `info.seed` (não `configuration.seed`); o replay
  oficial usa `steps[N]={estado pós-ação N, ação N}` enquanto o env local usa
  `steps[N]={estado pós-ação N-1, ação N-1}` → indexação `k+1` reproduz exatamente.

### Linha de base (v2) no pool real (30 jogos)
- v2 = **1/30 vitórias, margem média −101k**. Perde para TODOS (top-5 e casuais,
  que fazem 60–160k vs nossos 20–30k).
- Meta do Top-5: abertura v23_fork (1C+4S ou 2C+2S + HIRE) e **rotas open-loop de
  719–720 ações** pré-computadas (Kaito Fukami v27 clona rota do Ezzzzzekki).

### Experimentos v3→v9 (bench local + pool)
| v | mudança | bench local | pool margem |
|---|---|---|---|
| v3 | abertura animais 2C+2S | ~4,7k (colapso) | — |
| v4 | front-run melão/morango | ~38,4k (neutro) | — |
| v5 | staged land conservador | ~36,3k (regressão) | — |
| v6 | pecuária alta densidade | ~1k (colapso, fluxo PLACE quebrado) | — |
| v7 | melão cedo + volume (24) | **~42,5k (+12%)** | −105k |
| v8 | v7 + mãos teto 12 | ~40,3k | **−86,5k** |
| v9 | v8 + 3º quadrante | ~38,4k (viagem) | −86k |

- Lições: (a) melão cedo+volume = **+12% moedas**; (b) mais mãos = melhor margem
  no pool (pressão de mercado derruba preço dos oponentes) mas pior vs passivos;
  (c) 3º quadrante = neutro/piora (regra de ouro #2 confirmada); (d) pecuária
  REATIVA colapsa (fuga em 2 dias sem feed; fluxo PICKUP→PLACE quebrado) — só
  rota open-loop determinística funciona, como no topo.
- Conclusão: teto desta arquitetura ~42k moedas / −86k margem, ainda 0/30 vs real.
  Fechar o gap exige reescrever o motor (open-loop), não patches.

### Submissão
- **GranjaAgent v7** (melão cedo + volume) submetido 2026-08-12 (melhor em moedas).

---

## Sessão 2026-08-14 (continuação) — GranjaAgent v10: migração para pecuária open-loop

### Decisão executada
- **submission.py = GranjaAgent v10** (base C95 extraído do findings + docstring + aliases
  `agent_fn`/`main_agent`/`c94_submission_agent`). Snapshot em `submission_v10.py`.
- O v10 já embute todos os guards recomendados: weed repair (3 camadas), front-run de mercado
  (1 turno), DROP antes de SELL (shed logistics da rota), terminal liquidation, feed-first.

### Validação local (engine 1.32.6 = replays oficiais)
| Régua | v7 (melão-puro) | **v10 (pecuária open-loop)** |
|---|---|---|
| Bench local (12 seeds) | ~41.7–43.4k | **~146.5–157.8k (3.6x)** |
| Head-to-head vs v7 (4 seeds × 2 seats) | 0-8 | **8-0** (77–160k vs 27–32k) |
| Pool contrafactual (7 replays reais × 2 seats) | 4/14 · −33.834 | **13/14 · +81.886** |
| Stress 20 seeds vs pass | — | média 143k · min 103k · max 178k · 0 erros |
| Seeds aleatórios (3 jogos) | — | 115–155k, DONE/DONE |

### Farm final da rota (seed 42)
- 9 COW + 4 SHEEP + 1 empty pasture · 10 hands · NE+NW+SW · 158.448 moedas (meta modal exata).

### Submissão e resultado
- **GranjaAgent v10 submetido 2026-08-14 22:58 → publicScore 600.0 (NOVO MÁXIMO histórico).**
  v7 era 505.0; A.9 (antigo máximo) 539.6; topo do leaderboard 3264.3.

---

## Sessão 2026-08-14 (continuação) — v11 (V16-RC5 8C/4S + premium market lead)

### Monitoramento do v10 (4 episódios reais 14/08 23:00–23:14)
- **4V/0D** — bancos 83.224–156.907: vitória fácil vs passivo (127k vs 3k), vs pecuária mal executada
  (83k vs 21k), vs 12 vacas+3 ovelhas (118k vs 25k), e **vs oponente forte (payoon: 11 vacas + 8 ovelhas +
  13 mãos, 111.485) → 156.907** (liderança do dia 5 ao 30).
- O v10 já opera no nível de bancos da meta (83–157k vs meta 84–155k).

### Monitoramento completo do v10 (10 episódios reais 14–15/08) — 8V/2D (80%)
- Vitórias 63–157k; derrotas por margens mínimas: −2.184 (Sky kun) e −1.144 (KiKi).
- **Rating: 600.0 → 1787.1 em ~1h de partidas reais** (subiu 600 → 1748 → 1787 conforme jogos acumulam).
- Confirma: o v10/C95 vence consistentemente a meta real; as derrotas são apertadas (timing de mercado).

### Descoberta: V16-RC5 vence o C95 no H2H local
- Extraídos os agentes públicos da meta: **V16-RC5** (boatlee, `/tmp/kilo/v16_rc5_main.py`) e
  **adaptive-farming** (tetsutani, `/tmp/kilo/tetsu_main.py`).
- Head-to-head local (24 seeds × 2 seats = 48 jogos): **v11/V16-RC5 vs v10/C95 = 38-10** (~79% win).
  Motivo: market layer do V16 lê a demanda do TOWN e vende 1 turno antes (front-run) → no confronto
  direto da meta, quem vende antes pega preço melhor e derruba o preço do outro.
- Réguas das demais (V16 vs C95): pool contrafactual 13/14 (+83.579 vs +81.886) · stress 20 seeds
  média 149k · bench local ~150–163k. Tetsu ficou no meio (4-4 vs C95 no 1º lote).

### Adoção
- **submission.py = GranjaAgent v11** (V16-RC5 + docstring + aliases); snapshot `submission_v11.py`;
  `submission_v10.py` preserva o C95.
- **v11 submetido 2026-08-15 00:06 → publicScore 600.0 inicial; aguardando partidas reais.**

---

## Sessão 2026-08-14 — Partidas reais do v7 (1V/6D) + meta pecuária + agente C95 extraído

### Partidas reais do v7 (7 episódios 13–14/08) — 1V/6D
- Vitória 39.476 (oponente fraco: 12 mãos + animais mal executados = 19.289).
- Derrotas apertadas 34.104–34.514 (oponentes 36–50k: 5 vacas + morango + SW).
- Esmagamentos 30.238–30.383 (oponentes **147.936–160.285** = pecuária completa da meta).
- Nossos bancos reais: 27,8k–39,5k (bench local vs passivos dá 42k — o real é mais duro).
- publicScore da submissão v7: **505.0** (vs A.9 máx 539.6; topo do LB 3264).

### Engine 1.32.6 confirmado (código local = replays oficiais module_version 1.32.6)
- MELON max_yield **6** / max_yield_day **12** / janela rega 6–12 / cap 6 só com rega
  → **FERTILIZAR MELÃO É DESPERDÍCIO** (nosso código fertilizava!); guardar p/ WHEAT (max 6 exige fert).
- STRAWBERRY max_yield 4 interval 2; animal = 1 FERTILIZER/dia vendável ("free money").
- Glut: MELON ~150un (quadrático); MILK/WOOL quase tão rápidos; WHEAT/EGG ~glut-proof.
- SE (4k) nunca compensa; topo usa NE+NW+SW (1k+2k).

### Meta atual (live-meta Furina, dados 08-11; Elo 3100+)
- Modal farm: **9 COW + 4 SHEEP + 1 WHEAT · 10–12 mãos · NE+NW+SW** (30% dos players).
- Dinheiro: mediano 84.151 / max 154.941 (nós 27–43k → gap 2–4x).
- Sell rhythm: FERT d4 · MELON d10 · MILK d11 · STRAW d15 · WHEAT d8 · WOOL d6; batches 4–15.
- Build order C95 (Lev Neganov ep 91587143): d0 4H+1C+1S+seeds+5W; d2 SELL FERT; d7–12 HIRE 6–14/dia
  +1 COW/dia; d10 BUY_LAND + SELL MELON 5; FERT diário, MILK d9+, WOOL d6+, STRAW d14+.

### Head-to-head local (régua nova)
- **C95 (topo extraído) vs v7 = 6-0** (77–178k vs 26–33k); C95 vs starter ~127k (v7 ~42k) → ~3x.
- C95 roda sem erros em seeds novos. `/tmp/kilo/c95_main.py` = base candidata do próximo submission.

### Lições para o próximo submission.py
1. **Migrar para pecuária open-loop** (8C/4S ou 9C/4S): rota C95/V16-RC5 + guards (WEED repair, FEED
   first, DROP antes de SELL, liquidar fim); validar no `bench_pool.py` (30 jogos).
2. Se manter reativo: FIXs — não fertilizar MELON; WATER 1º janela 6–12; vender FERT cedo;
   mãos 10–12; batches pequenos + "premium market lead" (1 turno antes).
3. Bench local vs passivos NÃO mede o real (oponentes reais fazem 36–160k); usar head-to-head
   com C95/V16 e pool contrafactual como régua.

---

## Roteiro de teste local (reprodutível)
```bash
pip install kaggle-environments --no-deps   # pygame falha, mas env roda
python3 bench.py submission.py              # 12 seeds vs random/starter/pass/Grok
python3 -c "from kaggle_environments import make; \
env=make('kaggriculture', configuration={'episodeSteps':720,'seed':1}); \
env.run(['submission.py','starter']); print([round(s['reward'],1) for s in env.steps[-1]])"
```
- Baixar replay de episódio real:
  `kaggle competitions episodes <SUBMISSION_ID>` → pegar id →
  `kaggle competitions replay <EPISODE_ID> -p ./replays`
- Estudar oponente: contar tiles/animais/dinheiro por dia e ações (ver
  `analyze_replay.py`).

## Oponentes no leaderboard (rating, não moedas)
- Topo 14/08: **カワシギ 3264.3** · Ueddy 3116.0 · researchstudio.site 3110.2 · Utkarsh #2 3098.7 ·
  somewhere after 3092.6 · Mohamed abdelrazik 3086.1. Kaito Fukami saiu do topo.
- Rating reflete vitórias/derrotas, não moedas; moedas altas → vitórias → rating alto.
- MCP Kaggle não autenticado nesta máquina; usar Kaggle CLI + env local + replays.
