"""V12Z asexual comparison. Only survivor policy differs between mutation arms."""
from collections import Counter,defaultdict
from copy import deepcopy
import random
from .exposure_genome import Individual,Genome
from .growth import random_genome,mutate,replay_mutation
from .foundation_fitness import lexicase
from .regulatory_search import tuple_tree
from .shared_prefix_search import ranked,nominees,digest
from .composition_search import summary as prior_summary
from .linkage_restart_operator import mutate_ids
from .family_reservoir import retain
from .routing_transfer import canonical

ARMS=('current_mutation','family_mutation','resample','frozen')
ARCHIVES=('primary','choice','corridor')

def summary(rs,meta):
    m=prior_summary(rs,meta);pairs=defaultdict(list)
    for r in rs:
        q=meta[r['case']]
        if q['family']=='paired':pairs[q['base'],q['pose']].append(r)
    good={k:meta[v[0]['case']] for k,v in pairs.items() if len(v)==2 and all(r['optimal'] for r in v)}
    for name,pred in [('all',lambda q:True),('long',lambda q:q['prefix']>=4),('prefix4',lambda q:q['prefix']==4),('cycle',lambda q:q['graph']=='cycle' and q['prefix']>0)]:
        keys=sorted(k for k,q in good.items() if pred(q));m[name+'_keys']=[list(k) for k in keys];m[name]=len(keys)
        m[name+'_contexts']=sorted({good[k]['template'] for k in keys})
    for name,pred in [('corridor',lambda q:q['family']=='corridor'),('ordinary',lambda q:q['family'] in ('ordinary_random','ordinary_perfect'))]:
        keys=sorted(r['case'] for r in rs if r['optimal'] and pred(meta[r['case']]))
        m[name+'_keys']=keys;m[name]=len(keys)
    m['ordinary_no_path']=sum(r['no_path'] for r in rs if meta[r['case']]['family']=='ordinary_disconnected')
    m['prefix8']=sum(q['prefix']==8 for q in good.values())
    return m

def archive_rank(m,name):
    tail=(m['no_path']-m['false_no_path'],m['partial'])
    if name=='primary':return (m['long'],m['cycle'],m['positive'],m['pairs'],m['corridors'],m['ordinary'],*tail)
    if name=='choice':return (m['zero'],m['positive'],m['long'],m['corridors'],*tail)
    if name=='corridor':return (m['corridors'],m['ordinary'],m['pairs'],*tail)
    raise ValueError(name)

def update_archives(aa,i,m,g,metadata):
    for name in ARCHIVES:
        rank=archive_rank(m,name);old=aa.get(name)
        if old is None or (tuple(-v for v in rank),i.genome.digest,i.identity)<(tuple(-v for v in old['rank']),old['digest'],old['item']['id']):
            aa[name]=dict(item=i.save(),digest=i.genome.digest,rank=list(rank),metrics=m,generation=g,ancestry=deepcopy(metadata))

def assert_population(s):
    pop=s['population'];ids=[r['id'] for r in pop]
    assert len(pop)==len(set(ids))==96,'Population identity collision'
    assert set(s['gene_ids'])==set(s['families'])==set(ids)
    registry={r['id']:r for r in pop}
    for r in pop:
        genes=s['gene_ids'][r['id']]
        assert len(genes)==len(set(genes))==len(r['genome']['genes'])<=256
    for r in s['protected']:assert registry[r['id']]==r,'Protected identity overwritten'

def init_state(key,pool,archives=None):
    s=dict(key=key,arm=key.split('/')[-1],population=deepcopy(pool['items']),protected=deepcopy(pool['protected']),gene_ids=deepcopy(pool['gene_ids']),families=deepcopy(pool['families']),rng=deepcopy(pool['search_rng']),serial=0,generation=0,archives=deepcopy(archives or {}))
    assert_population(s);return s

def lineage(s,i):return dict(family=s['families'][i.identity],gene_ids=s['gene_ids'][i.identity])

def family_stats(s):
    protected={r['id'] for r in s['protected']};members=[r for r in s['population'] if r['id'] not in protected]
    counts=Counter(s['families'][r['id']] for r in members);n=len(members)
    return dict(mutable=len(members),families=len(counts),effective=n*n/sum(x*x for x in counts.values()),unique_genotypes=len({Individual.load(r).genome.digest for r in members}),largest=max(counts.values()))

def reproduce(state,rank,archives):
    assert_population(state)
    if state['arm']=='frozen':
        out=deepcopy(state);out['generation']+=1;out['archives']=deepcopy(archives)
        return out,dict(key=state['key'],generation=state['generation'],frozen=True,births=[],population=digest(out['population']),families=family_stats(out))
    rng=random.Random();rng.setstate(tuple_tree(state['rng']));before=rng.getstate()
    records=[dict(id=i.identity,family=state['families'][i.identity],genotype=i.genome.digest,gene_ids=state['gene_ids'][i.identity],genes=i.save()['genome']['genes'],behavior=digest([(r['mask'],r['status']) for r in ev.rows])) for ev,i in rank]
    retained,event=retain(records,[r['id'] for r in state['protected']],'family' if state['arm']=='family_mutation' else 'current')
    registry={i.identity:i for _,i in rank};selected=[registry[r['id']] for r in retained];elite=[i.identity for i in selected]
    ids={i.identity:state['gene_ids'][i.identity] for i in selected};families={i.identity:state['families'][i.identity] for i in selected};births=[]
    for index in range(52):
        name=f'family_z/{state["key"]}/i{state["serial"]+index}'
        assert name not in registry and name not in ids
        parent=None;events=None
        if state['arm']=='resample' or index<7:
            genome=Genome(random_genome(rng,True),7);genes=[name+f'/gene{k}' for k in range(len(genome.genes))];family=name
        else:
            parent=rng.choice(rank)[1] if rng.random()<.1 else lexicase(rng,rank)
            program,events=mutate(parent.genome.program,rng,1,256,True)
            assert replay_mutation(parent.genome.program,events,256)==program
            genome=Genome(program,7);genes=mutate_ids(state['gene_ids'][parent.identity],events,name);family=state['families'][parent.identity]
        item=Individual(name,genome,parent.identity if parent else None,state['generation']+1)
        births.append(dict(item=item.save(),gene_ids=genes,family=family,parents=[parent.identity] if parent else [],mutation=events))
        selected.append(item);ids[name]=genes;families[name]=family
    new=deepcopy(state);new.update(population=[i.save() for i in selected],gene_ids=ids,families=families,rng=canonical(rng.getstate()),serial=state['serial']+52,generation=state['generation']+1,archives=deepcopy(archives))
    assert_population(new)
    packet=dict(generation=state['generation'],key=state['key'],elite=elite,retention=event,births=births,rng_before=digest(before),rng_after=digest(rng.getstate()),population=digest(new['population']),train_fitness={i.identity:list(ev.fitness) for ev,i in rank},families=family_stats(new))
    return canonical(new),canonical(packet)

def gate(target,controls,frozen,meta):
    keys=lambda m,n:set(tuple(k) if isinstance(k,list) else k for k in m[n+'_keys'])
    new=keys(target,'prefix4')-keys(frozen,'prefix4')
    contexts={meta[next(c for c,q in meta.items() if q['family']=='paired' and (q['base'],q['pose'])==k)]['template'] for k in new}
    retention={n:len(keys(target,n)&keys(frozen,n))/max(1,len(keys(frozen,n))) if keys(frozen,n) else 1. for n in ('all','corridor','ordinary')}
    newcycle=keys(target,'cycle')-keys(frozen,'cycle')
    checks=dict(new_prefix4=len(new)>=16,above_controls=all(target['prefix4']>=c['prefix4']+16 for c in controls),independent_contexts=len(contexts)>=2,new_cycle=len(newcycle)>=8,retention=all(v>=.95 for v in retention.values()),false_no_path=target['false_no_path']<=frozen['false_no_path'])
    return dict(passed=all(checks.values()),checks=checks,new_prefix4=len(new),new_contexts=len(contexts),new_cycle=len(newcycle),retention=retention)
