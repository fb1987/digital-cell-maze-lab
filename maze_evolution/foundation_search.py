"""V12 bounded search, also used by separate solver-repair calibration controls."""
import json
import random
from pathlib import Path

from .datasets import seed_for
from .growth import Individual, Genome, mutate, random_genome
from .runtime import Limits
from .regulatory_search import tuple_tree
from .foundation_fitness import evaluate, lexicase


class Search:
    def __init__(self, config, initial, registry, evaluations, checkpoint, resume=False, references=None):
        if config['method'] not in ('evolution', 'resample') or not 16 <= config['population'] <= 512:
            raise ValueError('Invalid bounded search configuration')
        self.config = config
        self.key = '/'.join(str(config[k]) for k in ('study', 'topology', 'origin', 'method', 'replicate'))
        self.registry, self.evaluations = registry, evaluations
        self.checkpoint = Path(checkpoint)
        self.rng = random.Random(seed_for(config['seed'], self.key, config['replicate'], 0))
        self.serial = self.next_generation = self.work = self.responses = 0
        self.history = []
        self.champion = self.frozen = None
        self.champion_rank = self.frozen_rank = None
        self.champion_rows = self.frozen_rows = None
        self.validation_events = 0
        self.initial_digests = []
        if resume:
            state = json.loads(self.checkpoint.read_text())
            if state['config'] != config:
                raise ValueError('Checkpoint configuration differs')
            self.rng.setstate(tuple_tree(state['rng_state']))
            for key in ('serial', 'next_generation', 'work', 'responses', 'history', 'initial_digests',
                        'validation_events', 'champion_rows', 'frozen_rows'):
                setattr(self, key, state[key])
            for key in ('champion', 'frozen'):
                setattr(self, key, Individual.load(state[key]) if state[key] else None)
            for key in ('champion_rank', 'frozen_rank'):
                setattr(self, key, tuple(state[key]) if state[key] is not None else None)
            self.population = [Individual.load(i) for i in state['population']]
        else:
            if len(initial) != config['population']:
                raise ValueError('Incorrect founder population')
            refs = references or [None] * len(initial)
            self.population = [self.create(g, None, 0, founder=ref) for g, ref in zip(initial, refs)]
            self.initial_digests = [i.genome.digest for i in self.population]

    def create(self, genome, parent, birth, events=None, founder=None):
        item = Individual(f'{self.key}/i{self.serial}', genome, parent, birth)
        self.serial += 1
        self.registry.write(json.dumps(dict(**item.save(), events=events, founder=founder), separators=(',', ':')) + '\n')
        return item

    def evaluate(self, item, pairs, split, generation):
        ev = evaluate(item, pairs, self.config['topology'], Limits(**self.config['limits']), self.config['goal_pulse'])
        self.work += ev.work
        self.responses += len(ev.rows)
        self.evaluations.write(json.dumps(dict(condition=self.key, id=item.identity, split=split,
            generation=generation, fitness=ev.fitness, descriptor=ev.descriptor, work=ev.work,
            cases=ev.rows), separators=(',', ':')) + '\n')
        return ev

    def initialize(self, validation):
        if self.champion is not None:
            return
        for item in self.population:
            ev = self.evaluate(item, validation, 'validation_initial', -1)
            if self.champion_rank is None or ev.fitness > self.champion_rank:
                self.champion, self.champion_rank, self.champion_rows = item, ev.fitness, ev.rows
        self.frozen, self.frozen_rank, self.frozen_rows = self.champion, self.champion_rank, self.champion_rows
        self.save()

    def step(self, batch, validation, level=0):
        generation = self.next_generation
        ranked = [(self.evaluate(item, batch, 'train', generation), item) for item in self.population]
        ranked.sort(key=lambda pair: pair[0].fitness, reverse=True)
        if generation % self.config['validation_every'] == 0:
            seen = set()
            nominees = []
            for ev, item in ranked:
                if item.genome.digest not in seen:
                    seen.add(item.genome.digest)
                    nominees.append(item)
                if len(nominees) == self.config['validation_nominees']:
                    break
            # Keep validation response budgets equal even in homogeneous populations.
            for _, item in ranked:
                if len(nominees) == self.config['validation_nominees']:
                    break
                if item.identity not in {n.identity for n in nominees}:
                    nominees.append(item)
            for item in nominees:
                ev = self.evaluate(item, validation, 'validation', generation)
                if ev.fitness > self.champion_rank:
                    self.champion, self.champion_rank, self.champion_rows = item, ev.fitness, ev.rows
            self.validation_events += 1
        elite_count = max(1, self.config['population'] // 8)
        selected = [ranked[0][1]]
        identities = {selected[0].identity}
        descriptors = {ranked[0][0].descriptor}
        for ev, item in ranked:
            if ev.descriptor not in descriptors and len(selected) < elite_count:
                selected.append(item)
                descriptors.add(ev.descriptor)
                identities.add(item.identity)
        for _, item in ranked:
            if len(selected) == elite_count:
                break
            if item.identity not in identities:
                selected.append(item)
                identities.add(item.identity)
        immigrants = self.config['immigrants']
        if not 0 <= immigrants <= self.config['population'] // 4:
            raise ValueError('Unbounded immigration')
        mutations = resamples = 0
        for _ in range(self.config['population'] - elite_count):
            if self.config['method'] == 'resample' or resamples < immigrants:
                item = self.create(random_genome(self.rng, True), None, generation + 1)
                resamples += 1
            else:
                parent = self.rng.choice(ranked)[1] if self.rng.random() < .1 else lexicase(self.rng, ranked)
                genome, events = mutate(parent.genome, self.rng, self.rng.randint(1, 6), 256, True)
                item = self.create(genome, parent.identity, generation + 1, events)
                mutations += 1
            selected.append(item)
        self.history.append(dict(generation=generation, level=level, train_fitness=ranked[0][0].fitness,
            champion_rank=self.champion_rank, champion=self.champion.identity, work=self.work,
            responses=self.responses, mutations=mutations, resamples=resamples,
            unique=len({item.genome.digest for _, item in ranked}),
            max_genes=max(len(item.genome.genes) for _, item in ranked)))
        self.population = selected
        self.next_generation += 1
        self.save()
        return self.history[-1]

    def state(self):
        return dict(config=self.config, serial=self.serial, next_generation=self.next_generation,
            rng_state=self.rng.getstate(), work=self.work, responses=self.responses,
            history=self.history, initial_digests=self.initial_digests, validation_events=self.validation_events,
            population=[i.save() for i in self.population], champion=self.champion.save() if self.champion else None,
            frozen=self.frozen.save() if self.frozen else None, champion_rank=self.champion_rank,
            frozen_rank=self.frozen_rank, champion_rows=self.champion_rows, frozen_rows=self.frozen_rows)

    def save(self):
        self.registry.flush()
        self.evaluations.flush()
        temporary = self.checkpoint.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.state(), separators=(',', ':')) + '\n')
        temporary.replace(self.checkpoint)
