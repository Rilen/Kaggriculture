import json
d = json.load(open('replays/episode-92065613-replay.json'))
steps = d['steps']


def summarize(farm):
    tiles = farm.get('tiles', [])
    r = dict(money=int(farm.get('money', 0)), animals=0, coops=0, pastures=0,
             plants=0, melon=0, straw=0, tomato=0, wheat=0, carrot=0, weeds=0,
             quads=len(farm.get('unlocked_quadrants', [])), hands=len(farm.get('hands', [])))
    for row in tiles:
        for t in row:
            if not isinstance(t, dict):
                continue
            k = t.get('kind')
            if k == 'PLANT':
                r['plants'] += 1
                c = t.get('crop')
                key = {'MELON': 'melon', 'STRAWBERRY': 'straw', 'TOMATO': 'tomato',
                       'WHEAT': 'wheat', 'CARROT': 'carrot'}.get(c)
                if key:
                    r[key] += 1
            elif k == 'COOP':
                r['coops'] += 1
                if t.get('animal'):
                    r['animals'] += 1
            elif k == 'PASTURE':
                r['pastures'] += 1
                if t.get('animal'):
                    r['animals'] += 1
            elif k == 'WEED':
                r['weeds'] += 1
    return r


for day in [0, 2, 4, 7, 10, 14, 18, 22, 26, 29]:
    step = day * 24
    if step >= len(steps):
        break
    print('=== DAY', day, '===')
    for pi in (0, 1):
        obs = steps[step][pi]['observation']
        farm = obs['farms'][pi]
        print(' P%d' % pi, summarize(farm))
