"""V13B one partial-score intervention; common reproduction and archives."""
from collections import Counter,defaultdict
from copy import deepcopy
import random
from .exposure_genome import Individual,Genome
from .growth import random_genome,mutate,replay_mutation
from .foundation_fitness import lexicase
from .regulatory_search import tuple_tree
from .shared_prefix_search import nominees,digest
from .exposure_selection import evaluate
import numpy as np
from .composition_search import summary as prior_summary
from .linkage_restart_operator import mutate_ids
from .family_reservoir import retain
from .routing_transfer import canonical

ARMS=('current','selective','resample','frozen')
ARCHIVES=('primary','choice','corridor')

def summary(rs,meta):
    m=prior_summary(rs,meta);pairs=defaultdict(list)
    for r in rs:
        q=meta[r['case']]
        if q['family']=='paired':pairs[q['base'],q['pose']].append(r)
    good={k:meta[v[0]['case']] for k,v in pairs.items() if len(v)==2 and all(r['optimal'] for r in v)}
    for name,pred in [('upstream',lambda q:q['prefix'] in (1,2)),('p2',lambda q:q['prefix']==2),('all',lambda q:True),('long',lambda q:q['prefix']>=4),('prefix4',lambda q:q['prefix']==4),('cycle',lambda q:q['graph']=='cycle' and q['prefix']>0)]:
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
    if name=='primary':return (m['upstream'],m['pairs'],m['corridors'],*tail)
    if name=='choice':return (m['zero'],m['upstream'],m['corridors'],*tail)
    if name=='corridor':return (m['corridors'],m['pairs'],*tail)
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
    if key.startswith('fresh/') and archives:
        s['protected']=list({a['item']['id']:a['item'] for a in archives.values()}.values())
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
    retained,event=retain(records,[r['id'] for r in state['protected']],'current')
    registry={i.identity:i for _,i in rank};selected=[registry[r['id']] for r in retained];elite=[i.identity for i in selected]
    ids={i.identity:state['gene_ids'][i.identity] for i in selected};families={i.identity:state['families'][i.identity] for i in selected};births=[]
    for index in range(52):
        name=f'selectivity_v13b/{state["key"]}/i{state["serial"]+index}'
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

def selectivity(row,o):
    """Evaluator-only score. Exact normal shortest output remains the top tier."""
    if row['optimal']:return 1.
    if not o.path or row['status']!='emitted':return 0.
    mask=np.unpackbits(np.frombuffer(bytes.fromhex(row['mask']),np.uint8),bitorder='little')[:len(o.maze.cells)]
    tp=int(mask[o.path].sum());extra=int(mask.sum())-tp
    if tp==len(o.path):return .5+.49/(1+extra)
    return .49*(tp/len(o.path))**2/(1+extra)

def ranked(population,rows,meta,arm='current'):
    out=[]
    for i in population:
        rr=rows[i.identity]
        # Replace only the partial-score field passed into common ranking/lexicase.
        ev=evaluate([dict(r,partial=r['selectivity']) for r in rr],meta) if arm=='selective' else evaluate(rr,meta)
        ev.rows=rr
        out.append((ev,i))
    return sorted(out,key=lambda x:(tuple(-v for v in x[0].fitness),x[1].genome.digest,x[1].identity))

def gate(target,controls,frozen,meta):
    keys=lambda m,n:set(tuple(k) if isinstance(k,list) else k for k in m[n+'_keys'])
    new=keys(target,'upstream')-keys(frozen,'upstream');newp2=keys(target,'p2')-keys(frozen,'p2')
    lookup={(m['base'],m['pose']):m for m in meta.values() if m['family']=='paired'}
    contexts={lookup[k]['template'] for k in new};poses={k[1] for k in new}
    retention={n:len(keys(target,n)&keys(frozen,n))/len(keys(frozen,n)) if keys(frozen,n) else 1. for n in ('all','corridor')}
    checks=dict(new_upstream=len(new)>=8,new_prefix2=len(newp2)>=4,above_controls=all(target['upstream']>=m['upstream']+8 for m in controls),contexts=len(contexts)>=2,poses=len(poses)>=2,retention=all(v>=.95 for v in retention.values()),false_no_path=target['false_no_path']<=frozen['false_no_path'])
    return dict(passed=all(checks.values()),checks=checks,new_upstream=len(new),new_prefix2=len(newp2),new_contexts=len(contexts),retention=retention)
