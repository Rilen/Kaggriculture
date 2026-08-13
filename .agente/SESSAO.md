# SESSAO — Registro da Sessão Atual

> Gerenciado pelos comandos `/iniciar-sessao` e `/finalizar-sessao` (ou `Agente, inicie a sessão` / `Agente, finalize a sessão`).

## Estado da sessão atual

- **Status:** encerrada
- **Início:** 2026-08-12 (pesquisa de meta + experimentos v3–v9)
- **Fim:** 2026-08-12 21:18
- **Objetivo:** Analisar o perfil/meta do Top-5 (Kaito Fukami e outros), construir harness contrafactual (strict-future) e rodar a série v3→v9 para fechar o gap de receita.

## Pesquisa MCP — novidades e segredos descobertos

- Líder **Kaito Fukami** (@kaitofukami, EXPERT, Financial Engineering Group/Tóquio): notebook v27 "25/27 Strict-Future" = rota open-loop de 719 ações clonada do Ezzzzzekki + sparse controller. Método: derrota real → 1 falha → challengers → freeze → janela futura.
- Meta do Top-5: abertura **v23_fork** (1C+4S+5H ou 2C+2S) — 26/30 times convergiram; edge está na CONTINUAÇÃO, não na abertura.
- Balance change 06/08 (engine ≥1.32.6): TC compra 1x/dia; shops com reposição → mercado mais sensível a glut.
- Avaliação final: torneio único **Bradley-Terry** após o deadline.
- Detalhe completo em `INTEL.md`.

## O que foi feito nesta sessão

- **Harness contrafactual:** `replay_agent.py` + `bench_replay.py` + `bench_pool.py` (15 replays × 2 seats = 30 jogos). Seed real em `info.seed`; indexação `k+1` reproduz exato.
- **Linha de base:** v2 = 1/30 vitórias, margem média −101k no pool real (topo 60–160k).
- **Experimentos v3→v9:** v3/v6 pecuária = colapso; v4 front-run = neutro; v5 staged land = regressão; **v7 melão cedo+volume = +12% (~42,5k)**; v8 +mãos = melhor margem (−86k); v9 +3º quad = neutro.
- **Submissão:** GranjaAgent **v7** submetido 2026-08-12.
- **Limpeza:** `perdi/` removido; `.gitignore` refinado (removidos globais `*.json/*.csv`; mantidos dados pesados).

## Resultados / métricas

- Bench local v7 (12 seeds): random **43.137** · starter **41.670** · pass **41.810** · Grok **43.387** (v2 ~37,9k → **+12%**).
- Pool real v7: 0/30, margem −105k. Melhor margem: v8 (−86,5k).
- Conclusão: teto da arquitetura ~42k moedas / −86k margem; gap 3–7× vs topo exige reescrever o motor (open-loop).

## Decisões e próximos passos

1. Deploy corrente: **GranjaAgent v7**. Monitorar rating pós-deploy.
2. Próximo passo estrutural: clonar/gerar rota open-loop (v23) validada no `bench_pool.py` (30 jogos).
3. Manter `bench_pool.py` como régua de aceite de qualquer mudança futura.

---

## Histórico de sessões

### 2026-08-12 — Pesquisa de meta + harness contrafactual + série v3→v9
- Perfil do líder Kaito Fukami e meta v23_fork documentados em INTEL.md.
- Harness contrafactual (replay_agent/bench_replay/bench_pool) com 30 jogos; linha de base v2 = 1/30, −101k.
- Experimentos v3–v9; v7 (melão cedo + volume, +12%) submetido. v3/v6 refutados.
- `perdi/` removido; `.gitignore` refinado; commit + push no GitHub.

### 2026-08-11 — Sessão inicial (organização + sistema .agente)
- Configuração do sistema `.agente/` (VERDADE, REGRAS_DE_OURO, HISTORICO, INTEL, SESSAO), comandos `/iniciar-sessao` e `/finalizar-sessao`, agente `agente`, limpeza de 80+ arquivos obsoletos.
- GranjaAgent v2 é a versão corrente (drop de animais, fazenda densa, MELON max).
- Bench validado: 35.4k–39k média local.
