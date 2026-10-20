"""V12X-R1 common selection and replayable ancestry; operator feasibility only."""
from copy import deepcopy
import random
from .exposure_genome import Individual,Genome
from .growth import random_genome,mutate,replay_mutation
from .foundation_fitness import lexicase
from .regulatory_search import tuple_tree
from .shared_prefix_search import ranked,digest
from .composition_operator import rows
from .linkage_restart_operator import candidates,transfer,mutate_ids,retained_changes
from .routing_transfer import canonical

ARMS=('linked','unlinked','sham','mutation','resample','frozen')
SEXUAL=('linked','unlinked','sham')

def assert_population(state):
    pop=state['population'];identities=[r['id'] for r in pop]
    assert len(pop)==len(set(identities))==96, 'Population identity collision'
    assert set(state['gene_ids'])==set(identities)
    registry={r['id']:r for r in pop}
    for raw in pop:
        ids=state['gene_ids'][raw['id']]
        assert len(ids)==len(set(ids))==len(raw['genome']['genes']), 'Gene identity mapping mismatch'
    for raw in state['protected']:assert registry[raw['id']]==raw, 'Protected identity overwritten'

def init_state(key,pool):
    state=dict(key=key,arm=key.split('/')[-1],population=deepcopy(pool['items']),protected=deepcopy(pool['protected']),
        gene_ids=deepcopy(pool['gene_ids']),rng=deepcopy(pool['search_rng']),serial=0,generation=0)
    assert_population(state);return state

def donor_choice(rng,rank,parent,ids):
    shortlist=[lexicase(rng,rank) for _ in range(4)]+[rng.choice(rank)[1] for _ in range(4)]
    evs={i.identity:e for e,i in rank};pe=evs[parent.identity];eligible=[];seen=set()
    for donor in shortlist:
        if donor.identity in seen or donor.genome.digest==parent.genome.digest:continue
        seen.add(donor.identity)
        opts=candidates(rows(parent.genome.program),rows(donor.genome.program),tuple(ids[parent.identity]),tuple(ids[donor.identity]))
        if not opts:continue
        de=evs[donor.identity];gains=tuple(sum(max(0,b[j]-a[j]) for a,b in zip(pe.case_values,de.case_values)) for j in range(4))
        eligible.append((gains,donor))
    eligible.sort(key=lambda x:(tuple(-v for v in x[0]),x[1].genome.digest,x[1].identity))
    packet=dict(shortlist=[i.identity for i in shortlist],eligible=[i.identity for _,i in eligible])
    if not eligible:return None,dict(packet,reason='no_homologous_variant')
    return eligible[0][1],dict(packet,reason='common_pool',gains=list(eligible[0][0]))

def reproduce(state,rank):
    assert_population(state)
    if state['arm']=='frozen':
        out=deepcopy(state);out['generation']+=1
        return out,dict(key=state['key'],generation=state['generation'],frozen=True,population=digest(out['population']))
    rng=random.Random();rng.setstate(tuple_tree(state['rng']));before=rng.getstate();selected=[];seen=set();ids=state['gene_ids']
    def add(i):
        if len(selected)<24 and i.identity not in seen:selected.append(i);seen.add(i.identity)
    for raw in state['protected']:add(Individual.load(raw))
    add(rank[0][1]);behaviors=set()
    for ev,i in rank:
        b=digest([(r['mask'],r['status']) for r in ev.rows])
        if b not in behaviors:add(i);behaviors.add(b)
    for _,i in rank:add(i)
    assert len(selected)==24
    newids={i.identity:ids[i.identity] for i in selected};elite=[i.identity for i in selected];births=[]
    for index in range(72):
        name=f'linkage_x2/{state["key"]}/i{state["serial"]+index}';assert name not in ids and name not in newids
        parent=donor=None;cross=mate=events=None;retained=0
        if state['arm']=='resample' or index<9:
            genome=Genome(random_genome(rng,True),7);geneids=[name+f'/gene{k}' for k in range(len(genome.genes))]
        else:
            parent=rng.choice(rank)[1] if rng.random()<.1 else lexicase(rng,rank)
            program=parent.genome.program;geneids=list(ids[parent.identity])
            if state['arm'] in SEXUAL and (index-9)%2==0:
                donor,mate=donor_choice(rng,rank,parent,ids)
                if donor is not None:program,geneids,cross=transfer(program,donor.genome.program,geneids,ids[donor.identity],rng,state['arm'])
            premutation=program;program,events=mutate(program,rng,1,256,True)
            assert replay_mutation(premutation,events,256)==program
            geneids=mutate_ids(geneids,events,name);genome=Genome(program,7)
            if donor is not None:retained=retained_changes(parent.genome.program,ids[parent.identity],donor.genome.program,ids[donor.identity],cross,program,geneids)
        i=Individual(name,genome,parent.identity if parent else None,state['generation']+1)
        parents=[parent.identity] if parent else []
        if cross and cross['accepted']:parents.append(donor.identity)
        births.append(dict(item=i.save(),gene_ids=geneids,parents=parents,mutation=events,crossover=cross,mating=mate,
            proposed_donor=donor.identity if donor else None,retained_donor_changes=retained))
        selected.append(i);newids[name]=geneids
    new=deepcopy(state);new.update(population=[i.save() for i in selected],gene_ids=newids,rng=canonical(rng.getstate()),serial=state['serial']+72,generation=state['generation']+1)
    assert_population(new)
    event=dict(generation=state['generation'],key=state['key'],elite=elite,births=births,rng_before=digest(before),rng_after=digest(rng.getstate()),population=digest(new['population']),train_fitness={i.identity:list(ev.fitness) for ev,i in rank})
    return canonical(new),canonical(event)
