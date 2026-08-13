"""Contrafactual 'strict-future' local sobre replays oficiais.

Uso:
  python3 bench_replay.py <AGENT> <REPLAY.json> [--seats 0,1] [--sanity]

  --sanity : roda replay(seat0) vs replay(seat1). O resultado DEVE reproduzir
             exatamente o replay original (prova que o harness funciona).
  default : roda <AGENT> vs o oponente gravado (outro seat), nos dois seats.

Metrica de aceite (Passo 1): win rate + margem vs pool real de oponentes
gravados, nao apenas moedas vs random/starter.
"""
import json
import os
import sys
from kaggle_environments import make

AGENT = sys.argv[1] if len(sys.argv) > 1 else "submission.py"
REPLAY = sys.argv[2] if len(sys.argv) > 2 else "replays/episode-91035389-replay.json"
SANITY = "--sanity" in sys.argv
SEATS = [0, 1]


def _load():
    d = json.load(open(REPLAY))
    seed = d["configuration"].get("seed")
    if seed is None:
        seed = d.get("info", {}).get("seed")  # replay oficial guarda o seed em info
    cfg = {"episodeSteps": d["configuration"].get("episodeSteps", 720)}
    if seed is not None:
        cfg["seed"] = seed
    orig_rewards = d.get("rewards")
    return d, cfg, orig_rewards


def run(seat_agent0):
    """seat_agent0: 'agent' | 'replay' — o que ocupa o seat 0."""
    os.environ["REPLAY_FILE"] = REPLAY
    agents = [AGENT, "replay_agent.py"]
    if seat_agent0 == "replay":
        os.environ["REPLAY_SEAT"] = "0"
        agents = ["replay_agent.py", AGENT]
    else:
        os.environ["REPLAY_SEAT"] = "1"
    env = make("kaggriculture", configuration=cfg, debug=False)
    env.run(agents)  # type: ignore[arg-type]
    last = env.steps[-1]
    return [round(st["reward"], 1) for st in last]


def main():
    global cfg
    d, cfg, orig = _load()
    print(f"replay: {REPLAY}")
    print(f"  configuration: {cfg}  rewards originais: {orig}")
    if SANITY:
        os.environ["REPLAY_FILE"] = REPLAY
        os.environ.pop("REPLAY_SEAT", None)  # cada agente usa obs['player'] (0 e 1)
        env = make("kaggriculture", configuration=cfg, debug=False)
        env.run(["replay_agent.py", "replay_agent.py"])  # type: ignore[arg-type]
        res = [round(st["reward"], 1) for st in env.steps[-1]]
        ok = res == [round(x, 1) for x in orig]
        print(f"  sanity replay-vs-replay: {res} vs original {orig} -> {'OK' if ok else 'DIVERGENTE'}")
        return
    for seat0 in ("agent", "replay"):
        res = run(seat0)
        mine = res[0] if seat0 == "agent" else res[1]
        opp = res[1] if seat0 == "agent" else res[0]
        win = "WIN" if mine > opp else ("TIE" if mine == opp else "LOSS")
        print(f"  nosso-seat0={seat0=='agent':>5}: {res} -> {win} (nosso {mine} vs opp {opp})")


if __name__ == "__main__":
    main()
