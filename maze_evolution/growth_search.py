"""V11 strict-choice priority preserving both V10 arms and validated primitives."""
import copy
import hashlib
import json
from pathlib import Path
import random
import time
import numpy as np
from .growth import Genome,mutate,random_genome,Individual
from .regulatory_search import tuple_tree
from .runtime import Limits
from .growth_fitness import evaluate,lexicase


def record(item,ev,label):
    value={'task':ev.normal_fitness,'transmission':(ev.long_signal,ev.fitness[0],ev.fitness[1]),
           'goal':(ev.goal_score,ev.fitness[0],ev.fitness[1]),'quality':(ev.goal_quality,ev.fitness[0],ev.fitness[1]),
           'specificity':(ev.goal_specificity,ev.fitness[0],ev.fitness[1]),
           'choice':(ev.junction_both,ev.junction,ev.balanced_goal,ev.goal_score,ev.fitness[0],ev.fitness[1]),
           'junction':(ev.junction,ev.junction_both,ev.balanced_goal,ev.fitness[0],ev.fitness[1]),
           'balanced':(ev.balanced_goal,ev.pair_both,ev.goal_quality,ev.goal_score,ev.fitness[0],ev.fitness[1])}
    rank=value[label]
    return dict(individual=item.save(),rank=list(rank),signal=ev.long_signal,goal=ev.goal_score,
        quality=ev.goal_quality,specificity=ev.goal_specificity,both=ev.pair_both,
        strict_pairs=ev.strict_pairs,selection_credit=ev.selection_credit,choice_families=ev.choice_families,junction=ev.junction,junction_both=ev.junction_both,junction_families=ev.junction_families,balanced=ev.balanced_goal,balanced_families=ev.balanced_families,goal_families=ev.goal_families,valid=ev.fitness[0],optimal=ev.fitness[1])


def load_forks(paths,config,supplement,ancestry):
    if paths is None or len(paths)!=2 or len(config['fork_sha256'])!=2:
        raise ValueError('Two explicit V10 forks and hashes are required')
    result=[]
    for path,mode,sha in zip(paths,('fixed','curriculum'),config['fork_sha256']):
        raw=Path(path).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Fork hash differs')
        saved=json.loads(raw);ac=saved['config']
        if (ac.get('search_version')!=10 or ac.get('origin')!='random' or ac.get('pressure')!=mode
                or ac['topology']!=config['topology'] or ac.get('replicate')!=config['replicate']):
            raise ValueError('Expected matching random-origin V10 checkpoints')
        result.append(saved)
    if supplement is None or ancestry is None:raise ValueError('Explicit validation supplement and ancestry are required')
    extra=[]
    for path,key in ((supplement,'supplement_sha256'),(ancestry,'ancestry_sha256')):
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=config[key]:raise ValueError('Supplement/ancestry hash differs')
    records=json.loads(Path(supplement).read_text())['records']
    for mode in ('fixed','curriculum'):
        extra.append(records[f"distance/{config['topology']}/{mode}/{config['replicate']}"]['individual'])
    for record in json.loads(Path(ancestry).read_text())['records']:
        if record['condition'].split('/')[1]==config['topology'] and int(record['condition'].split('/')[3])==config['replicate']:
            extra.extend(n['individual'] for n in record['nodes'])
    return result,extra


def learned_parents(ancestors,extra):
    unique=[];digests=set()
    for ancestor in ancestors:
        items=[ancestor['archives'][label]['individual'] for label in ('task','choice','junction','balanced','goal','transmission')]
        for item in items+ancestor['protected']:
            digest=Genome.from_dict(item['genome']).digest
            if digest not in digests:unique.append(item);digests.add(digest)
    for item in extra:
        digest=Genome.from_dict(item['genome']).digest
        if digest not in digests:unique.append(item);digests.add(digest)
    return unique


def search(config,batches,validation,registry,evaluations,history,checkpoint,fork=None,
           resume=None,deadline=None,progress=True,supplement=None,ancestry=None):
    if not 4<=config['population']<=128 or not 1<=config['generations']<=1000:
        raise ValueError('Unbounded V11 search')
    if config['gene_limit'] not in (128,256) or config['pressure']!=f"cap{config['gene_limit']}":raise ValueError('Capacity/arm mismatch')
    immutable={k:v for k,v in config.items() if k!='generations'}
    key=f"growth/{config['topology']}/{config['pressure']}/{config['replicate']}"
    rng=random.Random(0); serial=0; start_generation=0; total_work=total_evaluations=0
    train_limits=Limits(**config['train_limits']); eval_limits=Limits(**config['eval_limits'])
    archives={};phase_leaders={}
    def create(genome,parent,birth,mutation=None):
        nonlocal serial
        item=Individual(f'{key}/i{serial}',genome,parent,birth); serial+=1
        registry.write(json.dumps({**item.save(),'mutation':mutation or []},separators=(',',':'))+'\n');return item
    def evaluate_log(item,pairs,generation,split,limits):
        nonlocal total_work,total_evaluations
        objective='choice'
        ev=evaluate(item,pairs,config['topology'],limits,objective,config['horizon'],config['gene_limit'])
        total_work+=ev.work;total_evaluations+=2*len(pairs)
        evaluations.write(json.dumps(dict(condition=key,id=item.identity,generation=generation,split=split,
            objective=objective,strict_pairs=ev.strict_pairs,selection_credit=ev.selection_credit,choice_families=ev.choice_families,junction=ev.junction,junction_both=ev.junction_both,junction_families=ev.junction_families,balanced=ev.balanced_goal,balanced_families=ev.balanced_families,fitness=ev.fitness,case_values=ev.case_values,normal_fitness=ev.normal_fitness,smooth_fitness=ev.smooth_fitness,alpha=ev.alpha,descriptor=ev.descriptor,work=ev.work,inference_work=ev.inference_work,
            probe_work=ev.probe_work,signal=ev.long_signal,goal=ev.goal_score,quality=ev.goal_quality,
            specificity=ev.goal_specificity,both=ev.pair_both,goal_families=ev.goal_families,
            cases=ev.rows),separators=(',',':'))+'\n')
        return ev
    def update(item,ev):
        for label in ('task','transmission','goal','balanced','junction','choice','quality','specificity'):
            candidate=record(item,ev,label)
            if label not in archives or tuple(candidate['rank'])>tuple(archives[label]['rank']):archives[label]=candidate
    if resume is not None:
        saved=json.loads(Path(resume).read_text())
        if saved['config']!=immutable:raise ValueError('Resume configuration differs')
        rng.setstate(tuple_tree(saved['rng_state']));serial=saved['serial'];start_generation=saved['next_generation']
        population=[Individual.load(x) for x in saved['population']]
        archives=saved['archives'];frozen=saved['frozen'];initial_digests=saved['initial_digests']
        fork_injection=saved['fork_injection'];protected=saved['protected']
        total_work=saved['total_work'];total_evaluations=saved['total_evaluations'];phase_leaders=saved['phase_leaders']
    else:
        ancestors,extra=load_forks(fork,config,supplement,ancestry)
        ancestor=ancestors[0]  # Prespecified Fixed-arm next population and RNG.
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
                     max(ranked,key=lambda x:x[0].balanced_goal)[1],max(ranked,key=lambda x:x[0].junction)[1],
                     max(ranked,key=lambda x:(x[0].junction_both,x[0].junction,x[0].balanced_goal,x[0].goal_score,*x[0].normal_fitness[:2]))[1]):
            if item.identity not in {i.identity for i in nominees}:nominees.append(item)
        if generation%10==0:
            for _,item in list(niches.values())[:3]:
                if item.identity not in {i.identity for i in nominees}:nominees.append(item)
        for item in nominees:update(item,evaluate_log(item,validation,generation,'validation',eval_limits))
        if generation in (15,31,47):
            ev,item=ranked[0]
            phase_leaders[str(generation)]=dict(individual=item.save(),fitness=list(ev.fitness),strict_pairs=ev.strict_pairs,
                junction=ev.junction,cases=[p.first.maze.case_id for p in pairs])
        history.append(dict(condition=key,generation=generation,niches=len(niches),
            unique=len({i.genome.digest for i in population}),max_genes=max(len(i.genome.genes) for i in population),above128=sum(len(i.genome.genes)>128 for i in population),median_genes=float(np.median([len(i.genome.genes) for i in population])),
            alpha=ranked[0][0].alpha,train_fitness=json.dumps(ranked[0][0].fitness),validation_fitness=json.dumps(archives['task']['rank']),
            task=archives['task']['individual']['id'],transmission=archives['transmission']['signal'],
            goal=archives['goal']['goal'],goal_signal=archives['goal']['signal'],
            goal_quality=archives['goal']['quality'],goal_specificity=archives['goal']['specificity'],
            goal_both=archives['goal']['both'],choice_both=archives['choice']['junction_both'],choice_score=archives['choice']['junction'],junction=archives['junction']['junction'],junction_both=archives['junction']['junction_both'],balanced=archives['balanced']['balanced'],balanced_both=archives['balanced']['both'],total_work=total_work,maze_evaluations=total_evaluations))
        if progress and (generation%10==0 or generation+1==config['generations']):
            print(f"{key} g{generation:03d} task={archives['task']['rank'][:3]} goal={archives['goal']['goal']:.4f} "
                  f"junction={archives['junction']['junction']:.4f} choices={archives['choice']['junction_both']:.2f} niches={len(niches)}",flush=True)
        # Fixed validation-selected V10 variants are shared across pressure arms.
        # New V11 validation archives never re-enter reproduction automatically.
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
            genome,events=mutate(parent.genome,rng,rng.randint(1,6),config['gene_limit'],True)
            population.append(create(genome,parent.identity,generation+1,events))
        if len(population)>config['population']:raise RuntimeError('Population ceiling exceeded')
        finished=generation+1==config['generations'] or (deadline is not None and time.perf_counter()>=deadline)
        saved=dict(config=immutable,phase_leaders=phase_leaders,serial=serial,next_generation=generation+1,rng_state=rng.getstate(),
            population=[i.save() for i in population],archives=archives,frozen=frozen,initial_digests=initial_digests,
            fork_injection=fork_injection,protected=protected,total_work=total_work,total_evaluations=total_evaluations)
        if generation%10==0 or finished:
            temporary=Path(str(checkpoint)+'.tmp');temporary.write_text(json.dumps(saved,separators=(',',':'))+'\n')
            temporary.replace(checkpoint)
        if finished:break
    return dict(config=config,phase_leaders=phase_leaders,archives=archives,frozen=frozen,initial_digests=initial_digests,
        fork_injection=fork_injection,protected=protected,next_generation=saved['next_generation'],work=total_work,maze_evaluations=total_evaluations)
