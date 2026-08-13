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
- Topo ~3.030–3.217 (Kaito Fukami 3217 em 2026-08-11). Rating reflete
  vitórias/derrotas, não moedas; moedas altas → vitórias → rating alto.
- Não há MCP "kaggriculture" configurado; usar Kaggle CLI + env local + replays.
