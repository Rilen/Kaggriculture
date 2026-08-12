# INTEL — Inteligência sobre Oponentes e Meta (via MCP)

> Alimentado na inicialização de cada sessão com pesquisa MCP (Kaggle): leaderboard,
> discussões, notebooks meta, relatórios de vencedores, datasets de análise.
> Atualizado: 2026-08-11

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

_(Inserir aqui os achados da pesquisa MCP de cada inicialização de sessão, com fonte e data.)_

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
