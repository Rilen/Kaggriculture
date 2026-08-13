from kaggle_environments import make
import statistics, sys

AGENT = sys.argv[1] if len(sys.argv) > 1 else "submission.py"

def run(opp, seed):
    env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': seed})
    env.run([AGENT, opp])
    return [round(st['reward'], 1) for st in env.steps[-1]]

OPPS = ['random', 'starter', 'pass', 'submission_by_grok.py']
for opp in OPPS:
    res = [run(opp, s) for s in range(1, 13)]
    scores = [r[0] for r in res]
    wins = sum(1 for r in res if r[0] > r[1])
    print('%-22s win=%2d/8 avg=%.0f min=%.0f max=%.0f' % (opp, wins, statistics.mean(scores), min(scores), max(scores)))
