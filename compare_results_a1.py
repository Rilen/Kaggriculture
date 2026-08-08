import json

with open("replays/v17.2_pathing_forensics.json") as f:
    v2_data = json.load(f)

with open("replays/v17.3_patchA_results.json") as f:
    v3_data = json.load(f)

with open("replays/v17.3_patchA1_results.json") as f:
    a1_data = json.load(f)

def agg(data, key):
    return sum(v.get(key, 0) for v in data.values())

def avg(data, key):
    vals = [v.get(key, 0) for v in data.values()]
    return sum(vals) / len(vals) if vals else 0

v2_score = avg(v2_data, "score")
v3_score = avg(v3_data, "score")
a1_score = avg(a1_data, "score")

v3_unr = agg(v3_data, "claims_released_due_to_unreachable_target")
a1_unr = agg(a1_data, "claims_released_due_to_unreachable_target")

v3_repl = agg(v3_data, "circuit_breaker_triggered")
a1_repl = agg(a1_data, "circuit_breaker_triggered")

v3_tc = agg(v3_data, "target_changes")
a1_tc = agg(a1_data, "target_changes")

v3_col = agg(v3_data, "same_tile_collisions")
a1_col = agg(a1_data, "same_tile_collisions")

v3_unp5 = agg(v3_data, "unproductive_n5")
a1_unp5 = agg(a1_data, "unproductive_n5")

v3_prod = agg(v3_data, "productive_actions")
a1_prod = agg(a1_data, "productive_actions")

v3_rev = agg(v3_data, "total_revenue")
a1_rev = agg(a1_data, "total_revenue")

report = f"""PATCH A.1:
IMPLEMENTADO

V17.2 SCORE:
{v2_score:.1f}
V17.3 SCORE:
{v3_score:.1f}
V17.3-A.1 SCORE:
{a1_score:.1f}

FALSE UNREACHABLE:
V17.3 → {v3_unr}
A.1 → {a1_unr}

REPLANS:
V17.3 → {v3_repl}
A.1 → {a1_repl}

TARGET CHANGES:
V17.3 → {v3_tc}
A.1 → {a1_tc}

COLLISIONS:
V17.3 → {v3_col}
A.1 → {a1_col}

UNPRODUCTIVE N=5:
V17.3 → {v3_unp5}
A.1 → {a1_unp5}

PRODUCTIVE ACTIONS:
V17.3 → {v3_prod}
A.1 → {a1_prod}

REVENUE:
V17.3 → {v3_rev}
A.1 → {a1_rev}

DIAGNÓSTICO:
A alteração eliminou 100% dos "False Unreachable" ({a1_unr}), conforme previsto, mantendo a claim do worker quando ele chega no alvo. No entanto, o score despencou. O motivo foi identificado na simulação: ao remover a invalidação de BFS, o worker agora aguarda indefinidamente em qualquer alvo "válido", mas inútil. Por exemplo, se ele prioriza um tile "EMPTY" para plantar, mas não possui sementes e nem está adjacente ao Shed, o `_decide` retorna `PASS` indefinidamente. Antes (v17.3), o BFS acusava falha por estar em cima do tile, e após 4 turnos o worker soltava o alvo, permitindo que ele voltasse a se mover pelo mapa (ping-pong que acidentalmente fazia-o repor o inventário). No A.1, o worker fica travado num deadlock eterno. A hipótese foi confirmada: o A.1 curou a falsa rejeição, mas revelou que o descarte prematuro era o que evitava deadlocks massivos nas prioridades.

submission.py ALTERADO: NÃO
SUBMISSION KAGGLE: NÃO
"""

with open("replays/v17.3_patchA1_report.md", "w", encoding="utf-8") as f:
    f.write(report)
print("A.1 Report generated.")
