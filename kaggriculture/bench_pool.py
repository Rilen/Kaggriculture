"""Benchmark contrafactual de pool — mede win rate + margem contra um pool de
replays oficiais (top-5 e seus oponentes reais), nos DOIS seats.

Uso:
  python3 bench_pool.py [AGENT] [REPLAY_DIR]

Para cada replay, roda:
  - nosso agente no seat 0 vs oponente gravado (seat 1 do replay)
  - nosso agente no seat 1 vs oponente gravado (seat 0 do replay)
e rotula cada resultado pelo NOME real do time que o replay_agent reproduziu.

O harness reproduz o episodio original deterministicamente (seed de info.seed),
entao qualquer diferenca de resultado vem apenas da nossa politica.
"""
import glob
import json
import os
import statistics
import sys
from collections import defaultdict

from kaggle_environments import make

AGENT = sys.argv[1] if len(sys.argv) > 1 else "submission.py"
REPLAY_DIR = sys.argv[2] if len(sys.argv) > 2 else "/tmp/kilo/top_replays"


def load(replay):
    d = json.load(open(replay))
    seed = d["configuration"].get("seed") or d.get("info", {}).get("seed")
    cfg = {"episodeSteps": d["configuration"].get("episodeSteps", 720)}
    if seed is not None:
        cfg["seed"] = seed
    names = [a.get("Name", "?") for a in d.get("info", {}).get("Agents", [{}, {}])]
    return cfg, names


def play(replay, our_seat):
    cfg, names = load(replay)
    os.environ["REPLAY_FILE"] = replay
    # replay_agent reproduz o outro seat (o oponente gravado)
    os.environ["REPLAY_SEAT"] = str(1 - our_seat)
    agents = [AGENT, "replay_agent.py"] if our_seat == 0 else ["replay_agent.py", AGENT]
    env = make("kaggriculture", configuration=cfg, debug=False)
    env.run(agents)  # type: ignore[arg-type]
    last = env.steps[-1]
    mine = last[our_seat]["reward"] or 0.0
    opp = last[1 - our_seat]["reward"] or 0.0
    return mine, opp, names[1 - our_seat]


def main():
    replays = sorted(glob.glob(os.path.join(REPLAY_DIR, "*.json")))
    if not replays:
        print(f"nenhum replay em {REPLAY_DIR}")
        return
    rows = []
    for r in replays:
        for seat in (0, 1):
            rows.append(play(r, seat))

    by_opp = defaultdict(list)
    for mine, opp, name in rows:
        by_opp[name].append((mine, opp))

    print(f"agente: {AGENT}  |  {len(rows)} jogos contrafactuais (2 seats x {len(replays)} replays)")
    print(f"{'oponente':<18}{'jogos':>6}{'wins':>6}{'nosso avg':>11}{'opp avg':>11}{'margem':>9}")
    total_wins = 0
    all_margins = []
    for name in sorted(by_opp):
        r = by_opp[name]
        wins = sum(1 for m, o in r if m > o)
        total_wins += wins
        m_avg = statistics.mean(m for m, o in r)
        o_avg = statistics.mean(o for m, o in r)
        margin = m_avg - o_avg
        all_margins.append(margin)
        print(f"{name:<18}{len(r):>6}{wins:>6}{m_avg:>11.0f}{o_avg:>11.0f}{margin:>+9.0f}")

    print("-" * 62)
    print(f"TOTAL: {total_wins}/{len(rows)} vitorias | margem media {statistics.mean(all_margins):+.0f}")


if __name__ == "__main__":
    main()
