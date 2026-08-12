# VERDADE — Estado Atual do Projeto (Kaggriculture)

> Fonte da verdade do agente. **SEMPRE atualizar este arquivo** no início e fim de cada sessão.
> Última atualização: 2026-08-11 21:59 (sessão de organização encerrada; GranjaAgent v2 corrente)

## 1. Versão deployada e score

| Campo | Valor |
|-------|-------|
| Agente ativo | **GranjaAgent v2** (`submission.py`) |
| Estratégia | Fazenda DENSA em 2 quadrants, 100% plantação (sem animais), MELON como motor de dinheiro |
| Score local (12 seeds) | random ~37.124 · starter ~37.840 · pass ~37.928 · Grok-v17 ~39.021 |
| Floor local | ~30.000 (sem colapsos) |
| Último submission Kaggle | GranjaAgent v2 (2026-08-11) |
| Skill rating Kaggle | A.9 = 637.0 (máx histórico) · A.14 = 261.1 (regressão, arquivado) |

## 2. Código

- `submission.py` — agente principal (GranjaAgent v2). Contém aliases `agent`, `agent_fn`, `main_agent`.
- `bench.py` — benchmark local (12 seeds vs random/starter/pass/Grok). Uso: `python3 bench.py submission.py`.
- `simulate_local.py` — simulação offline sobre replays gravados (não re-executa a engine).
- `analyze_replay.py` — análise de replays de oponentes.
- `submission_by_grok.py` — oponente de referência (Grok v17) usado no bench.

## 3. Regras de ouro consolidadas (detalhe em `REGRAS_DE_OURO.md`)

1. **Melão é o motor de dinheiro confiável** — maximize tiles de MELÃO.
2. **Fazenda DENSA em 2 quadrants** vence espalhar em 4 (viagem anula ganho).
3. **Motor de animais é volatilidade** — fora do Granja (GOLDEN: só ganso se usar).
4. **Mão de obra contratada é barata e essencial** — nunca deixar colapsar; teto `4+min(4,day//5)`.
5. **Mercado: venda consciente** com cap por turno + liquidação total day≥27.
6. **Confiabilidade > complexidade** — floor alto ganha rating, não teto.
7. **Armadilhas já pisadas** — ver `REGRAS_DE_OURO.md` §7.

## 4. Parâmetros-chave do GranjaAgent v2

```python
TARGET_COOPS = 0            # animais DROPADOS
TARGET_PASTURES = 0
WHEAT_TARGET = 12
STRAWBERRY_TARGET = 10
MELON_TARGET = 18
PLANT_DEADLINE = {"MELON": 18, "STRAWBERRY": 21, "TOMATO": 19, "CARROT": 25, "WHEAT": 27}
LIQUIDATE_DAY = 27
# Hire: 4 + min(4, day//5)  (até 8 mãos)
# Land: só NE (quads 1→2), BUY_LAND se money >= 1600
# Seeds: WHEAT=10, STRAWBERRY=5, MELON=4 (estoque); venda cap MELON≤15/turno
```

## 5. Como rodar validação local (RITUAL)

```bash
export PYTHONPATH=/home/rtl/.local/lib/python3.14/site-packages
python3 bench.py submission.py
```

- 12 seeds vs random/starter/pass/Grok. Linha de base atual: média ~37–39k.
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
- Replays brutos em `replays/`; derrotas em `perdi/`; análises antigas (v15–v18) em `archive/analise_v15_v18/`.

## 8. Controle de sessão

- Iniciar: ler `.agente/` → atualizar VERDADE → rodar bench → **pesquisa MCP (busca/relatório/chave-de-ouro)** para descobrir novidades e segredos de oponentes → registrar em `SESSAO.md`.
- Finalizar: resumir descobertas → atualizar `HISTORICO.md` e `VERDADE.md` → registrar em `SESSAO.md`.
