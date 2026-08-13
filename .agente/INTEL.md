# INTEL — Inteligência sobre Oponentes e Meta (via MCP)

> Alimentado na inicialização de cada sessão com pesquisa MCP (Kaggle): leaderboard,
> discussões, notebooks meta, relatórios de vencedores, datasets de análise.
> Atualizado: 2026-08-12

## Resumo executivo

- Topo do leaderboard (2026-08-11): ~3.030–3.217 (Kaito Fukami 3217).
- Rating reflete vitórias/derrotas, não moedas. Moedas altas → vitórias → rating alto.
- Lição-chave de oponente real: bot ocioso de melão (PASS 685/720, 3 melões) marcou 5.549
  e venceu um agente complexo de 5.105 → **floor alto > teto sem chão**.

## Notebooks meta baixados (`.agente/intel/kernels/`)

| Kernel | Tese |
|--------|------|
| findings-from-zero-to-top-meta | Meta de estratégia do zero ao topo |
| strawberry-pays-24x-what-the-price-table-says | Morango rende 24x o preço tabelado |
| weedproof-clone-market | Clone de mercado à prova de mato |
| dual-market-relay | Relé de mercado duplo |
| easy-bronse-in-lb-2628-2 | Bronze fácil no LB |

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
