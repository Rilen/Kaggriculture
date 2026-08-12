---
description: "Inicia sessão de desenvolvimento Kaggriculture: atualiza VERDADE, roda bench e pesquisa MCP por novidades/segredos de oponentes"
agent: agente
---
Você está iniciando uma **sessão de desenvolvimento** da Kaggriculture. Siga o protocolo abaixo EXATAMENTE nesta ordem:

## 1. Atualizar a VERDADE
- Leia `.agente/VERDADE.md`, `.agente/REGRAS_DE_OURO.md`, `.agente/HISTORICO.md` e `.agente/INTEL.md`.
- Verifique `git log --oneline -5` e `git status` para saber o estado atual.
- Confirme qual versão do `submission.py` está no disco e se há alterações não commitadas.
- Atualize `.agente/VERDADE.md` (campo "Última atualização" e versão corrente).

## 2. Validar baseline local
- Rode o bench rápido: `PYTHONPATH=/home/rtl/.local/lib/python3.14/site-packages python3 bench.py submission.py`.
- Compare a média com a linha de base em VERDADE (§5). Se caiu < 30k ou colapsou, pare e reporte antes de continuar.

## 3. Pesquisa MCP — novidades e segredos para combater oponentes
- Execute a "busca relatório chave de ouro" via MCP Kaggle (use o checklist de `.agente/INTEL.md`):
  1. Leaderboard: `kaggle_get_competition_leaderboard` em kaggriculture.
  2. Discussões recentes: `kaggle_list_competition_topics` (sortBy Recent) e abra tópicos promissores com `kaggle_get_forum_topic`.
  3. Notebooks meta: `kaggle_search_notebooks` filtrado pela competição.
  4. Writeups de vencedores: `kaggle_list_hackathon_write_ups` / `kaggle_get_writeup_by_slug`.
  5. Datasets de análise: `kaggle_search_datasets` (ex.: "kaggriculture").
- Se algum achado mudar a meta (novo oponente dominante, novo segredo de estratégia), registre em `.agente/INTEL.md` e, se aplicável, sugira ajuste em `VERDADE.md`/`REGRAS_DE_OURO.md`.

## 4. Registrar a sessão
- Preencha `.agente/SESSAO.md`: status "ativa", data/hora, objetivo (peça ao usuário se não foi dado), achados MCP.

## 5. Relatório
- Responda em PORTUGUÊS com: (a) versão corrente + estado git; (b) resultado do bench (média vs baseline); (c) principais novidades/segredos da pesquisa MCP com fontes; (d) sugestão de foco para a sessão.
