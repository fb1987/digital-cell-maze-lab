"""V12Q identical rank/reproduction across arms; only training inputs differ."""
from collections import defaultdict
from copy import deepcopy
import hashlib,json,random
from .exposure_genome import Genome,Individual
from .exposure_selection import evaluate
from .foundation_fitness import lexicase
from .growth import random_genome,mutate,replay_mutation
from .regulatory_search import tuple_tree
from .routing_transfer import canonical

ARMS=('current','mixed','resample')
ARCHIVES=('primary','choice','corridor')

def digest(x):return hashlib.sha256(json.dumps(canonical(x),sort_keys=True,separators=(',',':')).encode()).hexdigest()

def summary(rows,meta):
    pairs=defaultdict(list)
    for r in rows:
        m=meta[r['case']]
        if m['family']=='paired':pairs[m['base'],m['pose']].append(r)
    assert all(len(rs)==2 for rs in pairs.values())
    good=[k for k,rs in pairs.items() if all(r['optimal'] for r in rs)]
    by=defaultdict(lambda:dict(pairs=0,opportunities=0,contexts=set(),poses=set()))
    for k,rs in pairs.items():
        m=meta[rs[0]['case']];s=by[f'{"stress" if m["stress"] else "core"}/{m["graph"]}/p{m["prefix"]}'];s['opportunities']+=1
        if k in good:s['pairs']+=1;s['contexts'].add(m['template']);s['poses'].add(m['pose'])
    for v in by.values():v['contexts']=sorted(v['contexts']);v['poses']=sorted(v['poses'])
    positive=[k for k in good if meta[pairs[k][0]['case']]['prefix']==1 and not meta[pairs[k][0]['case']]['stress']]
    zero=[k for k in good if meta[pairs[k][0]['case']]['prefix']==0 and not meta[pairs[k][0]['case']]['stress']]
    return dict(pairs=len(good),opportunities=len(pairs),positive=len(positive),zero=len(zero),positive_keys=[list(k) for k in positive],positive_contexts=sorted({meta[pairs[k][0]['case']]['template'] for k in positive}),positive_poses=sorted({k[1] for k in positive}),corridors=sum(r['optimal'] for r in rows if meta[r['case']]['family']=='corridor'),optimal=sum(r['optimal'] for r in rows),valid=sum(r['valid'] for r in rows),no_path=sum(r['no_path'] for r in rows),false_no_path=sum(r['reachable'] and r['status']=='no_path' for r in rows),partial=round(sum(r['partial'] for r in rows),8),by=dict(by),work=sum(r['reads']+r['dispatches']+r['exposure_checks'] for r in rows),behavior=digest([(r['mask'],r['status'],r['steps']) for r in rows]))

def archive_rank(s,name):
    tail=(s['no_path']-s['false_no_path'],s['partial'])
    if name=='primary':return (s['positive'],s['pairs'],s['corridors'],*tail)
    if name=='choice':return (s['zero'],s['positive'],s['corridors'],*tail)
    if name=='corridor':return (s['corridors'],s['no_path']-s['false_no_path'],s['pairs'],s['partial'])
    raise ValueError(name)

def update_archives(archives,item,s,generation):
    for name in ARCHIVES:
        rank=archive_rank(s,name);old=archives.get(name)
        if old is None or (tuple(-v for v in rank),item.genome.digest,item.identity)<(tuple(-v for v in old['rank']),old['digest'],old['item']['id']):
            archives[name]=dict(item=item.save(),digest=item.genome.digest,rank=list(rank),metrics=s,generation=generation)

def ranked(population,rows,meta):
    return sorted(((evaluate(rows[i.identity],meta),i) for i in population),key=lambda x:(tuple(-v for v in x[0].fitness),x[1].genome.digest,x[1].identity))

def nominees(rank):
    out=[];seen=set()
    for ev,i in rank:
        behavior=digest([(r['mask'],r['status']) for r in ev.rows])
        if behavior not in seen:out.append(i);seen.add(behavior)
        if len(out)==2:return out
    for _,i in rank:
        if i.identity not in {v.identity for v in out}:out.append(i)
        if len(out)==2:return out
    raise AssertionError('Missing nominee')

def reproduce(state,rank,archives):
    rng=random.Random();rng.setstate(tuple_tree(state['rng']));before=rng.getstate();selected=[];seen=set()
    def add(i):
        if len(selected)<24 and i.identity not in seen:selected.append(i);seen.add(i.identity)
    for raw in state['protected']:add(Individual.load(raw))
    for name in ARCHIVES:add(Individual.load(archives[name]['item']))
    add(rank[0][1]);behaviors=set()
    for ev,i in rank:
        b=digest([(r['mask'],r['status']) for r in ev.rows])
        if b not in behaviors:add(i);behaviors.add(b)
    for _,i in rank:add(i)
    assert len(selected)==24
    elite=[i.identity for i in selected];births=[]
    for index in range(72):
        events=None;parent=None
        if state['arm']=='resample' or index<9:genome=Genome(random_genome(rng,True),7)
        else:
            p=rng.choice(rank)[1] if rng.random()<.1 else lexicase(rng,rank);parent=p.identity
            program,events=mutate(p.genome.program,rng,1,256,True);assert replay_mutation(p.genome.program,events,256)==program
            genome=Genome(program,p.genome.exposure)
        i=Individual(f'{state["key"]}/i{state["serial"]+index}',genome,parent,state['generation']+1)
        births.append(dict(item=i.save(),events=events));selected.append(i)
    new=deepcopy(state);new.update(population=[i.save() for i in selected],rng=canonical(rng.getstate()),serial=state['serial']+72,generation=state['generation']+1,archives=deepcopy(archives))
    packet=dict(generation=state['generation'],key=state['key'],elite=elite,births=births,rng_before=digest(before),rng_after=digest(rng.getstate()),population=digest(new['population']),train_fitness={i.identity:list(ev.fitness) for ev,i in rank})
    return canonical(new),canonical(packet)

def gate(mixed,current,resample,frozen):
    new=set(map(tuple,mixed['positive_keys']))-set(map(tuple,frozen['positive_keys']))
    return bool(len(new)>=8 and mixed['positive']>=max(current['positive'],resample['positive'],frozen['positive'])+8 and len(mixed['positive_contexts'])>=2 and len(mixed['positive_poses'])>=2 and mixed['zero']>=.95*frozen['zero'] and mixed['corridors']>=.95*frozen['corridors'] and mixed['false_no_path']<=frozen['false_no_path'])
