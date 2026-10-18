"""V12B mutation-locality comparison; the wide arm uses V12A unchanged."""
from .foundation_search import Search
from .foundation_fitness import lexicase
from .growth import mutate, random_genome


class MutationSearch(Search):
    def step(self, batch, validation, level=0):
        policy = self.config['mutation_policy']
        if policy == 'wide':
            return super().step(batch, validation, level)
        if policy != 'single':
            raise ValueError('Unknown mutation locality')
        # Same selection, nomination, retention and random-parent convention as
        # V12A. The sole mutation change is one requested edit per offspring.
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
                genome, events = mutate(parent.genome, self.rng, 1, 256, True)
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
