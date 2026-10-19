"""Replay V12E reproduction from logged grades and saved initial RNG, without inference."""
from collections import Counter, defaultdict
import hashlib
import json
import random

from .growth import Genome, Individual, mutate, random_genome
from .regulatory_search import Evaluation, tuple_tree


def state_items(state):
    return [state['champion'], state['frozen'], *state.get('population', [])] + [
        v['item'] for source in ('skills', 'frozen_skills', 'common_archives') for v in state[source].values()]


def unique_items(states):
    result = {}
    for state in states.values():
        for item in state_items(state):
            assert result.setdefault(item['id'], item) == item, item['id']
    return result


def ranked_fitness(raw, policy):
    return tuple(raw) if policy == 'current' else (raw[3], raw[0], raw[1], raw[2], raw[4], raw[5])


def hash_json(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()


def choose_parent(rng, ranked):
    if rng.random() < .1:
        return rng.choice(ranked)[1], 'random'
    survivors = list(ranked)
    order = list(range(len(survivors[0][0].case_values)))
    rng.shuffle(order)
    for case in order:
        for field in range(4):
            maximum = max(ev.case_values[case][field] for ev, _ in survivors)
            tolerance = .02 if field == 3 else 0.
            survivors = [(ev, item) for ev, item in survivors
                         if ev.case_values[case][field] >= maximum - tolerance]
            if len(survivors) == 1:
                return survivors[0][1], 'lexicase'
    return rng.choice(survivors)[1], 'lexicase'


def elites(ranked):
    selected = [ranked[0][1]]
    identities = {selected[0].identity}
    descriptors = {ranked[0][0].descriptor}
    for ev, item in ranked:
        if ev.descriptor not in descriptors and len(selected) < 12:
            selected.append(item)
            descriptors.add(ev.descriptor)
            identities.add(item.identity)
    for _, item in ranked:
        if len(selected) == 12:
            break
        if item.identity not in identities:
            selected.append(item)
            identities.add(item.identity)
    assert len(selected) == 12
    return selected


class ReproductionAudit:
    def __init__(self, parents, states, lineage):
        self.parents, self.states, self.lineage = parents, states, iter(lineage)
        self.populations = {key: [Individual.load(i) for i in s['population']] for key, s in parents.items()}
        self.digests = {key: {i.identity: i.genome.digest for i in pop} for key, pop in self.populations.items()}
        self.rngs = {key: random.Random() for key in parents}
        for key, rng in self.rngs.items():
            rng.setstate(tuple_tree(parents[key]['rng_state']))
        self.serials = {key: s['serial'] for key, s in parents.items()}
        original = unique_items(parents)
        self.expected = unique_items(states)
        for identity in set(original) & set(self.expected):
            assert original[identity] == self.expected[identity]
        self.expected.update(original)
        self.checked = set(original)
        self.stats = defaultdict(Counter)
        self.samples = []

    def step(self, key, generation, train, validation, history):
        cfg = self.states[key]['config']
        policy = cfg['selection_policy']
        alternative = 'paired' if policy == 'current' else 'current'
        population = self.populations[key]
        assert [r['id'] for r in train] == [i.identity for i in population]
        digests = self.digests[key]

        def ranked(name):
            entries = []
            for record, item in zip(train, population):
                values = [(int(r['valid'] or r['no_path']), int(r['optimal'] or r['no_path']),
                           int(r['pair_optimal']), r['partial'] + r['paired_partial']) for r in record['cases']]
                if name == 'paired':
                    values = [(p, v, o, s) for v, o, p, s in values]
                ev = Evaluation(ranked_fitness(record['raw_fitness'], name), values,
                                tuple_tree(record['descriptor']), record['cases'], record['work'])
                entries.append((ev, item))
            return sorted(entries, key=lambda v: v[0].fitness, reverse=True)

        ordered, counterfactual = ranked(policy), ranked(alternative)
        assert tuple(history['train_fitness']) == ordered[0][0].fitness
        assert history['unique'] == len(set(digests.values()))
        assert history['max_genes'] == max(len(i.genome.genes) for i in population)
        assert history['maximum_train_complete_pairs'] == max(r['raw_fitness'][3] for r in train)
        top = {digests[i.identity] for ev, i in ordered if ev.fitness == ordered[0][0].fitness}
        alt_top = {digests[i.identity] for ev, i in counterfactual if ev.fitness == counterfactual[0][0].fitness}
        assert history['ordering_top_genotypes_differ'] == (top != alt_top)
        stats = self.stats[key]
        stats['generations'] += 1
        stats['global_top_genotype_sets_differ'] += top != alt_top
        if generation % 8 == 0:
            seen, nominees = set(), []
            for _, item in ordered:
                if digests[item.identity] not in seen:
                    seen.add(digests[item.identity])
                    nominees.append(item.identity)
                if len(nominees) == 4:
                    break
            for _, item in ordered:
                if len(nominees) == 4:
                    break
                if item.identity not in nominees:
                    nominees.append(item.identity)
            assert [r['id'] for r in validation] == nominees
        else:
            assert not validation
        selected, alt_selected = elites(ordered), elites(counterfactual)
        stats['retained_genotype_sets_differ'] += ({digests[i.identity] for i in selected}
                                                 != {digests[i.identity] for i in alt_selected})
        rng = self.rngs[key]
        mutations = immigrants = 0
        for _ in range(84):
            if cfg['method'] == 'resample' or immigrants < 9:
                genome = random_genome(rng, True)
                parent_id, events = None, None
                immigrants += 1
            else:
                alternate_rng = random.Random()
                alternate_rng.setstate(rng.getstate())
                parent, mechanism = choose_parent(rng, ordered)
                alternative_parent, alternative_mechanism = choose_parent(alternate_rng, counterfactual)
                assert mechanism == alternative_mechanism
                stats['parent_draws'] += 1
                stats[mechanism + '_parent_draws'] += 1
                ids_differ = parent.identity != alternative_parent.identity
                dna_differ = digests[parent.identity] != digests[alternative_parent.identity]
                stats['counterfactual_parent_ids_differ'] += ids_differ
                stats['counterfactual_parent_genotypes_differ'] += dna_differ
                if dna_differ and len(self.samples) < 512:
                    self.samples.append(dict(condition=key, generation=generation, mechanism=mechanism,
                        selected_parent=parent.identity, alternative_parent=alternative_parent.identity))
                genome, events = mutate(parent.genome, rng, 1, 256, True)
                parent_id = parent.identity
                mutations += 1
            record = next(self.lineage)
            identity = f'{key}/i{self.serials[key]}'
            expected = Individual(identity, genome, parent_id, generation + 1)
            actual = Individual.load(record)
            assert actual == expected, identity
            assert record['events'] == events and record['founder'] is None
            if identity in self.expected:
                assert actual.save() == self.expected[identity]
                self.checked.add(identity)
            self.serials[key] += 1
            selected.append(expected)
        assert history['mutations'] == mutations == (75 if cfg['method'] == 'evolution' else 0)
        assert history['resamples'] == immigrants == (9 if cfg['method'] == 'evolution' else 84)
        stats['mutations'] += mutations
        stats['immigrants'] += immigrants
        stats['registered'] += 84
        self.populations[key] = selected
        self.digests[key] = {i.identity: digests.get(i.identity) or i.genome.digest for i in selected}
        assert history['population_sha256'] == hash_json([self.digests[key][i.identity] for i in selected])
        assert history['rng_sha256'] == hash_json(rng.getstate())

    def finish(self):
        assert next(self.lineage, None) is None
        assert self.checked == set(self.expected)
        for key, state in self.states.items():
            assert state['serial'] == self.serials[key]
            assert [i.save() for i in self.populations[key]] == state['population']
            assert tuple_tree(state['rng_state']) == self.rngs[key].getstate()
        return dict(registered=sum(s['registered'] for s in self.stats.values()),
            mutations=sum(s['mutations'] for s in self.stats.values()),
            immigrants=sum(s['immigrants'] for s in self.stats.values()),
            description='Every child, mutation event, random immigrant, parent selection, retained population and RNG hash replayed from the verified starting state; no candidate inference.',
            conditions={key: dict(stats) for key, stats in self.stats.items()},
            parent_counterfactual='Same current population and identical RNG state immediately before each actual parent draw, alternate global/case priority; descriptive, not a second evolved trajectory.',
            differing_parent_examples=self.samples), {k: Genome.from_dict(v['genome']) for k, v in self.expected.items()}
