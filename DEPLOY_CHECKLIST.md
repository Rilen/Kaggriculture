# A.12 Pre-Deploy Checklist

## ✅ Recomendação 1: Teste em episódios de derrota
- **Status:** CONCLUÍDO
- **Resultado:** PASS reduzido de 34.6% → 12.7% (-21.9pp) nos 7 episódios de derrota
- **Arquivo:** `test_a12_on_losses.py`

## ✅ Recomendação 2: Limitações do simulador
- **Status:** DOCUMENTADO
- **Arquivo:** `simulate_local.py`
- **Limitações:**
  1. Não re-executa o engine do Kaggle
  2. Usa observações gravadas do replay
  3. Score final é o do replay original, não o que nosso agente geraria
  4. Ações do nosso agente não mudam o estado do jogo para steps subsequentes
  5. Útil para comparar distribuição de ações, não score final

## ✅ Recomendação 3: Rollback para A.9
- **Status:** PREPARADO
- **Branch:** `rollback-a9`
- **Commit:** `2100aa4` (A.9 deployed, 637.0)
- **Comando para rollback:**
  ```bash
  git checkout rollback-a9 -- submission.py
  git commit -m "rollback: revert to A.9 (637.0)"
  git push
  ```

## ✅ Recomendação 4: Deploy amanhã
- **Status:** CHECKLIST PRONTO
- **Primeiro submission do dia:** A.12
- **Mensagem:** "A.12: value-first agent — task value scoring, WATER optimization, COLLECT_FERTILIZER gate, aggressive endgame"
- **Comando:**
  ```bash
  python -m kaggle competitions submit -c kaggriculture -f submission.py -m "A.12: value-first agent"
  ```

## ✅ Recomendação 5: Monitoramento pós-deploy
- **Status:** PLANO PRONTO
- **Métricas a monitorar:**
  1. Skill rating delta vs A.9 (637.0)
  2. target_persistence_turns / target_claims
  3. target_changes / target_claims (target churn)
  4. PASS rate em episódios futuros
  5. COLLECT_FERTILIZER frequency
  6. HIRE frequency
  7. Endgame liquidation effectiveness
- **Critérios para A.12b:**
  - Se rating < 600: rollback para A.9
  - Se 600 <= rating < 700: ajustar TASK_VALUE_THRESHOLD
  - Se rating >= 700: manter e iterar

## 📊 Dados de referência

| Versão | Score | PASS Rate | Delta |
|--------|-------|-----------|-------|
| A.9 (deployed) | 637.0 | ~34% (loss episodes) | baseline |
| A.12 (current) | pending | ~12.7% (loss episodes) | -21.9pp |

## 🎯 Próximos passos
1. Amanhã: deploy A.12 primeiro
2. Monitorar rating por 24h
3. Se < 600: rollback para A.9
4. Se 600-700: preparar A.12b com threshold ajustado
5. Se >= 700: manter e estudar novos oponentes
