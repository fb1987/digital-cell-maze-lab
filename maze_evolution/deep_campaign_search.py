"""Bounded mutation-only discovery and a behavioral coverage archive.

The archive is inspired by quality-diversity, not an implementation of MAP-Elites.
All archive candidates are rescored on the SAME fresh assessment before selection.
"""
from collections import Counter, defaultdict
from copy import deepcopy
import random

from .exposure_genome import Individual, Genome
from .exposure_selection import evaluate
from .foundation_fitness import lexicase
from .growth import random_genome, mutate, replay_mutation
from .linkage_restart_operator import mutate_ids
from .regulatory_search import tuple_tree
from .routing_transfer import canonical
from .selectivity_search import assert_population, ranked
from .shared_prefix_search import digest


def initial_states(old):
    result = []
    for island in range(3):
        source = old[f'carry/{island}/current']
        s = deepcopy(source)
        s.update(key=f'deep_v1/island{island}', generation=0, serial=0, archives={},
                 origin=dict(stage='selectivity_pressure', key=source['key'],
                             generation=source['generation'], state_digest=digest(source)),
                 frontier=1, promotion_streak=0, assessment_generation=-1,
                 coverage_archive=[], reinject=[], frozen_references=deepcopy(source['protected']))
        assert_population(s)
        result.append(canonical(s))
    return result


def candidates(s, assessment=False):
    raw = {r['id']:r for r in s['population']}
    if assessment:
        for a in s['coverage_archive']:
            raw[a['item']['id']] = a['item']
        for r in s['frozen_references']:
            raw[r['id']] = r
    return [Individual.load(r) for r in raw.values()]


def features(rows, meta):
    pairs = defaultdict(list)
    success, strata = set(), {}
    for r in rows:
        m = meta[r['case']]
        if m['family'] == 'paired':
            pairs[m['base'], m['pose']].append(r)
        else:
            k = 'single:' + r['case']
            strata[k] = m['family']
            if r['optimal'] or r['no_path']:
                success.add(k)
    for (base, pose), rr in pairs.items():
        assert len(rr) == 2
        m = meta[rr[0]['case']]
        k = f'pair:{base}:{pose}'
        strata[k] = f'paired/{m["graph"]}/prefix{m["prefix"]}'
        if all(r['optimal'] for r in rr):
            success.add(k)
    return success, strata


def coverage_select(items, rows, meta, limit=32):
    """Four aggregate elites, then normalized marginal successful-case coverage."""
    rank = ranked(items, rows, meta)
    unique = []
    seen = set()
    for ev, i in rank:
        if i.genome.digest not in seen:
            unique.append(i)
            seen.add(i.genome.digest)
    feature_map = {i.identity:features(rows[i.identity], meta)[0] for i in unique}
    strata = features(rows[unique[0].identity], meta)[1]
    totals = Counter(strata.values())
    weights = {k:1. / totals[v] for k, v in strata.items()}
    chosen = unique[:min(4, limit)]
    covered = set().union(*(feature_map[i.identity] for i in chosen))
    remaining = unique[len(chosen):]
    order = {i.identity:k for k, i in enumerate(unique)}
    while remaining and len(chosen) < limit:
        best = min(remaining, key=lambda i:(
            -sum(weights[k] for k in sorted(feature_map[i.identity] - covered)),
            order[i.identity]))
        chosen.append(best)
        covered.update(feature_map[best.identity])
        remaining.remove(best)
    return chosen, dict(success_features=len(covered), strata=dict(totals),
                        identities=[i.identity for i in chosen])


def assess_state(state, rows, meta):
    s = deepcopy(state)
    items = candidates(s, True)
    chosen, report = coverage_select(items, rows, meta)
    ancestry = {r['id']:dict(gene_ids=s['gene_ids'][r['id']],
                            family=s['families'][r['id']]) for r in s['population']}
    ancestry.update({a['item']['id']:dict(gene_ids=a['gene_ids'], family=a['family'])
                     for a in s['coverage_archive']})
    # Frozen references are protected members, so their locus records remain live.
    s['coverage_archive'] = [dict(item=i.save(), **ancestry[i.identity])
                             for i in chosen]
    live = {r['id'] for r in s['population']}
    s['reinject'] = [i.identity for i in chosen if i.identity not in live][:4]
    s['assessment_generation'] = s['generation']
    # Require one genome, not a union of specialists, to clear every graph stratum.
    passes = []
    for i in items:
        success, strata = features(rows[i.identity], meta)
        wanted = [f'paired/{graph}/prefix{s["frontier"]}'
                  for graph in ('fork', 'two_junction', 'cycle')]
        passes.append(all(
            sum(k in success for k, v in strata.items() if v == group) >=
            .8 * sum(v == group for v in strata.values()) > 0
            for group in wanted))
    s['promotion_streak'] = s['promotion_streak'] + 1 if any(passes) else 0
    if s['promotion_streak'] >= 2 and s['frontier'] < 8:
        levels = (1, 2, 4, 8)
        s['frontier'] = levels[levels.index(s['frontier']) + 1]
        s['promotion_streak'] = 0
    report.update(frontier=s['frontier'], promotion_streak=s['promotion_streak'],
                  reinject=s['reinject'],
                  fitness={i.identity:list(evaluate(rows[i.identity], meta).fitness)
                           for i in items})
    report['capabilities'] = {}
    for i in items:
        success, strata = features(rows[i.identity], meta)
        report['capabilities'][i.identity] = dict(
            by_stratum=dict(Counter(strata[k] for k in success)),
            false_no_path=sum(r['reachable'] and r['status'] == 'no_path'
                              for r in rows[i.identity]),
            shortest=sum(r['optimal'] for r in rows[i.identity]),
            legal=sum(r['valid'] for r in rows[i.identity]))
    return canonical(s), report


def reproduce(state, rows, meta):
    assert_population(state)
    rng = random.Random()
    rng.setstate(tuple_tree(state['rng']))
    before = digest(state['rng'])
    rank = ranked(candidates(state), rows, meta)
    registry = {i.identity:i for _, i in rank}
    selected, seen = [], set()
    loci = deepcopy(state['gene_ids'])
    families = deepcopy(state['families'])
    reasons = []

    def add(i, reason):
        if i.identity not in seen and len(selected) < 44:
            selected.append(i)
            seen.add(i.identity)
            reasons.append([i.identity, reason])

    for r in state['protected']:
        add(registry[r['id']], 'protected')
    for _, i in rank[:4]:
        add(i, 'merit')
    archive = {a['item']['id']:a for a in state['coverage_archive']}
    for identity in state['reinject']:
        a = archive[identity]
        add(Individual.load(a['item']), 'assessed_coverage_archive')
        loci[identity], families[identity] = a['gene_ids'], a['family']
    behaviors = set()
    for ev, i in rank:
        behavior = digest([(r['mask'], r['status']) for r in ev.rows])
        if behavior not in behaviors:
            add(i, 'behavior')
            behaviors.add(behavior)
    for _, i in rank:
        add(i, 'rank_fill')
    assert len(selected) == 44
    births = []
    for k in range(52):
        name = f'{state["key"]}/i{state["serial"] + k}'
        assert name not in loci
        parent, events = None, None
        if k < 7:
            genome = Genome(random_genome(rng, True), 7)
            genes = [f'{name}/gene{j}' for j in range(len(genome.genes))]
            family = name
        else:
            parent = rng.choice(rank)[1] if rng.random() < .1 else lexicase(rng, rank)
            program, events = mutate(parent.genome.program, rng, 1, 256, True)
            assert replay_mutation(parent.genome.program, events, 256) == program
            genome = Genome(program, 7)
            genes = mutate_ids(loci[parent.identity], events, name)
            family = families[parent.identity]
        i = Individual(name, genome, parent.identity if parent else None,
                       state['generation'] + 1)
        selected.append(i)
        loci[name], families[name] = genes, family
        births.append(dict(item=i.save(), gene_ids=genes, family=family,
                           mutation=events, parents=[parent.identity] if parent else []))
    new = deepcopy(state)
    new.update(population=[i.save() for i in selected],
               gene_ids={i.identity:loci[i.identity] for i in selected},
               families={i.identity:families[i.identity] for i in selected},
               rng=canonical(rng.getstate()), generation=state['generation'] + 1,
               serial=state['serial'] + 52, reinject=[])
    assert_population(new)
    return canonical(new), dict(births=births, survivors=reasons, rng_before=before,
                                rng_after=digest(new['rng']), population=digest(new['population']),
                                fitness={i.identity:list(ev.fitness) for ev, i in rank})
