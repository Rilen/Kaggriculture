import json, glob; from collections import Counter
files = sorted(glob.glob(r'C:\Users\rtl\Documents\Github\Kaggriculture\perdi\*.json'))
for fp in files[-5:]:
    f=open(fp); d=json.load(f); f.close()
    steps=d['steps']; info=d['info']; eid=info['EpisodeId']
    teams=info.get('TeamNames',['?','?'])
    our_ai=0 if 'Rilen' in (teams[0] if len(teams)>0 else '') else 1
    opp_ai=1-our_ai
    rev_opp=0.0; rev_us=0.0; act_opp=Counter(); act_us=Counter(); sell_opp=Counter(); hire_opp=hire_us=0
    for step in steps:
        for ai,ctr in [(opp_ai,act_opp),(our_ai,act_us)]:
            a=step[ai].get('action',{}); obs=step[ai].get('observation',{})
            prices=obs.get('market',{}).get('prices',{}) if obs else {}
            if isinstance(a,dict):
                for m in a.get('market',[]):
                    if m and m[0]=='SELL' and len(m)>=3:
                        rev=m[2]*prices.get(m[1],0)
                        if ai==opp_ai: rev_opp+=rev
                        else: rev_us+=rev
                        if ai==opp_ai: sell_opp[m[1]]+=m[2]
                    if m and m[0]=='HIRE':
                        if ai==opp_ai: hire_opp+=1
                        else: hire_us+=1
                for wa in [a.get('farmer',[''])]+a.get('hands',[]):
                    if wa: ctr[wa[0]]+=1
    s_opp=steps[-1][opp_ai].get('reward',0); s_us=steps[-1][our_ai].get('reward',0)
    obs_f=steps[-1][opp_ai].get('observation',{}); farms=obs_f.get('farms',[])
    farm=farms[opp_ai] if farms and opp_ai<len(farms) and isinstance(farms[opp_ai],dict) else {}
    cows=sheep=goose=0; crops=Counter()
    for row in farm.get('tiles',[]):
        for t in (row if isinstance(row,list) else []):
            if isinstance(t,dict):
                if t.get('kind')=='PASTURE':
                    a=t.get('animal')
                    if a=='COW': cows+=1
                    elif a=='SHEEP': sheep+=1
                elif t.get('kind')=='COOP':
                    if t.get('animal')=='GOOSE': goose+=1
                elif t.get('kind')=='PLANT': crops[t.get('crop','?')]+=1
    water_o=act_opp.get('WATER',0); water_u=act_us.get('WATER',0)
    fert_o=act_opp.get('FERTILIZE',0); fert_u=act_us.get('FERTILIZE',0)
    pass_o=act_opp.get('PASS',0); pass_u=act_us.get('PASS',0)
    print(f'{eid} | {teams[opp_ai][:25]:<25} | S:{s_opp:.0f}v{s_us:.0f} ({s_opp/max(s_us,1):.1f}x) | R:{rev_opp:.0f}v{rev_us:.0f}')
    print(f'  WATER:{water_o} v {water_u} | FERT:{fert_o} v {fert_u} | HI:{hire_opp} v {hire_us} | C{cows}S{sheep}G{goose}')
    print(f'  PASS:{pass_o} v {pass_u} | Sells: {dict(sell_opp.most_common(4))}')
    print()
