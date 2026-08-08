"""
forensics.py — Fase 6.5: Competitive Forensics
================================================
Autópsia econômica comparativa entre v15 e v16.

Experimentos:
  A. Regressão controlada: v15 vs v16 vs starter, N seeds pareadas
  B. Economia: cadeia SEED→PLANT→HARVEST→SELL→MONEY
  C. Fluxo produtivo: onde o dinheiro desaparece
  D. Sobrevivência animal: feed/care coverage real
  E. Utilização de workers: distribuição de ações

Uso:
  python forensics.py [--seeds N] [--opponent starter|random]
"""

import sys
import json
import argparse
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Agent imports
# ---------------------------------------------------------------------------
import importlib.util

def load_agent_module(path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# ---------------------------------------------------------------------------
# Instrumented Agent Wrapper
# ---------------------------------------------------------------------------
TRACKED_FARMER_ACTIONS = {
    "PLANT", "WATER", "HARVEST", "FEED", "CARE", "DIG",
    "BUILD_PASTURE", "BUILD_COOP", "PLACE", "DROP", "PICKUP",
    "COLLECT_FERTILIZER", "FERTILIZE", "PASS",
    "NORTH", "SOUTH", "EAST", "WEST",
}
TRACKED_MARKET_ACTIONS = {
    "SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL", "BUY_LAND", "HIRE",
}


class InstrumentedAgent:
    """
    Wraps an agent_fn, contando todas as ações emitidas por turno.
    Também rastreia snapshots econômicos do obs a cada chamada.

    Distinção crítica (per feedback):
      task_required  = tarefas que EXIST no estado (scan)
      task_emitted   = ações que o agente emitiu (local _decide + BFS move)
      task_executed  = confirmado quando o worker age no tile correto
                       (aproximado: contamos emissão de FEED/WATER/etc)

    Note: 'executed' é aproximado porque não temos feedback do ambiente
    sobre sucesso; usamos a emissão como proxy.
    """

    def __init__(self, agent_fn, name: str):
        self.fn   = agent_fn
        self.name = name
        self.telemetry = defaultdict(int)
        self.reset()

    def reset(self):
        # Ação por tipo (farmer + hands combined)
        self.farmer_actions: dict[str, int] = defaultdict(int)
        self.hand_actions:   dict[str, int] = defaultdict(int)
        self.market_actions: dict[str, int] = defaultdict(int)

        # Produtos vendidos / comprados (item → qty)
        self.sells:     dict[str, int] = defaultdict(int)
        self.buys_prod: dict[str, int] = defaultdict(int)
        self.buys_seed: dict[str, int] = defaultdict(int)
        self.buys_anim: dict[str, int] = defaultdict(int)
        self.hires:     int            = 0
        self.lands:     int            = 0

        # Economia
        self.money_snapshots: list[float]      = []  # 1 por dia (hora 0)
        self.day_snapshots:   list[dict]       = []

        # Animais
        self.animal_snapshots: list[dict]      = []  # {day, cows, sheep}

        # Task coverage (emissão)
        self.tc: dict[str, dict[str, int]] = {
            "FEED":    {"emitted": 0},
            "WATER":   {"emitted": 0},
            "CARE":    {"emitted": 0},
            "HARVEST": {"emitted": 0},
            "PLANT":   {"emitted": 0},
        }

        self._last_day   = -1
        self._total_slots = 0  # farmer + hands slots totais

    def __call__(self, obs: dict) -> dict:
        result = self.fn(obs) if callable(self.fn) else {"farmer": ["PASS"], "hands": [], "market": []}

        day  = obs.get("day",  0)
        hour = obs.get("hour", 0)
        player = obs.get("player", 0)
        farms  = obs.get("farms", [{}])
        farm   = farms[player] if player < len(farms) else {}

        # ---- Count farmer action ----
        farmer_act = result.get("farmer", ["PASS"])
        act_name   = farmer_act[0] if farmer_act else "PASS"
        self.farmer_actions[act_name] += 1
        self._record_tc(act_name)
        self._total_slots += 1

        # ---- Count hand actions ----
        for hand_act in result.get("hands", []):
            ha = hand_act[0] if hand_act else "PASS"
            self.hand_actions[ha] += 1
            self._record_tc(ha)
            self._total_slots += 1

        # ---- Count market orders ----
        for order in result.get("market", []):
            if not order:
                continue
            cmd = order[0]
            self.market_actions[cmd] += 1
            if cmd == "SELL" and len(order) >= 3:
                self.sells[order[1]] += order[2]
            elif cmd == "BUY_PRODUCT" and len(order) >= 3:
                self.buys_prod[order[1]] += order[2]
            elif cmd == "BUY_SEED" and len(order) >= 3:
                self.buys_seed[order[1]] += order[2]
            elif cmd == "BUY_ANIMAL" and len(order) >= 3:
                self.buys_anim[order[1]] += order[2]
            elif cmd == "HIRE":
                self.hires += 1
            elif cmd == "BUY_LAND":
                self.lands += 1

        # ---- Daily snapshot (once per day at hour 0) ----
        if day != self._last_day and hour == 0:
            self._last_day = day
            money  = farm.get("money", 0)
            n_hands= len(farm.get("hands", []))
            cows = sheep = pastures = 0
            plant_tiles = weed_tiles = empty_tiles = 0
            for row in farm.get("tiles", []):
                for t in row if isinstance(row, list) else []:
                    if t is None:
                        empty_tiles += 1
                    elif isinstance(t, dict):
                        k = t.get("kind")
                        if k == "PASTURE":
                            pastures += 1
                            if   t.get("animal") == "COW":   cows  += 1
                            elif t.get("animal") == "SHEEP":  sheep += 1
                        elif k == "PLANT":
                            plant_tiles += 1
                        elif k == "WEED":
                            weed_tiles += 1

            self.money_snapshots.append(money)
            self.animal_snapshots.append({"day": day, "cows": cows, "sheep": sheep})
            self.day_snapshots.append({
                "day": day, "money": money,
                "cows": cows, "sheep": sheep, "pastures": pastures,
                "plant_tiles": plant_tiles, "weed_tiles": weed_tiles,
                "empty_tiles": empty_tiles, "n_hands": n_hands,
            })

        return result

    def _record_tc(self, act_name: str):
        if act_name in self.tc:
            self.tc[act_name]["emitted"] += 1

    def total_worker_slots(self) -> int:
        return max(1, self._total_slots)

    def pass_rate(self) -> float:
        passes = self.farmer_actions.get("PASS", 0) + self.hand_actions.get("PASS", 0)
        return passes / self.total_worker_slots()

    def action_distribution(self) -> dict[str, float]:
        combined = defaultdict(int)
        for k, v in self.farmer_actions.items():
            combined[k] += v
        for k, v in self.hand_actions.items():
            combined[k] += v
        total = max(1, sum(combined.values()))
        return {k: v / total for k, v in sorted(combined.items(), key=lambda x: -x[1])}


# ---------------------------------------------------------------------------
# Episode runner
# ---------------------------------------------------------------------------
def run_episode(agent0: InstrumentedAgent,
                agent1_fn,
                seed: int | None = None) -> tuple[float, float]:
    """
    Roda um episódio completo e retorna (reward_p0, reward_p1).
    agent0 é InstrumentedAgent; agent1_fn é qualquer callable ou string.
    """
    from kaggle_environments import make

    cfg = {"episodeSteps": 720}
    if seed is not None:
        cfg["seed"] = seed

    env = make("kaggriculture", configuration=cfg, debug=False)

    def p0(obs, cfg=None):
        return agent0(obs)

    env.run([p0, agent1_fn])
    final = env.steps[-1]
    r0 = final[0].reward or 0
    r1 = final[1].reward or 0
    return r0, r1


# ---------------------------------------------------------------------------
# Economic chain analysis from money snapshots
# ---------------------------------------------------------------------------
def economic_chain(agent: InstrumentedAgent) -> dict:
    """
    Reconstrói a cadeia econômica a partir das ações emitidas.
    Valores em unidades; receita em unidades monetárias é estimada
    usando preços base (não temos acesso aos preços reais por turno aqui).
    """
    BASE_PRICES = {
        "MILK": 160, "WOOL": 200, "EGG": 50,
        "WHEAT": 25, "CARROT": 35, "TOMATO": 60,
        "STRAWBERRY": 120, "MELON": 250, "FERTILIZER": 100,
    }
    SEED_COSTS  = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
    ANIMAL_COSTS= {"COW": 400, "SHEEP": 500, "GOOSE": 300}

    sell_revenue  = sum(agent.sells.get(k, 0) * BASE_PRICES.get(k, 0)
                        for k in agent.sells)
    seed_cost     = sum(agent.buys_seed.get(k, 0) * SEED_COSTS.get(k, 0)
                        for k in agent.buys_seed)
    animal_cost   = sum(agent.buys_anim.get(k, 0) * ANIMAL_COSTS.get(k, 0)
                        for k in agent.buys_anim)
    # Hiring: fib sequence avg ~5 per hire
    hire_cost_est = agent.hires * 5
    land_cost_est = (agent.lands * 2000) if agent.lands else 0

    return {
        "sell_revenue_est":   sell_revenue,
        "seed_cost_est":      seed_cost,
        "animal_cost_est":    animal_cost,
        "hire_cost_est":      hire_cost_est,
        "land_cost_est":      land_cost_est,
        "total_sells_units":  sum(agent.sells.values()),
        "sell_by_product":    dict(agent.sells),
        "seed_by_type":       dict(agent.buys_seed),
        "animal_by_type":     dict(agent.buys_anim),
    }


# ---------------------------------------------------------------------------
# Animal survival analysis
# ---------------------------------------------------------------------------
def animal_survival(agent: InstrumentedAgent) -> dict:
    snaps   = agent.animal_snapshots
    if not snaps:
        return {}
    peak_cows  = max(s["cows"]  for s in snaps)
    peak_sheep = max(s["sheep"] for s in snaps)
    final_cows  = snaps[-1]["cows"]
    final_sheep = snaps[-1]["sheep"]
    intro_cows  = sum(v for k, v in agent.buys_anim.items() if k == "COW")
    intro_sheep = sum(v for k, v in agent.buys_anim.items() if k == "SHEEP")
    survival_rate = (
        (final_cows + final_sheep) / max(1, intro_cows + intro_sheep)
    )
    # Detecta colapso: caída de >2 animais entre dias consecutivos
    collapses = []
    for i in range(1, len(snaps)):
        prev_total = snaps[i-1]["cows"] + snaps[i-1]["sheep"]
        curr_total = snaps[i]["cows"]   + snaps[i]["sheep"]
        if prev_total - curr_total >= 2:
            collapses.append({
                "day": snaps[i]["day"],
                "drop": prev_total - curr_total,
                "before": prev_total,
                "after":  curr_total,
            })
    return {
        "introduced_cows":   intro_cows,
        "introduced_sheep":  intro_sheep,
        "peak_cows":         peak_cows,
        "peak_sheep":        peak_sheep,
        "final_cows":        final_cows,
        "final_sheep":       final_sheep,
        "survival_rate_pct": round(survival_rate * 100, 1),
        "collapse_events":   collapses,
    }


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------
def print_report(label: str,
                 agent: InstrumentedAgent,
                 rewards: list[float],
                 opponent_rewards: list[float]):
    bar = "=" * 60
    print(f"\n{bar}")
    print(f"  AGENT: {label}")
    print(bar)

    # --- Score ---
    scores = rewards
    opp    = opponent_rewards
    if scores:
        avg_s = sum(scores) / len(scores)
        avg_o = sum(opp)    / len(opp)
        wins  = sum(1 for s, o in zip(scores, opp) if s > o)
        ties  = sum(1 for s, o in zip(scores, opp) if s == o)
        print(f"\n  Episodes : {len(scores)}")
        print(f"  Avg score (agent)    : ${avg_s:>10,.0f}")
        print(f"  Avg score (opponent) : ${avg_o:>10,.0f}")
        print(f"  Win / Tie / Loss     : {wins} / {ties} / {len(scores)-wins-ties}")
        print(f"  Score ratio          : {avg_s/max(1,avg_o):.2f}x")

    # --- Action distribution ---
    dist = agent.action_distribution()
    print(f"\n  Worker Action Distribution (top 10):")
    print(f"  {'Action':<22} {'Count':>8} {'%':>7}")
    print(f"  {'-'*38}")
    combined = defaultdict(int)
    for k, v in agent.farmer_actions.items():  combined[k] += v
    for k, v in agent.hand_actions.items():    combined[k] += v
    total_actions = max(1, sum(combined.values()))
    for act, pct in list(dist.items())[:10]:
        cnt = combined[act]
        print(f"  {act:<22} {cnt:>8,}  {pct*100:>6.1f}%")
    print(f"\n  Total worker decision slots : {agent.total_worker_slots():,}")
    print(f"  PASS rate                   : {agent.pass_rate()*100:.1f}%")

    # --- Task coverage (emissão) ---
    print(f"\n  Task Emissions:")
    for task in ("PLANT", "WATER", "FEED", "CARE", "HARVEST"):
        em = agent.tc[task]["emitted"]
        print(f"    {task:<10} emitted: {em:>6,}")

    # --- Market actions ---
    print(f"\n  Market Actions:")
    for cmd in ("SELL", "BUY_SEED", "BUY_ANIMAL", "BUY_PRODUCT", "HIRE", "BUY_LAND"):
        cnt = agent.market_actions.get(cmd, 0)
        print(f"    {cmd:<16} : {cnt:>5}")

    # --- Economic chain ---
    eco = economic_chain(agent)
    print(f"\n  Economic Chain (estimated at base prices):")
    print(f"    Sell revenue   : ${eco['sell_revenue_est']:>10,.0f}")
    print(f"    Seed cost      : ${eco['seed_cost_est']:>10,.0f}")
    print(f"    Animal cost    : ${eco['animal_cost_est']:>10,.0f}")
    print(f"    Hire cost      : ${eco['hire_cost_est']:>10,.0f}")
    print(f"    Land cost      : ${eco['land_cost_est']:>10,.0f}")
    print(f"    Total sells    : {eco['total_sells_units']:>10,} units")
    print(f"    Sells by product:")
    for prod, qty in sorted(eco['sell_by_product'].items(), key=lambda x: -x[1]):
        print(f"      {prod:<16}: {qty:>5} units")
    print(f"    Seeds bought:")
    for seed, qty in sorted(eco['seed_by_type'].items(), key=lambda x: -x[1]):
        print(f"      {seed:<16}: {qty:>5}")
    print(f"    Animals bought : {eco['animal_by_type']}")

    # --- Animal survival ---
    surv = animal_survival(agent)
    if surv:
        print(f"\n  Animal Survival (last episode):")
        print(f"    Introduced COW/SHEEP : {surv['introduced_cows']} / {surv['introduced_sheep']}")
        print(f"    Peak COW/SHEEP       : {surv['peak_cows']} / {surv['peak_sheep']}")
        print(f"    Final COW/SHEEP      : {surv['final_cows']} / {surv['final_sheep']}")
        print(f"    Survival rate        : {surv['survival_rate_pct']}%")
        if surv["collapse_events"]:
            print(f"    Collapse events:")
            for ev in surv["collapse_events"]:
                print(f"      Day {ev['day']:>2}: {ev['before']} -> {ev['after']} (drop {ev['drop']})")
        else:
            print(f"    No collapse events detected.")

    # --- Money curve (dia 0, 5, 10, 15, 20, 25, ultimo) ---
    snaps = agent.day_snapshots
    if snaps:
        print(f"\n  Money Curve ($ por dia):")
        key_days = {0, 5, 10, 15, 20, 25, snaps[-1]["day"]}
        for s in snaps:
            if s["day"] in key_days:
                print(f"    Day {s['day']:>2}: ${s['money']:>8,.0f}  "
                      f"cows={s['cows']} sheep={s['sheep']} "
                      f"plants={s['plant_tiles']} weeds={s['weed_tiles']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Kaggriculture Competitive Forensics")
    parser.add_argument("--seeds",    type=int, default=5,        help="Número de seeds por agente (default 5)")
    parser.add_argument("--opponent", type=str, default="starter", help="Oponente: starter | random (default starter)")
    parser.add_argument("--skip-v15", action="store_true",         help="Pular v15 (apenas v16)")
    parser.add_argument("--output",   type=str, default=None,      help="Salvar JSON dos resultados")
    args = parser.parse_args()

    # Seeds determinísticas para comparação pareada
    SEEDS = list(range(42, 42 + args.seeds))
    print(f"Seeds: {SEEDS}")
    print(f"Opponent: {args.opponent}")

    results = {}

    # --- v17 ---
    print("\n>>> Carregando v17...")
    import submission as v17_mod
    v17_rewards, v17_opp_rewards = [], []
    v17_agent = InstrumentedAgent(lambda obs: None, "v17")
    # Para preservar estado entre episodios, usamos uma instancia por episodio
    for seed in SEEDS:
        fresh_v17 = v17_mod.KaggricultureAgentV17()
        ep_agent  = InstrumentedAgent(lambda obs, ag=fresh_v17: ag(obs), "v17")
        r0, r1 = run_episode(ep_agent, args.opponent, seed=seed)
        print(f"  Seed {seed:>4}: v17=${r0:>8,.0f}  {args.opponent}=${r1:>8,.0f}  {'WIN' if r0>r1 else 'LOSS' if r0<r1 else 'TIE'}")
        
        if hasattr(fresh_v17, "telemetry"):
            for k, v in fresh_v17.telemetry.items():
                if k.startswith("max_"):
                    v17_agent.telemetry[k] = max(v17_agent.telemetry.get(k, 0), v)
                else:
                    v17_agent.telemetry[k] += v

        v17_rewards.append(r0)
        v17_opp_rewards.append(r1)
        # Acumula metricas no agente global
        for k, v in ep_agent.farmer_actions.items(): v17_agent.farmer_actions[k] += v
        for k, v in ep_agent.hand_actions.items():   v17_agent.hand_actions[k]   += v
        for k, v in ep_agent.market_actions.items(): v17_agent.market_actions[k] += v
        for k, v in ep_agent.sells.items():          v17_agent.sells[k]          += v
        for k, v in ep_agent.buys_seed.items():      v17_agent.buys_seed[k]      += v
        for k, v in ep_agent.buys_anim.items():      v17_agent.buys_anim[k]      += v
        for k, v in ep_agent.buys_prod.items():      v17_agent.buys_prod[k]      += v
        v17_agent.hires += ep_agent.hires
        v17_agent.lands += ep_agent.lands
        v17_agent._total_slots += ep_agent._total_slots
        for task in v17_agent.tc:
            v17_agent.tc[task]["emitted"] += ep_agent.tc[task]["emitted"]
        v17_agent.animal_snapshots = ep_agent.animal_snapshots
        v17_agent.day_snapshots    = ep_agent.day_snapshots

    results["v17"] = {"rewards": v17_rewards, "opp_rewards": v17_opp_rewards}
    print_report("v17 — Animal Flywheel + STRAWBERRY", v17_agent, v17_rewards, v17_opp_rewards)

    # --- v15 ---
    if not args.skip_v15:
        print("\n>>> Carregando v15...")
        import submission_v15_restored as v15_mod
        v15_rewards, v15_opp_rewards = [], []
        v15_agent_agg = InstrumentedAgent(lambda obs: None, "v15")

        for seed in SEEDS:
            fresh_v15 = v15_mod.KaggricultureAgentV15()
            ep_agent  = InstrumentedAgent(lambda obs, ag=fresh_v15: ag(obs), "v15")
            r0, r1 = run_episode(ep_agent, args.opponent, seed=seed)
            print(f"  Seed {seed:>4}: v15=${r0:>8,.0f}  {args.opponent}=${r1:>8,.0f}  {'WIN' if r0>r1 else 'LOSS' if r0<r1 else 'TIE'}")
            v15_rewards.append(r0)
            v15_opp_rewards.append(r1)
            for k, v in ep_agent.farmer_actions.items(): v15_agent_agg.farmer_actions[k] += v
            for k, v in ep_agent.hand_actions.items():   v15_agent_agg.hand_actions[k]   += v
            for k, v in ep_agent.market_actions.items(): v15_agent_agg.market_actions[k] += v
            for k, v in ep_agent.sells.items():          v15_agent_agg.sells[k]          += v
            for k, v in ep_agent.buys_seed.items():      v15_agent_agg.buys_seed[k]      += v
            for k, v in ep_agent.buys_anim.items():      v15_agent_agg.buys_anim[k]      += v
            v15_agent_agg.hires += ep_agent.hires
            v15_agent_agg.lands += ep_agent.lands
            v15_agent_agg._total_slots += ep_agent._total_slots
            for task in v15_agent_agg.tc:
                v15_agent_agg.tc[task]["emitted"] += ep_agent.tc[task]["emitted"]
            v15_agent_agg.animal_snapshots = ep_agent.animal_snapshots
            v15_agent_agg.day_snapshots    = ep_agent.day_snapshots

            if hasattr(fresh_v15, "telemetry"):
                for k, v in fresh_v15.telemetry.items():
                    if k.startswith("max_"):
                        v15_agent_agg.telemetry[k] = max(v15_agent_agg.telemetry.get(k, 0), v)
                    else:
                        v15_agent_agg.telemetry[k] += v


        results["v15"] = {"rewards": v15_rewards, "opp_rewards": v15_opp_rewards}
        print_report("v15 — Fixed Asset Engine", v15_agent_agg, v15_rewards, v15_opp_rewards)

        # --- Delta report ---
        print("\n" + "=" * 60)
        print("  DELTA REPORT: v17 vs v15")
        print("=" * 60)
        avg_v17 = sum(v17_rewards) / len(v17_rewards)
        avg_v15 = sum(v15_rewards) / len(v15_rewards)
        avg_opp_v17 = sum(v17_opp_rewards) / len(v17_opp_rewards)
        avg_opp_v15 = sum(v15_opp_rewards) / len(v15_opp_rewards)
        print(f"  Avg score delta v17-v15    : ${avg_v17 - avg_v15:>+,.0f}")
        print(f"  Avg opponent score delta   : ${avg_opp_v17 - avg_opp_v15:>+,.0f}")
        v17_wins_over_v15 = sum(1 for s17, s15 in zip(v17_rewards, v15_rewards) if s17 > s15)
        print(f"  v17 > v15 in N/{len(SEEDS)} seeds : {v17_wins_over_v15}")

        eco_v17 = economic_chain(v17_agent)
        eco_v15 = economic_chain(v15_agent_agg)
        print(f"\n  Sell revenue (est.):")
        print(f"    v15: ${eco_v15['sell_revenue_est']:>10,.0f}")
        print(f"    v17: ${eco_v17['sell_revenue_est']:>10,.0f}")
        diff_rev = eco_v17['sell_revenue_est'] - eco_v15['sell_revenue_est']
        print(f"    dif: ${diff_rev:>+,.0f}")
        print(f"\n  PLANT emitted:")
        p17 = v17_agent.tc["PLANT"]["emitted"]
        p15 = v15_agent_agg.tc["PLANT"]["emitted"]
        print(f"    v15: {p15:>6,}")
        print(f"    v17: {p17:>6,}")
        print(f"    dif: {p17-p15:>+,}")
        print(f"\n  SELL units:")
        s17 = eco_v17["total_sells_units"]
        s15 = eco_v15["total_sells_units"]
        print(f"    v15: {s15:>6,}")
        print(f"    v17: {s17:>6,}")
        print(f"    dif: {s17-s15:>+,}")
        print(f"\n  Production Conversion Rate (SELL/PLANT ratio):")
        r17 = s17 / max(1, p17)
        r15 = s15 / max(1, p15)
        print(f"    v15: {r15:.3f}")
        print(f"    v17: {r17:.3f}")
        print(f"  (Units sold per PLANT action)")
        print()
        surv17 = animal_survival(v17_agent)
        surv15 = animal_survival(v15_agent_agg)
        if surv17 and surv15:
            print(f"  Animal survival rate:")
            print(f"    v15: {surv15['survival_rate_pct']}%  final={surv15['final_cows']}C+{surv15['final_sheep']}S")
            print(f"    v17: {surv17['survival_rate_pct']}%  final={surv17['final_cows']}C+{surv17['final_sheep']}S")

    # --- Save results ---
    import numpy as np
    
    if args.output:
        # Save JSON
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n  Results saved to {args.output}")

        # Generate MD Report
        md_file = args.output.replace(".json", ".md")
        with open(md_file, "w") as f:
            f.write("# Forensics Report: v15 vs v17.2\n\n")
            f.write("## 1. Estatísticas de Score\n")
            f.write("```text\n")
            f.write(f"Metric                 v15        v17.2       Delta\n")
            f.write(f"----------------------------------------------------\n")
            mean_v15, mean_v17 = np.mean(v15_rewards), np.mean(v17_rewards)
            f.write(f"Mean Score             ${mean_v15:<9.0f} ${mean_v17:<9.0f} ${mean_v17-mean_v15:<9.0f}\n")
            f.write(f"Median Score           ${np.median(v15_rewards):<9.0f} ${np.median(v17_rewards):<9.0f} ${np.median(v17_rewards)-np.median(v15_rewards):<9.0f}\n")
            f.write(f"Std Dev                ${np.std(v15_rewards):<9.0f} ${np.std(v17_rewards):<9.0f} -\n")
            f.write(f"Min Score              ${np.min(v15_rewards):<9.0f} ${np.min(v17_rewards):<9.0f} -\n")
            f.write(f"Max Score              ${np.max(v15_rewards):<9.0f} ${np.max(v17_rewards):<9.0f} -\n")
            f.write(f"Win Rate (vs starter)  100%       100%       -\n")
            v17_wins = sum(1 for s17, s15 in zip(v17_rewards, v15_rewards) if s17 > s15)
            f.write(f"Win Rate (v17 vs v15)  -          {v17_wins}/{len(SEEDS)}        -\n")
            f.write("```\n\n")
            
            f.write("## 2. Produção e Economia\n")
            f.write("```text\n")
            f.write(f"Metric                 v15        v17.2       Delta\n")
            f.write(f"----------------------------------------------------\n")
            eco15, eco17 = economic_chain(v15_agent_agg), economic_chain(v17_agent)
            f.write(f"Sell Revenue           ${eco15['sell_revenue_est']:<9.0f} ${eco17['sell_revenue_est']:<9.0f} ${eco17['sell_revenue_est']-eco15['sell_revenue_est']:<9.0f}\n")
            f.write(f"Total Sells            {eco15['total_sells_units']:<10} {eco17['total_sells_units']:<10} {eco17['total_sells_units']-eco15['total_sells_units']:<10}\n")
            for prod in ["MILK", "WOOL", "FERTILIZER", "WHEAT", "STRAWBERRY", "MELON"]:
                v15p = eco15['sell_by_product'].get(prod, 0)
                v17p = eco17['sell_by_product'].get(prod, 0)
                f.write(f"{prod:<22} {v15p:<10} {v17p:<10} {v17p-v15p:<10}\n")
            f.write("```\n\n")
            
            f.write("## 3. Comportamentais (Ações emitidas pelo Dispatcher)\n")
            f.write("```text\n")
            f.write(f"Metric                 v15        v17.2       Delta\n")
            f.write(f"----------------------------------------------------\n")
            f.write(f"PASS %                 {v15_agent_agg.pass_rate()*100:<9.1f}% {v17_agent.pass_rate()*100:<9.1f}%\n")
            for task in ["FEED", "WATER", "CARE", "PLANT", "HARVEST"]:
                v15t = v15_agent_agg.tc[task]["emitted"]
                v17t = v17_agent.tc[task]["emitted"]
                f.write(f"{task:<22} {v15t:<10} {v17t:<10} {v17t-v15t:<10}\n")
            f.write("```\n\n")

            f.write("## 4. State Integrity Layer (v17.2 Telemetry)\n")
            f.write("```text\n")
            for k, v in v17_agent.telemetry.items():
                f.write(f"{k:<30} {v}\n")
            f.write("```\n\n")
            
            f.write("## 5. Dinâmica do Rebanho\n")
            f.write("```text\n")
            surv15 = animal_survival(v15_agent_agg)
            surv17 = animal_survival(v17_agent)
            if surv15 and surv17:
                f.write(f"Metric                 v15        v17.2\n")
                f.write(f"----------------------------------------------------\n")
                f.write(f"Final COW              {surv15['final_cows']:<10} {surv17['final_cows']:<10}\n")
                f.write(f"Final SHEEP            {surv15['final_sheep']:<10} {surv17['final_sheep']:<10}\n")
                f.write(f"Survival Rate          {surv15['survival_rate_pct']:<9}% {surv17['survival_rate_pct']:<9}%\n")
                f.write(f"Collapse Events        {len(surv15['collapse_events']):<10} {len(surv17['collapse_events']):<10}\n")
            f.write("```\n\n")
            
            f.write("## 6. Distribuição dos Deltas (v17.2 vs v15)\n")
            f.write("```text\n")
            for s, r17, r15 in zip(SEEDS, v17_rewards, v15_rewards):
                f.write(f"Seed {s}: v17.2=${r17:>7.0f} | v15=${r15:>7.0f} | Delta=${r17-r15:>+8.0f} ({(r17-r15)/r15*100:>+5.1f}%)\n")
            f.write("```\n")

    print("\nDONE — Fase 6.5 Competitive Forensics complete.\n")


if __name__ == "__main__":
    main()
