"""V12K: one context-consistency field, with identical common archives/runtime."""
from collections import defaultdict
from copy import deepcopy
import json,random
from .foundation_calibration import LIMITS
from .foundation_pair_confirm import normal_row
from .growth_runtime import Organism
from .growth import Individual,random_genome,mutate
from .regulatory_search import Evaluation,tuple_tree
from .fork_search import digest
from .fork_fitness import lexicase
from .robustness_data import BRANCHES

ARCHIVES=('context','pair','corridor','distance')


def annotate(rows,meta):
    groups=defaultdict(list);pairs=defaultdict(list)
    for r in rows:
        m=meta[r['case']];r.update(base=m['base'],family=m['family'],pose=m['pose'],prefix=m['prefix'],
            branch=m['family'] in BRANCHES,pair_optimal=False,context_complete=False,paired_partial=0.)
        if r['branch']:pairs[(m['base'],m['family'],m['pose'])].append(r)
    for pair in pairs.values():
        assert len(pair)==2
        complete=all(r['optimal'] for r in pair);weak=min(r['partial'] for r in pair)
        for r in pair:r.update(pair_optimal=complete,paired_partial=weak)
        groups[(pair[0]['base'],pair[0]['family'])].append(pair)
    for group in groups.values():
        full=all(p[0]['pair_optimal'] for p in group)
        for pair in group:
            for r in pair:r['context_complete']=full
    return rows


def ranks(rows,policy):
    contexts=len({(r['base'],r['family']) for r in rows if r['context_complete']})
    pairs=sum(r['pair_optimal'] for r in rows)//2
    work=sum(r['reads']+r['dispatches'] for r in rows)
    return (contexts if policy=='context' else 0,pairs,sum(r['optimal'] for r in rows),sum(r['valid'] for r in rows),
        sum(r['no_path'] for r in rows)-sum(r['reachable'] and r['status']=='no_path' for r in rows),
        round(sum(r['partial']+r['paired_partial'] for r in rows),8),
        -work if all(r['optimal'] or r['no_path'] for r in rows) else 0)


def archive_rank(rows,name):
    if name=='corridor':rows=[r for r in rows if r['family'].startswith('corridor')]
    if name=='distance':rows=[r for r in rows if r['branch'] and r['prefix']>=4]
    return ranks(rows,'context' if name=='context' else 'pair')


def result(rows,meta,policy):
    annotate(rows,meta)
    values=[(int(r['context_complete']) if policy=='context' else 0,int(r['pair_optimal']),
        int(r['optimal'] or r['no_path']),int(r['valid'] or r['no_path']),r['partial']+r['paired_partial']) for r in rows]
    descriptor=(tuple(int(r['valid']) for r in rows),tuple(min(7,int(r['partial']*8)) for r in rows),
        min(3,max(r['steps'] for r in rows)//16),int(any(sum(r['range_reads'][1:]) for r in rows)))
    return Evaluation(ranks(rows,policy),values,descriptor,rows,sum(r['reads']+r['dispatches'] for r in rows))


def evaluate(item,ids,cases,meta,topology,policy,budget=None):
    org=Organism(item.genome,topology,LIMITS);rows=[]
    for cid in ids:
        o=cases[cid];m=o.maze
        fn=lambda:org.react(m.cells,m.w,m.h,m.start,m.goal)
        r=budget.call(fn) if budget else fn()
        rows.append(normal_row(r,o))
    return result(rows,meta,policy)


class Search:
    def __init__(self,state,registry,log,cases,meta,budget=None):
        self.config=deepcopy(state['config']);self.key=state['key']
        self.population=[Individual.load(i) for i in state['population']]
        self.protected=[Individual.load(i) for i in state['protected']]
        self.rng=random.Random();self.rng.setstate(tuple_tree(state['rng_state']))
        for k in ('serial','generation','responses','work','archives','frozen','history'):setattr(self,k,deepcopy(state[k]))
        self.registry,self.log,self.cases,self.meta,self.budget=registry,log,cases,meta,budget

    def evaluate(self,item,ids,split):
        ev=evaluate(item,ids,self.cases,self.meta,self.config['topology'],self.config['policy'],self.budget)
        self.responses+=len(ev.rows);self.work+=ev.work
        self.log.write(json.dumps(dict(condition=self.key,id=item.identity,generation=self.generation,split=split,
            fitness=ev.fitness,descriptor=ev.descriptor,work=ev.work,cases=ev.rows),separators=(',',':'))+'\n')
        return ev

    def archive(self,item,ev):
        for name in ARCHIVES:
            rank=archive_rank(ev.rows,name)
            old=self.archives.get(name)
            if old is None or rank>tuple(old['rank']) or (rank==tuple(old['rank']) and item.genome.digest<Individual.load(old['item']).genome.digest):
                self.archives[name]=dict(item=item.save(),rank=rank,rows=ev.rows,generation=self.generation)

    def initialize(self,ids):
        for item in self.population:self.archive(item,self.evaluate(item,ids,'initial'))
        self.frozen=deepcopy(self.archives)

    def create(self,genome,parent,events=None):
        item=Individual(f'{self.key}/i{self.serial}',genome,parent,self.generation+1);self.serial+=1
        self.registry.write(json.dumps(dict(**item.save(),condition=self.key,events=events),separators=(',',':'))+'\n')
        return item

    def step(self,ids,validation):
        before=self.rng.getstate();evaluated=[(self.evaluate(i,ids,'train'),i) for i in self.population]
        ranked=sorted(evaluated,key=lambda x:x[0].fitness,reverse=True);nominees=[]
        if self.generation%8==0:
            seen=set()
            for ev,item in ranked:
                if item.genome.digest not in seen:nominees.append(item);seen.add(item.genome.digest)
                if len(nominees)==4:break
            for _,item in ranked:
                if len(nominees)==4:break
                if item.identity not in {i.identity for i in nominees}:nominees.append(item)
            for item in nominees:self.archive(item,self.evaluate(item,validation,'validation'))
        selected=[];seen=set();descriptors=set()
        def add(item):
            if item.identity not in seen and len(selected)<24:selected.append(item);seen.add(item.identity)
        for item in self.protected:add(item)
        for name in ARCHIVES:add(Individual.load(self.archives[name]['item']))
        add(ranked[0][1])
        for ev,item in ranked:
            if ev.descriptor not in descriptors:add(item);descriptors.add(ev.descriptor)
        for _,item in ranked:add(item)
        assert len(selected)==24
        elite=[i.identity for i in selected];births=[]
        for index in range(72):
            if self.config['method']=='resample' or index<9:item=self.create(random_genome(self.rng,True),None)
            else:
                parent=self.rng.choice(ranked)[1] if self.rng.random()<.1 else lexicase(self.rng,ranked)
                genome,events=mutate(parent.genome,self.rng,1,256,True);item=self.create(genome,parent.identity,events)
            births.append(item.identity);selected.append(item)
        best={}
        for p in ('pair','context'):
            maximum=max(ranks(ev.rows,p) for ev,_ in evaluated)
            best[p]=sorted({i.genome.digest for ev,i in evaluated if ranks(ev.rows,p)==maximum})
        self.history.append(dict(generation=self.generation,elite=elite,births=births,nominees=[i.identity for i in nominees],
            rng_before=digest(before),rng_after=digest(self.rng.getstate()),population_sha256=digest([i.genome.digest for i in selected]),
            unique=len({i.genome.digest for _,i in ranked}),top_sets_differ=best['pair']!=best['context'],train_best=ranked[0][0].fitness,
            archives={n:dict(rank=a['rank'],id=a['item']['id'],generation=a['generation']) for n,a in self.archives.items()}))
        self.population=selected;self.generation+=1

    def state(self):
        return dict(config=self.config,key=self.key,population=[i.save() for i in self.population],protected=[i.save() for i in self.protected],
            rng_state=self.rng.getstate(),serial=self.serial,generation=self.generation,responses=self.responses,work=self.work,
            archives=self.archives,frozen=self.frozen,history=self.history)
