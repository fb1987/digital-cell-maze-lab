"""Pure saved-row metrics for M26. No VM, dataset or selection imports."""
from collections import defaultdict
import hashlib
import json

ORDINARY = {'ordinary_perfect', 'ordinary_random'}
FIELDS = ('pairs', 'corridors', 'ordinary', 'no_path')


def genome_info(genome):
    blocks = genome['body']['blocks']
    instructions = sum(len(b) + bool(b) for b in blocks)
    return dict(instructions=instructions,
                append_total_eligible=instructions + 3 <= 128,
                append_any_writer_eligible=any(b and len(b) + 3 <= 31 for b in blocks),
                digest=hashlib.sha256(json.dumps(genome, sort_keys=True, separators=(',', ':')).encode()).hexdigest()[:20])


def append_reason(parent_instructions, activation_index):
    total = parent_instructions + 3 > 128
    writer = activation_index + 3 > 31
    return 'both_bounds' if total and writer else 'total128_only' if total else 'writer31_only' if writer else 'admitted'


class Panel:
    def __init__(self, meta, queries, fresh, bank):
        assert len(queries) == len(set(queries))
        self.queries = set(queries)
        self.meta = {c: meta[c] for c in queries}
        self.bases = defaultdict(list)
        self.pairs = defaultdict(list)
        self.lengths = {}
        self.source = {}
        self.fresh, self.bank = set(fresh), set(bank)
        for c, m in self.meta.items():
            if m['family'] in ORDINARY:
                self.bases[m['base']].append(c)
                self.lengths[m['base']] = len(m['path']) - 1
            if m['family'] == 'paired':
                self.pairs[(m['base'], m['pose'])].append(c)
        for b, cs in self.bases.items():
            assert len(cs) == 2 and len({self.meta[c]['pose'] for c in cs}) == 2
            assert len({len(self.meta[c]['path']) - 1 for c in cs}) == 1
            assert set(cs) <= self.fresh or set(cs) <= self.bank
            self.source[b] = 'fresh' if set(cs) <= self.fresh else 'bank'
        assert all(len(cs) == 2 for cs in self.pairs.values())
        self.target = {b for b, length in self.lengths.items() if length >= 8}
        self.long = {b for b, length in self.lengths.items() if length >= 16}
        self.target_cases = {c for b in self.target for c in self.bases[b]}

    def profile(self, rows):
        assert len(rows) == len(self.queries) and {r['case'] for r in rows} == self.queries
        optimal = {r['case'] for r in rows if r['optimal']}
        ordinary = {b for b, cs in self.bases.items() if set(cs) <= optimal}
        return dict(ordinary=ordinary, ordinary8=ordinary & self.target, ordinary16=ordinary & self.long,
                    single8=optimal & self.target_cases,
                    pairs={p for p, cs in self.pairs.items() if set(cs) <= optimal},
                    corridors={r['case'] for r in rows if r['optimal'] and self.meta[r['case']]['family'] == 'corridor'},
                    no_path={r['case'] for r in rows if r['no_path']},
                    false={r['case'] for r in rows if r['reachable'] and r['status'] == 'no_path'},
                    success={r['case'] for r in rows if r['optimal'] or r['no_path']})


def union_profiles(profiles):
    return {k: set().union(*(p[k] for p in profiles)) for k in profiles[0]}


def compare(child, parent):
    if parent is None:
        return None
    result = {k: dict(before=len(parent[k]), retained=len(parent[k] & child[k]),
                      gained=len(child[k] - parent[k]), lost=len(parent[k] - child[k])) for k in FIELDS}
    result['ordinary8'] = dict(before=len(parent['ordinary8']), retained=len(parent['ordinary8'] & child['ordinary8']),
                               gained=len(child['ordinary8'] - parent['ordinary8']), lost=len(parent['ordinary8'] - child['ordinary8']))
    result['all_old_correct_inputs_retained'] = parent['success'] <= child['success']
    result['domain90_and_disconnection90_zero_false'] = (
        all(10 * len(parent[k] & child[k]) >= 9 * len(parent[k]) for k in FIELDS)
        and bool(parent['no_path']) and not child['false'])
    return result


def novelty(profile, references, panel):
    complete = profile['ordinary8'] - references['ordinary8']
    single = profile['single8'] - references['single8']
    # A two-pose base may be new as an individual solver's combination even when
    # a portfolio of different references already solves both individual poses.
    beyond_collective = {b for b in complete if set(panel.bases[b]) & single}
    return dict(complete=complete, single=single, beyond_collective=beyond_collective)


def counts(profile):
    return {k: len(v) for k, v in profile.items()}


def cohort_flags(record):
    first = record.get('first')
    if first is None:
        return {'training_censored': True}
    return dict(first_exposed=True, genotype_changed=not record['noop'],
                ordinary8=first['counts']['ordinary8'] > 0,
                ordinary16=first['counts']['ordinary16'] > 0,
                novel_complete8=first['novel_complete8'] > 0,
                novel_single8=first['novel_single8'] > 0,
                novel_complete8_beyond_collective=first['novel_complete8_beyond_collective'] > 0,
                false_no_path=first['counts']['false'] > 0,
                parent_comparison_available=first['parent'] is not None,
                parent_ordinary8_gain=bool(first['parent'] and first['parent']['ordinary8']['gained']),
                parent_gain_with_full_correct_retention=bool(first['parent'] and first['parent']['ordinary8']['gained'] and first['parent']['all_old_correct_inputs_retained'] and not first['counts']['false']),
                novel_complete8_with_root90=bool(first['novel_complete8'] and first['root'] and first['root']['domain90_and_disconnection90_zero_false']))
