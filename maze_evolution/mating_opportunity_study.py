"""V12Y fixed-parent opportunity assay; zero maze generation or organism calls."""
import argparse
from collections import Counter, OrderedDict, defaultdict
from contextlib import ExitStack
import gzip
import hashlib
import json
from pathlib import Path
import platform
import random
import resource
import subprocess
import time
from .mating_opportunity_operator import options, virtual, seed, RULES
from .linkage_restart_study import prior_check as prior_x
from .routing_transfer import lines, logrow, sha
from .foundation_study import read_compressed
from .shared_prefix_search import digest

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT/'results/linkage_restart'
OUT = ROOT/'results/mating_opportunity'
SEED = 2026102003
SNAPSHOTS = (0, 8, 16, 24, 32)
WALL_CAP = 900
PAIR_CAP = 400000


def write(path, data):
    path.write_text(json.dumps(data, indent=2)+'\n')


def prior_check():
    n = prior_x()
    for name, value in json.loads((OLD/'completion.json').read_text())['source_and_artifact_sha256'].items():
        assert sha(ROOT/name) == value, name
        n += 1
    assert n == 6667
    return n


def freeze():
    assert not OUT.exists()
    OUT.mkdir()
    files = [ROOT/'docs/MATING_OPPORTUNITY_V12Y.md', ROOT/'tests/test_mating_opportunity.py',
             *sorted((ROOT/'maze_evolution').glob('*.py'))]
    inputs = [OLD/p for p in ('initial_states.json.gz', 'reproduction.jsonl.gz', 'next_states.json.gz',
                             'checkpoints/g16.json.gz', 'checkpoints/g32.json.gz',
                             'whole_layout_exclusions.json.gz', 'completion.json')]
    write(OUT/'preregistration.json', dict(seed=SEED, prior_hash_entries=prior_check(),
        candidate_calls=0, new_mazes=0, wall_cap=WALL_CAP, pair_cap=PAIR_CAP,
        sources={str(p.relative_to(ROOT)):sha(p) for p in files},
        inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},
        python=platform.python_version(), platform=platform.platform()))


def check_freeze(committed=False):
    reg = json.loads((OUT/'preregistration.json').read_text())
    for group in ('sources', 'inputs'):
        for name, value in reg[group].items():
            assert sha(ROOT/name) == value, name
    if committed:
        assert subprocess.check_output(['git','rev-parse','HEAD']) == subprocess.check_output(['git','rev-parse','origin/main'])
        assert subprocess.check_output(['git','show','HEAD:results/mating_opportunity/preregistration.json']) == (OUT/'preregistration.json').read_bytes()
    return reg


def node(raw, ids, roots):
    program = tuple(tuple(row) for row in raw['genome']['genes'])
    ids = tuple(ids)
    assert len(ids) == len(program) == len(set(ids))
    return dict(raw=raw, ids=ids, program=program, roots=frozenset(roots),
                signature=digest([raw['genome'], ids]), genotype=digest(raw['genome']))


def initial():
    saved = read_compressed(OLD/'initial_states.json.gz')
    populations = {}
    protected = {}
    for key, state in saved.items():
        populations[key] = {}
        protected[key] = {r['id']:r for r in state['protected']}
        for raw in state['population']:
            ids = state['gene_ids'][raw['id']]
            root = 'known_U_d07' if any(i.startswith('known_U_d07/') for i in ids) else raw['id']
            populations[key][raw['id']] = node(raw, ids, (root,))
    return populations, protected


def family_row(key, generation, pop, protected):
    counts = Counter()
    mutable = Counter()
    for identity, item in pop.items():
        for root in item['roots']:
            counts[root] += 1/len(item['roots'])
            if identity not in protected:
                mutable[root] += 1/len(item['roots'])
    effective = lambda c: sum(c.values())**2/sum(v*v for v in c.values()) if c else 0.
    return dict(key=key, generation=generation, members=len(pop), protected=len(protected),
                root_membership_weights=dict(counts), mutable_root_weights=dict(mutable),
                roots=len(counts), mutable_roots=len(mutable),
                effective_roots=effective(counts), effective_mutable_roots=effective(mutable),
                unique_genotypes=len({n['genotype'] for n in pop.values()}))


def build_stats(pool):
    result = {}
    for length in (2,4,8,16,32):
        p = [v for v in pool if v[1]-v[0] == length]
        result[str(length)] = [len(p), sum(v[4]>=2 for v in p),
            sum(v[5] for v in p), sum(v[5] and v[4]>=2 for v in p),
            sum(v[6] for v in p), sum(v[6] and v[4]>=2 for v in p)]
    return result


def possible(stats, cap, rule):
    for size, (n,m,fn,fm,gn,gm) in stats.items():
        if int(size)>cap:
            continue
        if rule == 'unlinked' and m:
            return True
        if rule == 'transitive' and fm or rule == 'gate' and gm:
            return True
        if rule == 'sham_transitive' and fn and m or rule == 'sham_gate' and gn and m:
            return True
    return False


class Assay:
    def __init__(self, audit=False):
        self.audit = audit
        self.start = time.perf_counter()
        self.seen = set()
        self.cache = OrderedDict()
        self.aggregate = defaultdict(Counter)
        self.unique = defaultdict(set)
        self.active = defaultdict(set)
        self.pair_occurrences = 0
        self.opportunities = 0
        self.families = 0
        self.stage_counts = Counter()

    def check(self):
        assert len(self.seen) <= PAIR_CAP, 'Static pair cap'
        assert time.perf_counter()-self.start < (1800 if self.audit else WALL_CAP), 'Static wall cap'
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < 3*2**30, 'Static memory cap'
        if self.opportunities % 512 == 0:
            assert sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()) < 3*2**30, 'Static artifact cap'

    def emit(self, name, value):
        if self.audit:
            assert next(self.streams[name], None) == json.loads(json.dumps(value)), (name, self.opportunities)
        else:
            logrow(self.streams[name], value)

    def pair(self, key, generation, recipient, donor):
        self.pair_occurrences += 1
        identity = recipient['signature'] + '/' + donor['signature']
        if identity in self.cache:
            self.cache.move_to_end(identity)
            return self.cache[identity]
        if self.audit:
            from .mating_opportunity_independent import options as implementation
        else:
            implementation = options
        pool, reason = implementation(recipient['program'], donor['program'], recipient['ids'], donor['ids'])
        packet = dict(pair=identity, first_reference=dict(key=key, generation=generation,
            recipient=recipient['raw']['id'], donor=donor['raw']['id']), reason=reason,
            genotype_pair=recipient['genotype']+'/'+donor['genotype'],
            segments=[list(v) for v in pool], stats=build_stats(pool))
        if identity not in self.seen:
            self.seen.add(identity)
            self.emit('pairs', packet)
        result = (pool, packet['stats'], identity, packet['genotype_pair'])
        self.cache[identity] = result
        if len(self.cache)>4096:
            self.cache.popitem(last=False)
        return result

    def probe(self, kind, key, generation, label, parent_id, views, pop):
        self.check()
        self.opportunities += 1
        self.stage_counts[kind] += 1
        parent = pop[parent_id]
        candidates = list(dict.fromkeys(d for view in views.values() for d in view))
        pairs = {d:self.pair(key, generation, parent, pop[d]) for d in candidates}
        result = {}
        for view, donors in views.items():
            donors = list(dict.fromkeys(donors))
            ranked = sorted(donors, key=lambda d: (seed(SEED, kind, key, generation, label, 'donor', d), d))
            for cap in (16,32):
                eligible = [d for d in ranked if any(v[1]-v[0]<=cap for v in pairs[d][0])]
                chosen = eligible[0] if eligible else None
                pool = pairs[chosen][0] if chosen is not None else ()
                outcomes = virtual(pool, cap, seed(SEED, kind, key, generation, label, view, cap, 'ticket'))
                all_possible = {rule:any(possible(pairs[d][1],cap,rule) for d in donors) for rule in RULES}
                result[view+'/'+str(cap)] = dict(donors=donors, eligible=eligible, chosen=chosen,
                    opportunity=all_possible, outcomes=outcomes)
                for rule, outcome in outcomes.items():
                    group = '/'.join((kind,key,view,str(cap),rule))
                    row = self.aggregate[group]
                    row['attempts'] += 1
                    row['eligible_donor'] += bool(eligible)
                    row['eligible_donor_count'] += len(eligible)
                    row['any_multi_donor_segment'] += all_possible[rule]
                    row['accepted'] += outcome['accepted']
                    row['multi'] += outcome['multi']
                    row['expected_multi'] += outcome['expected_multi']
                    if outcome['multi']:
                        self.active[group].add(generation)
                    for d in donors:
                        self.unique[group].add(pairs[d][3])
        self.emit('opportunities', dict(kind=kind,key=key,generation=generation,label=label,
            parent=parent_id, views=result))

    def snapshot(self, key, generation, pop, protected):
        self.families += 1
        self.emit('families', family_row(key,generation,pop,protected))
        rng = random.Random(seed(SEED,'snapshot',key,generation))
        parents = rng.sample(sorted(pop),16)
        for j, parent in enumerate(parents):
            donors = rng.sample(sorted(set(pop)-{parent}),8)
            self.probe('snapshot',key,generation,j,parent,dict(uniform8=donors),pop)

    def execute(self):
        pops, protected = initial()
        for key,pop in pops.items():
            self.snapshot(key,0,pop,protected[key])
        event_count = 0
        for event in lines(OLD/'reproduction.jsonl.gz'):
            event_count += 1
            key, g = event['key'], event['generation']
            pop = pops[key]
            assert len(pop)==96
            for identity,raw in protected[key].items():
                assert pop[identity]['raw']==raw
            for j,birth in enumerate(event.get('births',[])):
                if birth['mating'] is None:
                    continue
                parent = birth['parents'][0]
                historical = list(dict.fromkeys(birth['mating']['shortlist']))
                rng = random.Random(seed(SEED,'other_donors',key,g,j))
                extra = rng.sample(sorted(set(pop)-set(historical)-{parent}),8)
                actual = [] if birth['proposed_donor'] is None else [birth['proposed_donor']]
                self.probe('historical',key,g,j,parent,
                    dict(actual=actual,shortlist=historical,other8=extra,union=historical+extra),pop)
            if not event.get('frozen'):
                new = {identity:pop[identity] for identity in event['elite']}
                for birth in event['births']:
                    roots = set().union(*(pop[i]['roots'] for i in birth['parents'])) if birth['parents'] else {birth['item']['id']}
                    raw = birth['item']
                    assert raw['id'] not in pop and raw['id'] not in new
                    new[raw['id']] = node(raw,birth['gene_ids'],roots)
                pop = pops[key] = new
            assert digest([n['raw'] for n in pop.values()])==event['population']
            if g+1 in SNAPSHOTS:
                self.snapshot(key,g+1,pop,protected[key])
            if event_count%144==0:
                print(json.dumps(dict(events=event_count,unique_pairs=len(self.seen),
                    opportunities=self.opportunities,wall=round(time.perf_counter()-self.start,2))),flush=True)
        assert event_count==1152 and self.stage_counts==dict(historical=18432,snapshot=2880)
        final = read_compressed(OLD/'next_states.json.gz')
        for key,pop in pops.items():
            assert [n['raw'] for n in pop.values()]==final[key]['population']
            assert {i:list(n['ids']) for i,n in pop.items()}==final[key]['gene_ids']
        result = {}
        for group,row in sorted(self.aggregate.items()):
            result[group] = dict(row, expected_fraction=row['expected_multi']/row['attempts'],
                multi_fraction=row['multi']/row['attempts'], active_generations=len(self.active[group]),
                unique_genotype_pairs=len(self.unique[group]))
        return dict(by_condition=result, scope='Static pre-mutation opportunities on inspected X-R1 histories. No maze efficacy or post-mutation activation inference.',
                    decision=decision(result))


def decision(result):
    # A design screen only: 12% expected pre-mutation rate supplies a small margin
    # over the separately required 10% actual retained-transfer pilot gate.
    rates = {}
    qualified = []
    for cap in (16,32):
        passes = {origin:[] for origin in ('carry','fresh')}
        for origin in passes:
            for rep in range(3):
                values = {}
                for rule in ('gate','sham_gate','unlinked'):
                    entries = [result[f'historical/{origin}/{rep}/{arm}/union/{cap}/{rule}']
                               for arm in ('linked','unlinked','sham')]
                    values[rule] = sum(e['expected_fraction'] for e in entries)/3
                rates[f'{origin}/{rep}/{cap}'] = values
                if min(values.values())>=.12:
                    passes[origin].append(rep)
        if all(len(v)>=2 for v in passes.values()):
            qualified.append(cap)
    return dict(expected_fraction_by_origin_rep_cap=rates, qualifying_caps=qualified,
        selected_cap=qualified[0] if qualified else None,
        next_step='new_activation_pilot' if qualified else 'design_related_lineage_diversity',
        long_efficacy_run_authorized=False, static_screen_is_not_activation_gate=True)


def run(audit=False):
    reg = check_freeze(not audit)
    assert prior_check()==6667
    if audit:
        assert (OUT/'execution.json').exists() and not (OUT/'audit.json').exists()
    else:
        assert not (OUT/'pairs.jsonl.gz').exists()
    assay = Assay(audit)
    with ExitStack() as stack:
        assay.streams = {name:iter(lines(OUT/(name+'.jsonl.gz'))) if audit else
                         stack.enter_context(gzip.open(OUT/(name+'.jsonl.gz'),'wt',compresslevel=1))
                         for name in ('pairs','opportunities','families')}
        result = assay.execute()
        if audit:
            for name,it in assay.streams.items():
                assert next(it,None) is None, name
            assert result==json.loads((OUT/'analysis.json').read_text())
        else:
            write(OUT/'analysis.json',result)
    assay.check()
    packet = dict(complete=True, passed=True, candidate_calls=0,new_mazes=0,
        wall_seconds=time.perf_counter()-assay.start, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        unique_homology_aware_pairs=len(assay.seen),pair_occurrences=assay.pair_occurrences,
        opportunities=assay.opportunities,stages=dict(assay.stage_counts),family_snapshots=assay.families,
        prior_hash_entries=6667,source_hashes=len(reg['sources']),input_hashes=len(reg['inputs']),
        revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        audit_method='Independent backwards/set segment and dependency reconstruction; exact raw opportunity, family, aggregate and final population replay.' if audit else None)
    write(OUT/('audit.json' if audit else 'execution.json'),packet)
    print(json.dumps(packet,indent=2),flush=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('freeze','run','audit'))
    args=parser.parse_args()
    freeze() if args.action=='freeze' else run(args.action=='audit')


if __name__=='__main__':
    main()
