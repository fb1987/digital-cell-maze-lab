"""M1 matched pilot: generic random founders, common selection, no solver imports."""
from copy import deepcopy
import random
from collections import defaultdict
from . import modular_genome as modular
from . import growth as flat
from .datasets import seed_for
from .routing_transfer import canonical


def genome(rep,value):return (modular.Genome if rep=='modular' else flat.Genome).from_dict(value)
def random_genome(rep,rng):return (modular if rep=='modular' else flat).random_genome(rng)
def mutation(rep,g,rng):return modular.mutate(g,rng) if rep=='modular' else flat.mutate(g,rng,ceiling=256,return_events=True)
def tupled(x):return tuple(tupled(y) for y in x) if isinstance(x,list) else x


def founders(seed,population=96):
    states=[]
    for rep in ('flat','modular'):
        for replicate in range(3):
            rng=random.Random(seed_for(seed,'founders/'+rep,replicate,0))
            items=[]
            for i in range(population):
                identity=f'm1/{rep}/{replicate}/founder/{i}'
                items.append(dict(id=identity,genome=random_genome(rep,rng).to_dict(),root=identity,parent=None,birth=0,mutation_depth=0))
            for curriculum in ('familiar','broad'):
                for method in ('mutation','resample'):
                    name=f'{rep}/{replicate}/{curriculum}/{method}'
                    states.append(dict(name=name,representation=rep,replicate=replicate,curriculum=curriculum,method=method,
                        generation=0,assessment_generation=-1,population=deepcopy(items),archive=[],frozen=[],
                        rng=random.Random(seed_for(seed,'evolution/'+name,0,0)).getstate()))
    return canonical(states)


def values(rows):
    return [(int(r['optimal'] or r['no_path']),int(r['valid'] or r['no_path']),
             -int(r['reachable'] and r['status']=='no_path'),r['partial']) for r in rows]


def rank(rows,meta,ordinary=False):
    groups=defaultdict(list)
    for r in rows:
        m=meta[r['case']]
        if ordinary and m['family'] not in ('ordinary_perfect','ordinary_random'):continue
        groups[m['family']].append(r)
    score=[0.,0.,0.]
    for rs in groups.values():
        false=sum(r['reachable'] and r['status']=='no_path' for r in rs)
        score[0]+=(sum(r['optimal'] or r['no_path'] for r in rs)-false)/len(rs)
        score[1]+=(sum(r['valid'] or r['no_path'] for r in rs)-false)/len(rs)
        score[2]+=sum(r['partial'] for r in rs)/len(rs)
    return tuple(round(v/max(1,len(groups)),10) for v in score)


def ordered(items,rows,meta,ordinary=False):
    return sorted(items,key=lambda i:(tuple(-v for v in rank(rows[i['id']],meta,ordinary)),i['id']))


def lexicase(rng,pool,vals):
    pool=list(pool);cases=list(range(len(vals[pool[0]['id']])));rng.shuffle(cases)
    for c in cases:
        for field in range(4):
            best=max(vals[i['id']][c][field] for i in pool);epsilon=.02 if field==3 else 0
            pool=[i for i in pool if vals[i['id']][c][field]>=best-epsilon]
            if len(pool)==1:return pool[0]
    return rng.choice(pool)


def retain(pool,rows,meta,count,merit,rng=None):
    ranked=ordered(pool,rows,meta);chosen=ranked[:min(merit,count)]
    success={i['id']:{j for j,r in enumerate(rows[i['id']]) if r['optimal'] or r['no_path']} for i in pool}
    covered=set().union(*(success[i['id']] for i in chosen))
    left=[i for i in ranked if i not in chosen]
    while left and len(chosen)<count:
        best=max(left,key=lambda i:len(success[i['id']]-covered))
        if not success[best['id']]-covered:break
        chosen.append(best);covered|=success[best['id']];left.remove(best)
    vals={i['id']:values(rows[i['id']]) for i in left}
    while left and len(chosen)<count:
        best=lexicase(rng,left,vals) if rng else left[0]
        chosen.append(best);left.remove(best)
    return chosen


def candidates(state,assessment):
    items=state['population']+(state['archive']+state['frozen'] if assessment else [])
    registry={}
    for i in items:
        if i['id'] in registry:assert registry[i['id']]==i
        registry[i['id']]=i
    return list(registry.values())


def transition(states,data,results):
    rows=[{} for _ in states]
    for result in results:
        for e in result['entries']:
            for k,identity in e['aliases']:
                assert identity not in rows[k];rows[k][identity]=e['rows']
    states=deepcopy(states);decisions=[]
    for k,s in enumerate(states):
        r=rows[k];meta=data['metadata'];rng=random.Random();rng.setstate(tupled(s['rng']))
        assert set(r)=={i['id'] for i in candidates(s,data['kind']=='assessment')}
        if data['kind']=='assessment':
            pool=candidates(s,True)
            primary=ordered(pool,r,meta)[0];ordinary=ordered(pool,r,meta,True)[0]
            s['nominees']=[primary,ordinary]
            if s['generation']==0:s['frozen']=deepcopy(s['nominees'])
            s['archive']=retain(pool,r,meta,16,4)
            s['assessment_generation']=s['generation']
            decision=dict(name=s['name'],nominees=[i['id'] for i in s['nominees']],ranks=[rank(r[i['id']],meta) for i in s['nominees']],archive=[i['id'] for i in s['archive']],births=[])
        else:
            survivors=retain(s['population'],r,meta,44,16,rng);vals={i['id']:values(r[i['id']]) for i in survivors};births=[]
            for b in range(52):
                identity=f'm1/{s["name"]}/g{s["generation"]+1}/b{b}'
                if s['method']=='resample' or b<7:
                    g=random_genome(s['representation'],rng);parent=None;root=identity;depth=0;event=None
                else:
                    p=lexicase(rng,survivors,vals);g,event=mutation(s['representation'],genome(s['representation'],p['genome']),rng)
                    parent=p['id'];root=p['root'];depth=p['mutation_depth']+1
                child=dict(id=identity,genome=g.to_dict(),root=root,parent=parent,birth=s['generation']+1,mutation_depth=depth)
                births.append(dict(item=child,event=event))
            s['population']=survivors+[b['item'] for b in births];s['generation']+=1
            decision=dict(name=s['name'],survivors=[i['id'] for i in survivors],births=births)
        s['rng']=rng.getstate();assert len(s['population'])==len({i['id'] for i in s['population']})==96
        decisions.append(decision)
    return canonical(states),canonical(decisions)
