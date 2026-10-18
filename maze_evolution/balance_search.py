"""V7 mean/weaker-goal continuation preserving both V6 arms and balanced variants."""
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
from .balance_fitness import evaluate


def record(item,ev,label):
    value={'task':ev.normal_fitness,'transmission':(ev.long_signal,ev.fitness[0],ev.fitness[1]),
           'goal':(ev.goal_score,ev.fitness[0],ev.fitness[1]),'quality':(ev.goal_quality,ev.fitness[0],ev.fitness[1]),
           'specificity':(ev.goal_specificity,ev.fitness[0],ev.fitness[1]),
           'balanced':(ev.balanced_goal,ev.pair_both,ev.goal_quality,ev.goal_score,ev.fitness[0],ev.fitness[1])}
    rank=value[label]
    return dict(individual=item.save(),rank=list(rank),signal=ev.long_signal,goal=ev.goal_score,
        quality=ev.goal_quality,specificity=ev.goal_specificity,both=ev.pair_both,
        balanced=ev.balanced_goal,balanced_families=ev.balanced_families,goal_families=ev.goal_families,valid=ev.fitness[0],optimal=ev.fitness[1])


def load_forks(paths,config,supplement):
    if paths is None or len(paths)!=2 or len(config['fork_sha256'])!=2:
        raise ValueError('Two explicit V6 forks and hashes are required')
    result=[]
    for path,mode,sha in zip(paths,('pulse','flag'),config['fork_sha256']):
        raw=Path(path).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Fork hash differs')
        saved=json.loads(raw);ac=saved['config']
        if (ac.get('search_version')!=6 or ac.get('origin')!='random' or ac.get('pressure')!=mode
                or ac['topology']!=config['topology'] or ac.get('replicate')!=config['replicate']):
            raise ValueError('Expected matching random-origin V6 pulse/flag checkpoints')
        result.append(saved)
    if supplement is None:raise ValueError('Explicit V6 balanced validation archive is required')
    raw=Path(supplement).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=config['supplement_sha256']:raise ValueError('Supplement hash differs')
    records=json.loads(raw)['records']
    extra=[records[f"beacon/{config['topology']}/{mode}/{config['replicate']}"]['individual'] for mode in ('pulse','flag')]
    return result,extra


def learned_parents(ancestors,extra):
    """Choose by validation archive field, never by final-test performance."""
    unique=[];digests=set()
    for ancestor,balanced in zip(ancestors,extra):
        items=[ancestor['archives'][label]['individual'] for label in ('task','goal','transmission')]
        items+=ancestor['protected']+[balanced]
        for item in items:
            digest=Genome.from_dict(item['genome']).digest
            if digest not in digests:unique.append(item);digests.add(digest)
    return unique


def search(config,batches,validation,registry,evaluations,history,checkpoint,fork=None,
           resume=None,deadline=None,progress=True,supplement=None):
    if not 4<=config['population']<=128 or not 1<=config['generations']<=1000:
        raise ValueError('Unbounded V7 search')
    immutable={k:v for k,v in config.items() if k!='generations'}
    key=f"balance/{config['topology']}/{config['pressure']}/{config['replicate']}"
    rng=random.Random(0); serial=0; start_generation=0; total_work=total_evaluations=0
    train_limits=Limits(**config['train_limits']); eval_limits=Limits(**config['eval_limits'])
    archives={}
    def create(genome,parent,birth):
        nonlocal serial
        item=Individual(f'{key}/i{serial}',genome,parent,birth); serial+=1
        registry.write(json.dumps(item.save(),separators=(',',':'))+'\n');return item
    def evaluate_log(item,pairs,generation,split,limits):
        nonlocal total_work,total_evaluations
        objective=config['pressure'] if split=='train' else 'mean'
        ev=evaluate(item,pairs,config['topology'],limits,objective,config['horizon'])
        total_work+=ev.work;total_evaluations+=2*len(pairs)
        evaluations.write(json.dumps(dict(condition=key,id=item.identity,generation=generation,split=split,
            objective=objective,balanced=ev.balanced_goal,balanced_families=ev.balanced_families,fitness=ev.fitness,normal_fitness=ev.normal_fitness,alpha=ev.alpha,descriptor=ev.descriptor,work=ev.work,inference_work=ev.inference_work,
            probe_work=ev.probe_work,signal=ev.long_signal,goal=ev.goal_score,quality=ev.goal_quality,
            specificity=ev.goal_specificity,both=ev.pair_both,goal_families=ev.goal_families,
            cases=ev.rows),separators=(',',':'))+'\n')
        return ev
    def update(item,ev):
        for label in ('task','transmission','goal','balanced','quality','specificity'):
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
        ancestors,extra=load_forks(fork,config,supplement)
        ancestor=ancestors[0]  # Prespecified pulse-arm next population and RNG.
        parents=list(ancestor['population'])
        if len(parents)!=config['population']:raise ValueError('Fork population size differs')
        unique=learned_parents(ancestors,extra)
        if len(unique)>config['population']-max(1,config['population']//10)-1:raise ValueError('Insufficient room for protected variants')
        protected_digests={Genome.from_dict(i['genome']).digest for i in unique}
        fork_injection=[]
        for item in unique:
            digest=Genome.from_dict(item['genome']).digest
            if digest not in {Genome.from_dict(i['genome']).digest for i in parents}:
                slot=next(j for j in range(len(parents)-1,-1,-1) if Genome.from_dict(parents[j]['genome']).digest not in protected_digests)
                fork_injection.append(dict(learned_parent=item['id'],replaced_parent=parents[slot]['id'],slot=slot))
                parents[slot]=item
        rng.setstate(tuple_tree(ancestor['rng_state']))
        population=[create(Genome.from_dict(p['genome']),p['id'],0) for p in parents]
        initial_digests=[i.genome.digest for i in population]
        protected=[next(i.save() for i in population if i.genome.digest==Genome.from_dict(p['genome']).digest) for p in unique]
        for item in population:update(item,evaluate_log(item,validation,-1,'validation',eval_limits))
        frozen=copy.deepcopy(archives)
    for generation in range(start_generation,config['generations']):
        pairs=batches(generation)
        ranked=[(evaluate_log(i,pairs,generation,'train',train_limits),i) for i in population]
        rng.shuffle(ranked);ranked.sort(key=lambda x:x[0].fitness,reverse=True)
        niches={}
        for ev,item in ranked:niches.setdefault(ev.descriptor,(ev,item))
        nominees=[]
        for item in (ranked[0][1],max(ranked,key=lambda x:x[0].long_signal)[1],max(ranked,key=lambda x:x[0].goal_score)[1],
                     max(ranked,key=lambda x:x[0].goal_quality)[1],max(ranked,key=lambda x:x[0].goal_specificity)[1],
                     max(ranked,key=lambda x:x[0].balanced_goal)[1]):
            if item.identity not in {i.identity for i in nominees}:nominees.append(item)
        if generation%10==0:
            for _,item in list(niches.values())[:3]:
                if item.identity not in {i.identity for i in nominees}:nominees.append(item)
        for item in nominees:update(item,evaluate_log(item,validation,generation,'validation',eval_limits))
        history.append(dict(condition=key,generation=generation,niches=len(niches),
            unique=len({i.genome.digest for i in population}),median_genes=float(np.median([len(i.genome.genes) for i in population])),
            alpha=ranked[0][0].alpha,train_fitness=json.dumps(ranked[0][0].fitness),validation_fitness=json.dumps(archives['task']['rank']),
            task=archives['task']['individual']['id'],transmission=archives['transmission']['signal'],
            goal=archives['goal']['goal'],goal_signal=archives['goal']['signal'],
            goal_quality=archives['goal']['quality'],goal_specificity=archives['goal']['specificity'],
            goal_both=archives['goal']['both'],balanced=archives['balanced']['balanced'],balanced_both=archives['balanced']['both'],total_work=total_work,maze_evaluations=total_evaluations))
        if progress and (generation%10==0 or generation+1==config['generations']):
            print(f"{key} g{generation:03d} task={archives['task']['rank'][:3]} goal={archives['goal']['goal']:.4f} "
                  f"balanced={archives['balanced']['balanced']:.4f} both={archives['balanced']['both']:.2f} niches={len(niches)}",flush=True)
        # Fixed validation-selected V6 variants are shared across pressure arms.
        # New V7 validation archives never re-enter reproduction automatically.
        population=[ranked[0][1]]
        for saved_elite in protected:
            elite=Individual.load(saved_elite)
            if elite.identity not in {i.identity for i in population}:population.append(elite)
        immigrants=max(1,config['population']//10)
        for _,item in list(niches.values())[:config['population']//3]:
            if len(population)<config['population']-immigrants and item.identity not in {i.identity for i in population}:population.append(item)
        for _ in range(immigrants):population.append(create(random_genome(rng,True),None,generation+1))
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
