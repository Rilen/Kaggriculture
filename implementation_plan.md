# IMPLEMENTATION PLAN: v17.3-A.2 (Semantic Task Claiming)

## User Review Required
Este plano implementa a validação semântica orientada por demanda solicitada para o A.2. 
A arquitetura foi alterada de `target = (x, y)` para `target = (tx, ty, task_name)`.

## Proposed Changes

### [MODIFY] submission_v17_3_a2.py

1. **Alteração na Estrutura do Target**
   - O dicionário `self.worker_targets` passará a armazenar uma tupla `(tx, ty, task_name)`.
   - O conjunto `assigned` rastreará os tiles físicos `(tx, ty)` para evitar colisões entre workers executando tarefas concorrentes. Targets de `RESUPPLY` (Shed) não entram no `assigned` (vários workers podem ir ao Shed).

2. **Nova Função: `validate_task`**
   - Avalia a viabilidade semântica: `validate_task(self, task_name, tx, ty, winv, shed, tile, day, hour)`
   - Retornos possíveis:
     - `VALID`: O worker possui os insumos/condições e o tile é válido.
     - `WAITABLE`: A tarefa requer espera legítima (ex: `HARVEST` de planta que matura em 1 turno, se a estratégia justificar). Para V1, manteremos `INVALID` para não travar workers.
     - `INVALID`: A tarefa é impossível (ex: sem insumo local nem no Shed, tile ocupado, horário passou).
     - `RESUPPLY_REQUIRED`: O worker não possui o insumo (`winv`), mas ele existe no `Shed`.

3. **Demanda Direcionada (RESUPPLY)**
   - O `_move_priorities` deixará de avaliar o `shed` e o `winv`. Ele apenas identificará a "demanda física" do grid (ex: vaca com fome, tile vazio para plantar).
   - Após o BFS encontrar o alvo físico, a validação ocorre. Se retornar `RESUPPLY_REQUIRED`:
     - O target físico muda para as coordenadas do Shed `(sx, sy)`.
     - O `task_name` muda para `RESUPPLY_<ITEM>`.
     - Faz-se um novo BFS em direção ao Shed.
   - Quando o worker chega ao Shed e o `_is_shed_adj` faz o pickup, o `validate_task` avaliará `RESUPPLY_<ITEM>` no turno seguinte. Como o item agora está em `winv`, a task `RESUPPLY` torna-se `INVALID` (pois não é mais necessária). A claim é liberada e o worker busca o alvo real novamente.

4. **Ciclo de Vida do Target (em `worker_act`)**
   - Quando o worker tem um target ativo:
     - Roda `validate_task`.
     - Se `INVALID` -> `del self.worker_targets[worker_id]`.
     - Se `VALID` -> continua viagem.
     - Se `wpos == (tx, ty)` e a ação da task falhar no `_decide` -> `INVALID` (proteção de sanity).
   - O BFS do turno atual só é chamado se o target continuar válido, substituindo o antigo `circuit_breaker` burro.

5. **Ações Produtivas mantidas**
   - A macroeconomia, lógicas de `_decide` (que gera a Ação), `is_shed_adj` e animal flywheel ficarão intactas. 
   - Estamos apenas mudando a "cola" de roteamento (pathing) entre o momento que o worker fica ocioso e o momento que ele começa a se mover.

## Verification Plan

### Automated Tests
1. **Gate B - Sanity Test**: Rodar o agente por 20 turnos isolados para garantir que `validate_task` não gera exceções de Python e que o dicionário `assigned` não quebra com a nova tupla.
2. **Gate C - Smoke Test**: Rodar Seeds 42, 43 e 44 comparando `v17.2`, `v17.3` e `v17.3-A.2`.
3. **Métricas Estritas**: Observaremos se `unproductive_N5` e `target_changes` mantêm melhoria sem sacrificar o `revenue` (fuga do deadlock do A.1). Além disso, extrairemos contagens de `RESUPPLY` triggers e `INVALID` drops.
