"""Replay agent — reproduz, passo a passo, as acoes gravadas de um replay oficial
(formato kaggle_environments). Usado para contrafactual 'strict-future': o
oponente gravado NAO reage as nossas mudancas de politica.

Convencao de indexacao (validada empiricamente):
  - replay oficial: steps[N] = {estado POS-acao N, acao N}
  - env local:      steps[N] = {estado pos-acao N-1, acao N-1}
  Logo, para reproduzir o replay no env local, o agente chamado com obs.step=k
  deve retornar replay.steps[k+1].action (clamp k+1 <= N-1).

Seat: por padrao usa obs['player'] (o seat em que esta jogando), o que permite
sanity check replay-vs-replay. REPLAY_SEAT sobrescreve (para forcar o lado do
oponente gravado em contrafactual).
"""
import json
import os

_REPLAY = os.environ.get("REPLAY_FILE", "")
_SEAT = int(os.environ.get("REPLAY_SEAT", "-1"))
_ACTIONS = None
_PASS = {"farmer": ["PASS"], "hands": [], "market": []}


def _load():
    global _ACTIONS
    if _ACTIONS is None:
        d = json.load(open(_REPLAY))
        _ACTIONS = [[st[0].get("action"), st[1].get("action")] for st in d["steps"]]
    return _ACTIONS


def agent(obs, config):
    actions = _load()
    n = len(actions)
    step = obs.get("step", 0)
    seat = _SEAT if _SEAT >= 0 else obs.get("player", 0)
    i = step + 1 if step + 1 < n else n - 1
    a = actions[i][seat]
    if not isinstance(a, dict):
        return _PASS
    return {
        "farmer": a.get("farmer", ["PASS"]),
        "hands": a.get("hands", []),
        "market": a.get("market", []),
    }
