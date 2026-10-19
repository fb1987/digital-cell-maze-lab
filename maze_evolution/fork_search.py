"""V12G matched search with common protected archives and one pressure contrast."""
from copy import deepcopy
import hashlib,json,random
from .foundation_calibration import LIMITS
from .fork_fitness import evaluate,ranks,lexicase
from .growth import Individual,random_genome,mutate
from .regulatory_search import tuple_tree


def digest(value):return hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()


def archive_rank(rows,name):
    if name=='pair':return ranks([r for r in rows if r['fork']],'pair_archive')
    if name=='choice':return ranks([r for r in rows if r['fork']],'choice_archive')
    if name=='task':return ranks(rows,'current')
    if name=='corridor':return ranks([r for r in rows if not r['fork']],'current')
    raise ValueError(name)


class Search:
    def __init__(self,state,registry,log):
        self.state0=deepcopy(state);self.config=state['config'];self.key=state['key']
        self.population=[Individual.load(i) for i in state['population']]
        self.protected=[Individual.load(i) for i in state['protected']]
        self.rng=random.Random();self.rng.setstate(tuple_tree(state['rng_state']))
        for k in ('serial','generation','responses','work','archives','frozen','history'):setattr(self,k,deepcopy(state[k]))
        self.registry,self.log=registry,log

    def evaluate(self,item,pairs,split):
        ev=evaluate(item,pairs,self.config['topology'],LIMITS,self.config['policy'])
        self.responses+=len(ev.rows);self.work+=ev.work
        self.log.write(json.dumps(dict(condition=self.key,id=item.identity,generation=self.generation,split=split,fitness=ev.fitness,descriptor=ev.descriptor,work=ev.work,cases=ev.rows),separators=(',',':'))+'\n')
        return ev

    def archive(self,item,ev):
        for name in ('pair','choice','task','corridor'):
            rank=archive_rank(ev.rows,name)
            if name not in self.archives or rank>tuple(self.archives[name]['rank']):
                self.archives[name]=dict(item=item.save(),rank=rank,rows=ev.rows,generation=self.generation)

    def initialize(self,pairs):
        for item in self.population:self.archive(item,self.evaluate(item,pairs,'initial'))
        self.frozen=deepcopy(self.archives)

    def create(self,genome,parent,events=None):
        item=Individual(f'{self.key}/i{self.serial}',genome,parent,self.generation+1);self.serial+=1
        self.registry.write(json.dumps(dict(**item.save(),condition=self.key,events=events),separators=(',',':'))+'\n')
        return item

    def step(self,pairs,validation):
        before=self.rng.getstate()
        evaluated=[(self.evaluate(i,pairs,'train'),i) for i in self.population]
        ranked=sorted(evaluated,key=lambda x:x[0].fitness,reverse=True)
        nominees=[]
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
        for name in ('pair','choice','task','corridor'):add(Individual.load(self.archives[name]['item']))
        add(ranked[0][1])
        for ev,item in ranked:
            if ev.descriptor not in descriptors:add(item);descriptors.add(ev.descriptor)
        for _,item in ranked:add(item)
        assert len(selected)==24
        elite=[i.identity for i in selected];births=[]
        for index in range(72):
            if self.config['method']=='resample' or index<9:
                item=self.create(random_genome(self.rng,True),None)
            else:
                parent=self.rng.choice(ranked)[1] if self.rng.random()<.1 else lexicase(self.rng,ranked)
                genome,events=mutate(parent.genome,self.rng,1,256,True)
                item=self.create(genome,parent.identity,events)
            births.append(item.identity);selected.append(item)
        best={}
        for p in ('current','branch'):
            maximum=max(ranks(ev.rows,p) for ev,_ in evaluated)
            best[p]=sorted({i.genome.digest for ev,i in evaluated if ranks(ev.rows,p)==maximum})
        record=dict(generation=self.generation,elite=elite,births=births,nominees=[i.identity for i in nominees],
            rng_before=digest(before),rng_after=digest(self.rng.getstate()),population_sha256=digest([i.genome.digest for i in selected]),
            unique=len({i.genome.digest for _,i in ranked}),max_genes=max(len(i.genome.genes) for _,i in ranked),
            top_sets_differ=best['current']!=best['branch'],train_best=ranked[0][0].fitness,
            train_strict_responses=sum(r['pair_strict'] for ev,_ in ranked for r in ev.rows)//2,
            train_complete_pairs=sum(r['pair_optimal'] and r['fork'] for ev,_ in ranked for r in ev.rows)//2,
            archives={n:dict(rank=a['rank'],id=a['item']['id'],generation=a['generation']) for n,a in self.archives.items()})
        self.history.append(record);self.population=selected;self.generation+=1

    def state(self):
        return dict(config=self.config,key=self.key,population=[i.save() for i in self.population],protected=[i.save() for i in self.protected],
            rng_state=self.rng.getstate(),serial=self.serial,generation=self.generation,responses=self.responses,work=self.work,
            archives=self.archives,frozen=self.frozen,history=self.history)
