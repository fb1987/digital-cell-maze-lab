"""Deterministic search with diverse unfinished phenotypes and resumable state."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import random

import numpy as np

from .datasets import seed_for
from .evaluator import assess
from .regulatory import Genome, random_genome, seeded_genome, mutate
from .regulatory_runtime import Organism
from .runtime import Limits


@dataclass
class Individual:
    identity: str
    genome: Genome
    parent: str | None
    birth: int

    def save(self):
        return dict(id=self.identity, genome=self.genome.to_dict(), parent=self.parent, birth=self.birth)

    @classmethod
    def load(cls, value):
        return cls(value['id'], Genome.from_dict(value['genome']), value['parent'], value['birth'])


@dataclass
class Evaluation:
    fitness: tuple
    case_values: list
    descriptor: tuple
    rows: list
    work: int


def evaluate(individual, cases, topology, limits):
    organism = Organism(individual.genome, topology, limits)
    assessed, reactions, rows = [], [], []
    for oracle in cases:
        m = oracle.maze
        r = organism.react(m.cells, m.w, m.h, m.start, m.goal)
        a = assess(r, oracle)
        assessed.append(a)
        reactions.append(r)
        rows.append(dict(case=m.case_id, status=r.status, steps=r.steps, valid=a.valid_path,
                         optimal=a.optimal, no_path=a.no_path_correct, partial=a.partial,
                         failure=a.failure, reads=r.range_reads, dispatches=r.dispatches,
                         active=r.active_instructions,
                         mask=np.packbits(r.mask, bitorder='little').tobytes().hex()))
    work = sum(r.dispatches + r.spatial_reads for r in reactions)
    complete = all(a.valid_path or a.no_path_correct for a in assessed)
    # Invalid phenotypes carry no cost/length tie-break: don't select immediate
    # program shrinkage instead of allowing neutral complexity to accumulate.
    fitness = (sum(a.valid_path for a in assessed), sum(a.optimal for a in assessed),
               sum(a.no_path_correct for a in assessed)
               - sum(a.reachable and r.status == 'no_path' for a, r in zip(assessed, reactions)),
               round(sum(a.partial for a in assessed), 8), -work if complete else 0)
    case_values = [(int(a.valid_path or a.no_path_correct),
                    int(a.optimal or a.no_path_correct), a.partial) for a in assessed]
    length_bin = min(3, (len(individual.genome.genes)-1)//32)
    density = tuple(min(7, int(float(np.mean(r.mask))*8)) for r in reactions)
    progress = tuple(min(7, int(a.partial*8)) for a in assessed)
    expression = min(3, int(4 * sum(r.active_instructions for r in reactions)
                            / max(1, sum(r.dispatches for r in reactions))))
    lifetime = min(3, max(r.steps for r in reactions)//16)
    descriptor = (density, progress, length_bin, expression, lifetime,
                  int(any(sum(r.range_reads[1:]) for r in reactions)))
    return Evaluation(fitness, case_values, descriptor, rows, work)


def lexicase(rng, ranked, epsilon=.02):
    survivors = list(ranked)
    cases = list(range(len(survivors[0][0].case_values)))
    rng.shuffle(cases)
    for case in cases:
        for field in (0, 1, 2):
            best = max(ev.case_values[case][field] for ev, _ in survivors)
            tolerance = epsilon if field == 2 else 0
            survivors = [(ev, item) for ev, item in survivors
                         if ev.case_values[case][field] >= best - tolerance]
            if len(survivors) == 1:
                return survivors[0][1]
    return rng.choice(survivors)[1]


def tuple_tree(value):
    return tuple(tuple_tree(v) for v in value) if isinstance(value, list) else value


def search(config, batches, validation, registry, evaluations, history, checkpoint,
           resume=None, progress=True):
    """Resume uses a fresh result stream; prior ancestry remains in parent logs.

    `generations` is an absolute target. Checkpoint records the *next* population
    and RNG state, so extending that target reproduces uninterrupted evolution.
    """
    key = '/'.join(str(config[k]) for k in ('study', 'topology', 'origin', 'method', 'replicate'))
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

    def fresh(generation):
        population = []
        for i in range(config['population']):
            if config['origin'] == 'seeded':
                genome = seeded_genome() if i == 0 else mutate(seeded_genome(), rng, rng.randint(1, 6))
            else:
                genome = random_genome(rng, config['rich'])
            population.append(create(genome, None, generation))
        return population

    def log_evaluation(item, ev, generation, split):
        evaluations.write(json.dumps(dict(condition=key, generation=generation, split=split,
            id=item.identity, fitness=ev.fitness, descriptor=ev.descriptor,
            work=ev.work, cases=ev.rows), separators=(',', ':')) + '\n')

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
        initial_digests = saved['initial_digests']
        total_work, total_evaluations = saved['total_work'], saved['total_evaluations']
    else:
        population = fresh(0)
        initial_digests = [item.genome.digest for item in population]
        total_work, total_evaluations = 0, 0
        candidates = []
        for item in population:
            ev = evaluate(item, validation, config['topology'], validation_limits)
            log_evaluation(item, ev, -1, 'validation')
            total_work += ev.work
            total_evaluations += len(validation)
            candidates.append((ev.fitness, item))
        champion_fitness, champion = max(candidates, key=lambda pair: pair[0])
        frozen, frozen_fitness = champion, champion_fitness

    for generation in range(start_generation, config['generations']):
        batch = batches(generation)
        ranked = []
        for item in population:
            ev = evaluate(item, batch, config['topology'], train_limits)
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
        if config['rich'] and generation % 10 == 0:
            for _, item in list(niches.values())[:3]:
                if item.identity not in {i.identity for i in nominees}:
                    nominees.append(item)
        for item in nominees:
            ev = evaluate(item, validation, config['topology'], validation_limits)
            log_evaluation(item, ev, generation, 'validation')
            total_work += ev.work
            total_evaluations += len(validation)
            if ev.fitness > champion_fitness:
                champion, champion_fitness = item, ev.fitness
        history.append(dict(condition=key, generation=generation, niches=len(niches),
            unique=len({i.genome.digest for i in population}),
            median_genes=float(np.median([len(i.genome.genes) for i in population])),
            train_fitness=json.dumps(ranked[0][0].fitness),
            validation_fitness=json.dumps(champion_fitness), champion=champion.identity,
            champion_genes=len(champion.genome.genes), total_work=total_work,
            maze_evaluations=total_evaluations))
        if progress and (generation % 10 == 0 or generation + 1 == config['generations']):
            print(f'{key} g{generation:03} validation={champion_fitness[:4]} '
                  f'genes={len(champion.genome.genes)} niches={len(niches)}', flush=True)
        # Always prepare the next generation, even at the requested stopping
        # point. A resumed run consequently shares the uninterrupted RNG path.
        if config['method'] == 'resample':
            population = fresh(generation + 1)
        elif config['rich']:
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
        saved = dict(config=immutable, serial=serial, next_generation=generation+1,
            rng_state=rng.getstate(), population=[i.save() for i in population],
            champion=champion.save(), frozen=frozen.save(), champion_fitness=champion_fitness,
            frozen_fitness=frozen_fitness, initial_digests=initial_digests,
            total_work=total_work, total_evaluations=total_evaluations)
        if generation % 10 == 0 or generation + 1 == config['generations']:
            temporary = Path(str(checkpoint) + '.tmp')
            temporary.write_text(json.dumps(saved, separators=(',', ':')) + '\n')
            temporary.replace(checkpoint)
    return dict(config=config, champion=champion.save(), frozen=frozen.save(),
                fitness=champion_fitness, frozen_fitness=frozen_fitness,
                initial_digests=initial_digests, work=total_work, maze_evaluations=total_evaluations)
