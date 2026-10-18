"""V3 fork of the V2 search, changing only auxiliary selection pressure.

V2 files stay immutable. Both arms share observers, archive attention, mutations,
lexicase and behavioural niches. Stored scores are reset at the objective fork.
"""
import json
from pathlib import Path
import random
import time
import numpy as np
from .datasets import seed_for
from .regulatory import Genome, random_genome, mutate
from .regulatory_search import Individual, lexicase, tuple_tree
from .runtime import Limits
from .signal_fitness import evaluate

def search(config, batches, validation, registry, evaluations, history, checkpoint,
           fork=None, resume=None, progress=True, deadline=None):
    """Resume uses a fresh result stream; prior ancestry remains in parent logs.

    `generations` is an absolute target. Checkpoint records the *next* population
    and RNG state, so extending that target reproduces uninterrupted evolution.
    """
    key = '/'.join(str(config[k]) for k in ('study', 'topology', 'pressure', 'replicate'))
    immutable = {k: v for k, v in config.items() if k != 'generations'}
    rng = random.Random(seed_for(config['seed'], config['study'] + '/' + config['origin'], config['replicate'], 0))
    serial, start_generation = 0, 0
    train_limits, validation_limits = Limits(**config['train_limits']), Limits(**config['eval_limits'])

    def create(genome, parent, generation):
        nonlocal serial
        identity = f'{key}/i{serial}'
        serial += 1
        item = Individual(identity, genome, parent, generation)
        registry.write(json.dumps(item.save(), separators=(',', ':')) + '\n')
        return item

    def log_evaluation(item, ev, generation, split):
        evaluations.write(json.dumps(dict(condition=key, generation=generation, split=split,
            id=item.identity, fitness=ev.fitness, descriptor=ev.descriptor,
            work=ev.work, inference_work=ev.inference_work, probe_work=ev.probe_work, signal=ev.signal, long_signal=ev.long_signal, family_signals=ev.family_signals, cases=ev.rows), separators=(',', ':')) + '\n')

    if resume is not None:
        saved = json.loads(Path(resume).read_text())
        if saved['config'] != immutable:
            raise ValueError('Resume configuration differs from checkpoint')
        rng.setstate(tuple_tree(saved['rng_state']))
        serial, start_generation = saved['serial'], saved['next_generation']
        population = [Individual.load(v) for v in saved['population']]
        champion, frozen = Individual.load(saved['champion']), Individual.load(saved['frozen'])
        champion_fitness = tuple(saved['champion_fitness'])
        frozen_fitness = tuple(saved['frozen_fitness'])
        transmission = Individual.load(saved['transmission'])
        frozen_transmission = Individual.load(saved['frozen_transmission'])
        transmission_fitness = tuple(saved['transmission_fitness'])
        frozen_transmission_fitness = tuple(saved['frozen_transmission_fitness'])
        transmission_families = saved['transmission_families']
        initial_digests = saved['initial_digests']
        total_work, total_evaluations = saved['total_work'], saved['total_evaluations']
    else:
        if fork is None:
            raise ValueError('V3 must explicitly fork a random-origin V2 checkpoint')
        ancestor = json.loads(Path(fork).read_text())
        ac = ancestor['config']
        if ac['origin'] != 'random' or ac['method'] != 'evolution' or not ac['rich'] or ac['topology'] != config['topology']:
            raise ValueError('Expected a rich random-origin ancestor with matching topology')
        if len(ancestor['population']) != config['population']:
            raise ValueError('Fork population size differs')
        rng.setstate(tuple_tree(ancestor['rng_state']))
        population = [create(Genome.from_dict(v['genome']), v['id'], 0) for v in ancestor['population']]
        initial_digests = [item.genome.digest for item in population]
        total_work, total_evaluations = 0, 0
        candidates = []
        transmission_fitness = (-1., -1, -1)
        transmission = population[0]
        transmission_families = {}
        for item in population:
            ev = evaluate(item, validation, config['topology'], validation_limits, config['pressure'], config['horizon'])
            log_evaluation(item, ev, -1, 'validation')
            total_work += ev.work
            total_evaluations += len(validation)
            candidates.append((ev.fitness, item))
            tf = (ev.long_signal, ev.fitness[0], ev.fitness[1])
            if tf > transmission_fitness:
                transmission, transmission_fitness = item, tf
                transmission_families = ev.family_signals
        champion_fitness, champion = max(candidates, key=lambda pair: pair[0])
        frozen, frozen_fitness = champion, champion_fitness
        frozen_transmission = transmission
        frozen_transmission_fitness = transmission_fitness

    for generation in range(start_generation, config['generations']):
        batch = batches(generation)
        ranked = []
        for item in population:
            ev = evaluate(item, batch, config['topology'], train_limits, config['pressure'], config['horizon'])
            log_evaluation(item, ev, generation, 'train')
            total_work += ev.work
            total_evaluations += len(batch)
            ranked.append((ev, item))
        # Randomized ties preserve neutral variation; deterministic given RNG.
        rng.shuffle(ranked)
        ranked.sort(key=lambda pair: pair[0].fitness, reverse=True)
        niches = {}
        for ev, item in ranked:
            niches.setdefault(ev.descriptor, (ev, item))
        nominees = [ranked[0][1]]
        signal_nominee = max(ranked, key=lambda pair: pair[0].long_signal)[1]
        if signal_nominee.identity != nominees[0].identity:
            nominees.append(signal_nominee)
        if config['rich'] and generation % 10 == 0:
            for _, item in list(niches.values())[:3]:
                if item.identity not in {i.identity for i in nominees}:
                    nominees.append(item)
        for item in nominees:
            ev = evaluate(item, validation, config['topology'], validation_limits, config['pressure'], config['horizon'])
            log_evaluation(item, ev, generation, 'validation')
            total_work += ev.work
            total_evaluations += len(validation)
            tf = (ev.long_signal, ev.fitness[0], ev.fitness[1])
            if tf > transmission_fitness:
                transmission, transmission_fitness = item, tf
                transmission_families = ev.family_signals
            if ev.fitness > champion_fitness:
                champion, champion_fitness = item, ev.fitness
        history.append(dict(condition=key, generation=generation, niches=len(niches),
            unique=len({i.genome.digest for i in population}),
            median_genes=float(np.median([len(i.genome.genes) for i in population])),
            train_fitness=json.dumps(ranked[0][0].fitness),
            validation_fitness=json.dumps(champion_fitness), champion=champion.identity,
            champion_genes=len(champion.genome.genes), total_work=total_work,
            maze_evaluations=total_evaluations, transmission_signal=transmission_fitness[0],
            frozen_transmission_signal=frozen_transmission_fitness[0],
            transmission=transmission.identity))
        if progress and (generation % 10 == 0 or generation + 1 == config['generations']):
            print(f'{key} g{generation:03} validation={champion_fitness[:4]} '
                  f'genes={len(champion.genome.genes)} signal={transmission_fitness[0]:.3f} niches={len(niches)}', flush=True)
        # Always prepare the next generation, even at the requested stopping
        # point. A resumed run consequently shares the uninterrupted RNG path.
        if config['rich']:
            population = [ranked[0][1]]
            for _, item in list(niches.values())[:config['population']//3]:
                if item.identity not in {i.identity for i in population}:
                    population.append(item)
            for _ in range(max(1, config['population']//10)):
                population.append(create(random_genome(rng, True), None, generation + 1))
            while len(population) < config['population']:
                parent = rng.choice(ranked)[1] if rng.random() < .1 else lexicase(rng, ranked)
                population.append(create(mutate(parent.genome, rng, rng.randint(1, 6)), parent.identity, generation + 1))
        else:
            population = [i for _, i in ranked[:max(1, config['population']//8)]]
            pool = ranked[:max(2, len(ranked)//2)]
            while len(population) < config['population']:
                parent = max(rng.choices(pool, k=3), key=lambda pair: pair[0].fitness)[1]
                population.append(create(mutate(parent.genome, rng, rng.randint(1, 6)), parent.identity, generation + 1))
        finished = generation+1 == config['generations'] or (deadline is not None and time.perf_counter() >= deadline)
        saved = dict(config=immutable, serial=serial, next_generation=generation+1,
            rng_state=rng.getstate(), population=[i.save() for i in population],
            champion=champion.save(), frozen=frozen.save(), champion_fitness=champion_fitness,
            frozen_fitness=frozen_fitness, initial_digests=initial_digests,
            total_work=total_work, total_evaluations=total_evaluations,
            transmission=transmission.save(), transmission_fitness=transmission_fitness,
            frozen_transmission=frozen_transmission.save(), frozen_transmission_fitness=frozen_transmission_fitness,
            transmission_families=transmission_families)
        if generation % 10 == 0 or finished:
            temporary = Path(str(checkpoint) + '.tmp')
            temporary.write_text(json.dumps(saved, separators=(',', ':')) + '\n')
            temporary.replace(checkpoint)
        if finished:
            break
    return dict(config=config, champion=champion.save(), frozen=frozen.save(),
                fitness=champion_fitness, frozen_fitness=frozen_fitness,
                initial_digests=initial_digests, work=total_work, maze_evaluations=total_evaluations,
                next_generation=saved['next_generation'], transmission=transmission.save(),
                transmission_fitness=transmission_fitness, transmission_families=transmission_families,
                frozen_transmission=frozen_transmission.save(), frozen_transmission_fitness=frozen_transmission_fitness)
