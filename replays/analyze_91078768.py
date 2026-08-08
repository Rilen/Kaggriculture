import json
from collections import Counter

f = open(r'C:\Users\rtl\Documents\Github\Kaggriculture\91078768.json')
d = json.load(f); f.close()
steps = d['steps']

sell_opp = Counter(); sell_us = Counter()
rev_opp = 0.0; rev_us = 0.0
water_opp = water_us = 0
plant_opp = plant_us = 0
harvest_opp = harvest_us = 0

for si, step in enumerate(steps):
    for ai, (sc, lab) in enumerate([(sell_opp, 'opp'), (sell_us, 'us')]):
        a = step[ai].get('action', {})
        obs = step[ai].get('observation', {})
        prices = obs.get('market', {}).get('prices', {}) if obs else {}
        
        if isinstance(a, dict):
            for m in a.get('market', []):
                if m and m[0] == 'SELL' and len(m) >= 3:
                    r = m[2] * prices.get(m[1], 0)
                    if ai == 0: rev_opp += r
                    else: rev_us += r
                    sc[m[1]] += m[2]
            
            for wa in [a.get('farmer', [''])] + a.get('hands', []):
                if not wa: continue
                if wa[0] == 'WATER':
                    if ai == 0: water_opp += 1
                    else: water_us += 1
                elif wa[0] == 'PLANT':
                    if ai == 0: plant_opp += 1
                    else: plant_us += 1
                elif wa[0] == 'HARVEST':
                    if ai == 0: harvest_opp += 1
                    else: harvest_us += 1

print('=== SELL BREAKDOWN ===')
for label, sells, rev in [('Opponent', sell_opp, rev_opp), ('Us', sell_us, rev_us)]:
    print(f'{label} (revenue={rev:.0f}):')
    for item, qty in sorted(sells.items(), key=lambda x: -x[1]):
        print(f'  {item}: {qty} units')

print(f'\n=== CROP PIPELINE ===')
print(f'Opponent: PLANT={plant_opp} WATER={water_opp} HARVEST={harvest_opp} water/plant={water_opp/max(plant_opp,1):.1f}')
print(f'Us:       PLANT={plant_us} WATER={water_us} HARVEST={harvest_us} water/plant={water_us/max(plant_us,1):.1f}')

s_opp = steps[-1][0].get('reward', 0)
s_us = steps[-1][1].get('reward', 0)
print(f'\n=== SUMMARY ===')
print(f'Score: Opp={s_opp:.0f} Us={s_us:.0f} Gap={s_opp-s_us:.0f}')
print(f'Revenue: Opp={rev_opp:.0f} Us={rev_us:.0f}')
print(f'Cost: Opp={rev_opp-s_opp:.0f}({100-s_opp/rev_opp*100:.0f}%) Us={rev_us-s_us:.0f}({100-s_us/max(rev_us,1)*100:.0f}%)')
print(f'WATER ratio: Opp watered {water_opp/plant_opp:.1f}x per plant. Us watered {water_us/max(plant_us,1):.1f}x per plant.')
print(f'ROOT CAUSE: We planted 130 crops but watered only 31 times. Opponent planted 126 and watered 1082 times.')
print(f'Opponent grew MASSIVE STRAWBERRY harvests. Our crops died from drought.')
