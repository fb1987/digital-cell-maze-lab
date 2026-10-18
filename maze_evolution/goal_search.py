"""V4 paired-goal evolution with one shared protected signalling elite."""
import copy
import hashlib
import json
from pathlib import Path
import random
import time
import numpy as np
from .regulatory import Genome,mutate,random_genome
from .regulatory_search import Individual,lexicase,tuple_tree
from .runtime import Limits
from .goal_fitness import evaluate


def record(item,ev,label):
    rank=ev.fitness if label=='task' else (ev.long_signal,ev.fitness[0],ev.fitness[1]) if label=='transmission' else (ev.goal_score,ev.fitness[0],ev.fitness[1])
    return dict(individual=item.save(),rank=list(rank),signal=ev.long_signal,goal=ev.goal_score,
        quality=ev.goal_quality,specificity=ev.goal_specificity,both=ev.pair_both,
        goal_families=ev.goal_families,valid=ev.fitness[0],optimal=ev.fitness[1])


def search(config,batches,validation,registry,evaluations,history,checkpoint,fork=None,
           resume=None,deadline=None,progress=True):
    if not 4<=config['population']<=128 or not 1<=config['generations']<=1000:
        raise ValueError('Unbounded V4 search')
    immutable={k:v for k,v in config.items() if k!='generations'}
    key=f"goal/{config['topology']}/{config['pressure']}/{config['replicate']}"
    rng=random.Random(0); serial=0; start_generation=0; total_work=total_evaluations=0
    train_limits=Limits(**config['train_limits']); eval_limits=Limits(**config['eval_limits'])
    archives={}
    def create(genome,parent,birth):
        nonlocal serial
        item=Individual(f'{key}/i{serial}',genome,parent,birth); serial+=1
        registry.write(json.dumps(item.save(),separators=(',',':'))+'\n');return item
    def evaluate_log(item,pairs,generation,split,limits):
        nonlocal total_work,total_evaluations
        ev=evaluate(item,pairs,config['topology'],limits,config['pressure'],config['horizon'])
        total_work+=ev.work;total_evaluations+=2*len(pairs)
        evaluations.write(json.dumps(dict(condition=key,id=item.identity,generation=generation,split=split,
            fitness=ev.fitness,descriptor=ev.descriptor,work=ev.work,inference_work=ev.inference_work,
            probe_work=ev.probe_work,signal=ev.long_signal,goal=ev.goal_score,quality=ev.goal_quality,
            specificity=ev.goal_specificity,both=ev.pair_both,goal_families=ev.goal_families,
            cases=ev.rows),separators=(',',':'))+'\n')
        return ev
    def update(item,ev):
        for label in ('task','transmission','goal'):
            candidate=record(item,ev,label)
            if label not in archives or tuple(candidate['rank'])>tuple(archives[label]['rank']):archives[label]=candidate
    if resume is not None:
        saved=json.loads(Path(resume).read_text())
        if saved['config']!=immutable:raise ValueError('Resume configuration differs')
        rng.setstate(tuple_tree(saved['rng_state']));serial=saved['serial'];start_generation=saved['next_generation']
        population=[Individual.load(x) for x in saved['population']]
        archives=saved['archives'];frozen=saved['frozen'];initial_digests=saved['initial_digests']
        fork_injection=saved['fork_injection'];protected=saved['protected']
        total_work=saved['total_work'];total_evaluations=saved['total_evaluations']
    else:
        if fork is None:raise ValueError('An explicit random-origin V3 fork is required')
        raw=Path(fork).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=config['fork_sha256']:raise ValueError('Fork hash differs')
        ancestor=json.loads(raw); ac=ancestor['config']
        if ac.get('search_version')!=3 or ac.get('origin')!='random' or ac.get('pressure')!='causal' or ac['topology']!=config['topology']:
            raise ValueError('Expected a matching V3 causal random-origin checkpoint')
        parents=list(ancestor['population'])
        if len(parents)!=config['population']:raise ValueError('Fork population size differs')
        learned=ancestor['transmission']; learned_digest=Genome.from_dict(learned['genome']).digest
        injected=learned_digest not in {Genome.from_dict(p['genome']).digest for p in parents}
        fork_injection=dict(injected=injected,learned_parent=learned['id'],
                            replaced_parent=parents[-1]['id'] if injected else None)
        if injected:parents[-1]=learned
        rng.setstate(tuple_tree(ancestor['rng_state']))
        population=[create(Genome.from_dict(p['genome']),p['id'],0) for p in parents]
        initial_digests=[i.genome.digest for i in population]
        protected=next(i.save() for i in population if i.genome.digest==learned_digest)
        for item in population:update(item,evaluate_log(item,validation,-1,'validation',eval_limits))
        frozen=copy.deepcopy(archives)
    for generation in range(start_generation,config['generations']):
        pairs=batches(generation)
        ranked=[(evaluate_log(i,pairs,generation,'train',train_limits),i) for i in population]
        rng.shuffle(ranked);ranked.sort(key=lambda x:x[0].fitness,reverse=True)
        niches={}
        for ev,item in ranked:niches.setdefault(ev.descriptor,(ev,item))
        nominees=[]
        for item in (ranked[0][1],max(ranked,key=lambda x:x[0].long_signal)[1],max(ranked,key=lambda x:x[0].goal_score)[1]):
            if item.identity not in {i.identity for i in nominees}:nominees.append(item)
        if generation%10==0:
            for _,item in list(niches.values())[:3]:
                if item.identity not in {i.identity for i in nominees}:nominees.append(item)
        for item in nominees:update(item,evaluate_log(item,validation,generation,'validation',eval_limits))
        history.append(dict(condition=key,generation=generation,niches=len(niches),
            unique=len({i.genome.digest for i in population}),median_genes=float(np.median([len(i.genome.genes) for i in population])),
            train_fitness=json.dumps(ranked[0][0].fitness),validation_fitness=json.dumps(archives['task']['rank']),
            task=archives['task']['individual']['id'],transmission=archives['transmission']['signal'],
            goal=archives['goal']['goal'],goal_signal=archives['goal']['signal'],
            goal_quality=archives['goal']['quality'],goal_specificity=archives['goal']['specificity'],
            goal_both=archives['goal']['both'],total_work=total_work,maze_evaluations=total_evaluations))
        if progress and (generation%10==0 or generation+1==config['generations']):
            print(f"{key} g{generation:03d} task={archives['task']['rank'][:3]} goal={archives['goal']['goal']:.4f} "
                  f"signal={archives['transmission']['signal']:.3f} both={archives['goal']['both']:.2f} niches={len(niches)}",flush=True)
        # Protect the fixed V3 signalling genome equally in both arms. V4
        # validation archives never re-enter reproduction automatically.
        population=[ranked[0][1]]
        elite=Individual.load(protected)
        if elite.identity!=population[0].identity:population.append(elite)
        for _,item in list(niches.values())[:config['population']//3]:
            if item.identity not in {i.identity for i in population}:population.append(item)
        for _ in range(max(1,config['population']//10)):population.append(create(random_genome(rng,True),None,generation+1))
        while len(population)<config['population']:
            parent=rng.choice(ranked)[1] if rng.random()<.1 else lexicase(rng,ranked)
            population.append(create(mutate(parent.genome,rng,rng.randint(1,6)),parent.identity,generation+1))
        if len(population)>config['population']:raise RuntimeError('Population ceiling exceeded')
        finished=generation+1==config['generations'] or (deadline is not None and time.perf_counter()>=deadline)
        saved=dict(config=immutable,serial=serial,next_generation=generation+1,rng_state=rng.getstate(),
            population=[i.save() for i in population],archives=archives,frozen=frozen,initial_digests=initial_digests,
            fork_injection=fork_injection,protected=protected,total_work=total_work,total_evaluations=total_evaluations)
        if generation%10==0 or finished:
            temporary=Path(str(checkpoint)+'.tmp');temporary.write_text(json.dumps(saved,separators=(',',':'))+'\n')
            temporary.replace(checkpoint)
        if finished:break
    return dict(config=config,archives=archives,frozen=frozen,initial_digests=initial_digests,
        fork_injection=fork_injection,protected=protected,next_generation=saved['next_generation'],work=total_work,maze_evaluations=total_evaluations)
