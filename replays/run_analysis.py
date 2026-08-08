import sys
sys.path.insert(0, 'replays')
import bulk_episode_analysis as b
import glob
import os
import statistics
from collections import defaultdict

files = glob.glob('replays/*.json')
files = [f for f in files if 'sample_episode' in f or 'ep_' in f]
print(f'Files: {len(files)}')
for f in files: print(f'  {f}')

all_results = []
for fp in files:
    fname = os.path.basename(fp)
    if 'manifest' in fname or 'dataset' in fname or 'bulk' in fname:
        continue
    try:
        results, info = b.analyze_episode(fp)
        for r in results:
            all_results.append(r)
        print(f'  {fname}: {len(results)} agents, seed={info.get("seed")}')
    except Exception as e:
        print(f'  {fname}: ERROR {e}')

all_results = b.PASS_temporal_classify(all_results)

episodes = defaultdict(list)
for r in all_results:
    episodes[r['episode_id']].append(r)

wins = []; loss = []
for eid, ags in episodes.items():
    if len(ags) == 2:
        if ags[0]['score'] > ags[1]['score']:
            wins.append(ags[0]); loss.append(ags[1])
        else:
            wins.append(ags[1]); loss.append(ags[0])

print(f'\nEpisodes: {len(episodes)}, Winners: {len(wins)}, Losers: {len(loss)}\n')

ms = ['score','revenue','cost','cost_ratio','prod_actions','pass_count','pass_pct','rpa','rws','harvest','feed','care','water','plant','pickup','drop','sell','max_workers','avg_rev_after_pass_5']
h = f"{'Metric':<25} {'W Mean':>10} {'L Mean':>10} {'Adv%':>8}"
print(h); print('-' * len(h))
for m in ms:
    wv=[r[m] for r in wins]; lv=[r[m] for r in loss]
    if not wv or not lv: continue
    wm=statistics.mean(wv); lm=statistics.mean(lv)
    adv=(wm-lm)/abs(lm)*100 if lm else 0
    if m in ('pass_pct','cost_ratio'): s=f'{m:<25} {wm:>10.1f}% {lm:>10.1f}% {adv:>+8.1f}%'
    elif m in ('rpa','rws','avg_rev_after_pass_5'): s=f'{m:<25} {wm:>10.2f} {lm:>10.2f} {adv:>+8.1f}%'
    else: s=f'{m:<25} {wm:>10.1f} {lm:>10.1f} {adv:>+8.1f}%'
    print(s)

print('\nEffect sizes:')
def cd(xs,ys):
    d=statistics.mean(xs)-statistics.mean(ys)
    s=((statistics.stdev(xs)**2+statistics.stdev(ys)**2)/2)**0.5 if len(xs)>1 else 1e-9
    return d/s if s else 0
for m in ['score','pass_pct','rpa','cost_ratio','avg_rev_after_pass_5']:
    wv=[r[m] for r in wins]; lv=[r[m] for r in loss]
    if len(wv)>1: print(f'  {m:<25} d={cd(wv,lv):+.2f}')

print('\nPer-episode:')
for i,(eid,ags) in enumerate(episodes.items()):
    if len(ags)==2:
        a0,a1=ags
        w=a0 if a0['score']>a1['score'] else a1
        l=a1 if a0['score']>a1['score'] else a0
        print(f'  Ep{i}: W({w["team"][:20]}) sc={w["score"]:.0f} PASS={w["pass_pct"]:.1f}% RPA={w["rpa"]:.1f} cost={w["cost_ratio"]:.1f}%')
        print(f'        L({l["team"][:20]}) sc={l["score"]:.0f} PASS={l["pass_pct"]:.1f}% RPA={l["rpa"]:.1f} cost={l["cost_ratio"]:.1f}%')

# PASS classification
print('\nPASS class:')
for label, g in [('W',wins),('L',loss)]:
    prod=sum(1 for r in g if r.get('pass_classification')=='PRODUCTIVE_PASS_dominant')
    neut=sum(1 for r in g if r.get('pass_classification')=='NEUTRAL_PASS_dominant')
    wast=sum(1 for r in g if r.get('pass_classification')=='WASTEFUL_PASS_dominant')
    print(f'  {label}: PROD={prod} NEUT={neut} WAST={wast}')
