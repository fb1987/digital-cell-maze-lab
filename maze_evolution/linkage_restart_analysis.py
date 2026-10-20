"""V12X-R1 activation gate; training fitness is not independent efficacy evidence."""
from collections import Counter,defaultdict
import json
from .linkage_restart_data import *
from .linkage_restart_search import SEXUAL,ARMS
from .routing_transfer import lines,canonical
from .foundation_calibration import write_json

def compute(events,generations):
    by={f'{o}/{r}/{a}':Counter(births=0,scheduled=0,donor_available=0,accepted=0,multi_before_mutation=0,multi_retained=0,dependency_cut=0) for o in ('carry','fresh') for r in range(3) for a in ARMS}
    lengths=defaultdict(lambda:dict(proposed=Counter(),accepted=Counter(),multi_retained=Counter()));active=defaultdict(set);reasons=defaultdict(Counter)
    for e in events:
        key=e['key'];s=by[key]
        for b in e.get('births',[]):
            s['births']+=1;m=b['mating'];x=b['crossover']
            if m is None:continue
            s['scheduled']+=1;s['donor_available']+=x is not None
            if x is None:reasons[key][m['reason']]+=1;continue
            lengths[key]['proposed'][str(x['length'])]+=1;reasons[key][x['reason']]+=1
            if x['accepted']:
                s['accepted']+=1;s['multi_before_mutation']+=x['changed_instructions']>=2;s['multi_retained']+=b['retained_donor_changes']>=2
                s['dependency_cut']+=not x['dependency_closed'];lengths[key]['accepted'][str(x['length'])]+=1
                if b['retained_donor_changes']>=2:active[key].add(e['generation']);lengths[key]['multi_retained'][str(x['length'])]+=1
    passing={o:{a:[] for a in SEXUAL} for o in ('carry','fresh')}
    for key,s in by.items():
        origin,rep,arm=key.split('/');s['multi_generation_count']=len(active[key]);s['multi_fraction']=s['multi_retained']/s['scheduled'] if s['scheduled'] else 0
        s['passed']=arm in SEXUAL and generations>=32 and s['multi_fraction']>=.1 and len(active[key])>=8
        if s['passed']:passing[origin][arm].append(int(rep))
        if arm in SEXUAL:assert s['scheduled']==32*generations
    eligible={o:all(len(passing[o][a])>=2 for a in SEXUAL) for o in passing}
    return canonical(dict(generations=generations,adequate_generations=generations>=32,by_condition=by,lengths=lengths,reasons=reasons,passing=passing,origin_eligible=eligible,
        longer_search_authorized_by_gate=all(eligible.values()),interpretation='Feasibility activation only; no efficacy holdout, validation selection or generalization claim. No candidate is promoted based on these training scores. Both origins and all three crossover controls must qualify before this protocol permits a longer joint comparison.'))

def analyze():
    ex=json.loads((OUT/'execution.json').read_text());assert ex['complete']
    packet=compute(lines(OUT/'reproduction.jsonl.gz'),ex['generations']);write_json(OUT/'analysis.json',packet)
    print(json.dumps(packet,indent=2),flush=True)
