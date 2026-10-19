"""V12S: common selection, compatible complementary mating, exact replayable births."""
from copy import deepcopy
import random
from .exposure_genome import Individual,Genome
from .growth import random_genome,mutate,replay_mutation
from .composition_operator import rows,sites,splice,replay_splice
from .shared_prefix_search import summary as old_summary,ranked,nominees,digest
from .foundation_fitness import lexicase
from .regulatory_search import tuple_tree
from .routing_transfer import canonical

ARMS=('mutation','recombination','resample')
ARCHIVES=('primary','choice','corridor')

def summary(rs,meta):
    m=old_summary(rs,meta)
    by=m['by'];m['positive']=sum(x['pairs'] for k,x in by.items() if not k.endswith('/p0'))
    # Explicit matched pair identities, independent of whether core or stress.
    from collections import defaultdict
    pairs=defaultdict(list)
    for r in rs:
        q=meta[r['case']]
        if q['family']=='paired':pairs[q['base'],q['pose']].append(r)
    good=[k for k,rr in pairs.items() if all(r['optimal'] for r in rr) and meta[rr[0]['case']]['prefix']>0]
    m['positive_keys']=[list(k) for k in sorted(good)]
    m['positive_contexts']=sorted({meta[pairs[k][0]['case']]['template'] for k in good})
    m['positive_poses']=sorted({k[1] for k in good})
    m['stress_positive']=sum(meta[pairs[k][0]['case']]['graph']!='fork' for k in good)
    grouped=defaultdict(list)
    for k,rr in pairs.items():
        q=meta[rr[0]['case']]
        if q['prefix']>0:grouped[k[0]].append(all(r['optimal'] for r in rr))
    m['positive_full_groups']=sum(len(v)==8 and all(v) for v in grouped.values())
    return m

def archive_rank(m,name):
    tail=(m['no_path']-m['false_no_path'],m['partial'])
    if name=='primary':return (m['positive'],m['stress_positive'],m['pairs'],m['corridors'],*tail)
    if name=='choice':return (m['zero'],m['positive'],m['corridors'],*tail)
    if name=='corridor':return (m['corridors'],m['no_path']-m['false_no_path'],m['pairs'],m['partial'])
    raise ValueError(name)

def update_archives(aa,i,m,g):
    for name in ARCHIVES:
        rank=archive_rank(m,name);old=aa.get(name)
        if old is None or (tuple(-v for v in rank),i.genome.digest,i.identity)<(tuple(-v for v in old['rank']),old['digest'],old['item']['id']):
            aa[name]=dict(item=i.save(),digest=i.genome.digest,rank=list(rank),metrics=m,generation=g)

def donor_choice(rng,rank,parent):
    # Four fitness-selected and four uniform candidates; bounded without replacement
    # at final identity filtering. Scores use only the current training batch.
    candidates=[lexicase(rng,rank) for _ in range(4)]+[rng.choice(rank)[1] for _ in range(4)]
    evaluations={i.identity:ev for ev,i in rank};ev=evaluations[parent.identity];options=[];seen=set()
    for donor in candidates:
        if donor.identity in seen or donor.genome.digest==parent.genome.digest:continue
        seen.add(donor.identity)
        eligible=sites(rows(parent.genome.program),rows(donor.genome.program))
        if not eligible:continue
        de=evaluations[donor.identity]
        gains=tuple(sum(max(0,b[j]-a[j]) for a,b in zip(ev.case_values,de.case_values)) for j in range(4))
        options.append((gains,donor))
    if not options:return None,dict(shortlist=[x.identity for x in candidates],eligible=[],reason='no_compatible_donor')
    options.sort(key=lambda x:(tuple(-v for v in x[0]),x[1].genome.digest,x[1].identity))
    d=options[0][1]
    return d,dict(shortlist=[x.identity for x in candidates],eligible=[x.identity for _,x in options],gains=list(options[0][0]),reason='compatible')

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
        parent=None;donor=None;cross=None;mate=None;events=None
        if state['arm']=='resample' or index<9:genome=Genome(random_genome(rng,True),7)
        else:
            parent=rng.choice(rank)[1] if rng.random()<.1 else lexicase(rng,rank)
            program=parent.genome.program
            # Fixed half of non-immigrant births attempt recombination; others mutate.
            if state['arm']=='recombination' and (index-9)%2==0:
                donor,mate=donor_choice(rng,rank,parent)
                if donor is not None:
                    program,cross=splice(parent.genome.program,donor.genome.program,rng)
                    assert replay_splice(parent.genome.program,donor.genome.program,cross)==program
            before_mutation=program;program,events=mutate(program,rng,1,256,True)
            assert replay_mutation(before_mutation,events,256)==program
            genome=Genome(program,7)
        i=Individual(f'{state["key"]}/i{state["serial"]+index}',genome,parent.identity if parent else None,state['generation']+1)
        births.append(dict(item=i.save(),parents=([parent.identity]+([donor.identity] if donor else [])) if parent else [],
            mutation=events,crossover=cross,mating=mate));selected.append(i)
    new=deepcopy(state);new.update(population=[i.save() for i in selected],rng=canonical(rng.getstate()),serial=state['serial']+72,generation=state['generation']+1,archives=deepcopy(archives))
    event=dict(generation=state['generation'],key=state['key'],elite=elite,births=births,
        rng_before=digest(before),rng_after=digest(rng.getstate()),population=digest(new['population']),train_fitness={i.identity:list(ev.fitness) for ev,i in rank})
    return canonical(new),canonical(event)

def gate(target,asexual,resample,frozen):
    new=set(map(tuple,target['positive_keys']))-set(map(tuple,frozen['positive_keys']))
    return bool(len(new)>=16 and target['positive']>=max(asexual['positive'],resample['positive'],frozen['positive'])+16
        and target['positive_full_groups']>=2 and target['stress_positive']>=8
        and len(target['positive_contexts'])>=4 and target['zero']>=.95*frozen['zero']
        and target['corridors']>=.95*frozen['corridors'] and target['false_no_path']<=frozen['false_no_path'])
