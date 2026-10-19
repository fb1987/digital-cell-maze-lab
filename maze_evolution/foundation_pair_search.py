"""V12E: change completed-pair priority while retaining common validation archives."""
from copy import deepcopy
import hashlib
import json

from .foundation_fitness import evaluate
from .foundation_study_search import SkillSearch, skill_rank, certified_levels
from .runtime import Limits


def canonical(value):
    return json.loads(json.dumps(value))


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()


def priority(rank, policy):
    if policy == 'current':
        return tuple(rank)
    if policy == 'paired':
        v, o, n, p, s, w = rank
        return p, v, o, n, s, w
    raise ValueError('Unknown completed-pair priority')


def raw_rank(rows):
    complete = all(r['valid'] or r['no_path'] for r in rows)
    return (sum(r['valid'] for r in rows), sum(r['optimal'] for r in rows),
        sum(r['no_path'] for r in rows) - sum(r['reachable'] and r['status'] == 'no_path' for r in rows),
        sum(r['pair_optimal'] for r in rows) // 2,
        round(sum(r['partial'] + r['paired_partial'] for r in rows), 8),
        -sum(r['reads'] + r['dispatches'] for r in rows) if complete else 0)


def fork_state(parent, policy):
    """New ID namespace; exact population order, DNA, identities and RNG inherited."""
    state = deepcopy(parent)
    assert state['config']['origin'] == 'fresh'
    assert policy == 'current' or state['config']['method'] == 'evolution'
    state['config'].update(study='foundation_pair_' + policy, selection_policy=policy,
                           parent_condition='/'.join(str(parent['config'][k]) for k in
                               ('study', 'topology', 'origin', 'method', 'replicate')))
    for name in ('champion', 'frozen'):
        state[name + '_rank'] = list(priority(raw_rank(state[name + '_rows']), policy))
    state['common_archives'] = {
        name: dict(item=deepcopy(parent['champion']),
                   rank=list(priority(raw_rank(parent['champion_rows']), name)),
                   rows=deepcopy(parent['champion_rows']), generation=parent['next_generation'] - 1)
        for name in ('current', 'paired')}
    return state


class PairSearch(SkillSearch):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not kwargs.get('resume', False):
            raise ValueError('V12E must fork saved random-origin states')
        self.common_archives = json.loads(self.checkpoint.read_text())['common_archives']
        self._training = []

    def evaluate(self, item, pairs, split, generation):
        ev = evaluate(item, pairs, self.config['topology'], Limits(**self.config['limits']), True)
        original = ev.fitness
        policy = self.config['selection_policy']
        ev.fitness = priority(original, policy)
        if policy == 'paired':
            ev.case_values = [(p, v, o, s) for v, o, p, s in ev.case_values]
        self.work += ev.work
        self.responses += len(ev.rows)
        self.evaluations.write(json.dumps(dict(condition=self.key, id=item.identity, split=split,
            generation=generation, fitness=ev.fitness, raw_fitness=original,
            descriptor=ev.descriptor, work=ev.work, cases=ev.rows), separators=(',', ':')) + '\n')
        if split == 'train':
            self._training.append((item.genome.digest, original))
        if split.startswith('validation'):
            for name in ('current', 'paired'):
                rank = priority(original, name)
                if rank > tuple(self.common_archives[name]['rank']):
                    self.common_archives[name] = dict(item=item.save(), rank=rank,
                                                      rows=ev.rows, generation=generation)
            rates = {}
            for level in range(4):
                rows = [r for r in ev.rows if f'/level{level}/' in r['case']]
                rank = skill_rank(rows)
                key = str(level)
                if rank > tuple(self.skills[key]['rank']):
                    self.skills[key] = dict(item=item.save(), rank=rank, rows=rows, generation=generation)
                rates[key] = sum(r['pair_optimal'] for r in rows) / len(rows)
            for level in certified_levels(rates):
                self.competence.setdefault(str(level), dict(id=item.identity, generation=generation, rates=rates))
        return ev

    def step(self, batch, validation, level=0):
        self._training = []
        super().step(batch, validation, level)
        record = self.history[-1]
        maxima = {name: max(priority(rank, name) for _, rank in self._training)
                  for name in ('current', 'paired')}
        winners = {name: sorted({dna for dna, rank in self._training
                    if priority(rank, name) == maxima[name]}) for name in maxima}
        record.update(common_archives={name: {k: value[k] for k in ('rank', 'generation')}
                      | {'id': value['item']['id']} for name, value in self.common_archives.items()},
                      population_sha256=digest([item.genome.digest for item in self.population]),
                      rng_sha256=digest(self.rng.getstate()),
                      ordering_top_genotypes_differ=winners['current'] != winners['paired'],
                      maximum_train_complete_pairs=max(rank[3] for _, rank in self._training))
        self._training = []
        return record

    def state(self):
        return dict(**super().state(), common_archives=self.common_archives)

    def selection(self):
        return dict(**super().selection(), common_archives=self.common_archives)
