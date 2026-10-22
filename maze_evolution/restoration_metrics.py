"""M16 prospective restoration criteria. Evaluation only; never candidate inference."""
from collections import defaultdict
from .breeding_allocation_metrics import capabilities_plus, upstream_pairs, comparison
from .modular_pilot_search import rank
from .routing_transfer import canonical

FIELDS = ('pairs', 'corridors', 'ordinary_bases', 'correct_no_path')


def reference_sets(rows, meta, protected):
    caps = {i: capabilities_plus(rs, meta) for i, rs in rows.items()}
    union = {k: set().union(*(caps[i][k] for i in protected)) for k in (*FIELDS, 'success')}
    targets = upstream_pairs(caps['anchor/child'], meta) - union['pairs']
    pm = {(m['base'], m['pose']): m for m in meta.values() if m['family'] == 'paired'}
    return caps, union, targets, pm


def feature(cap, parent, child, targets, pm):
    # Require every skill of both anchors, not merely equal aggregate totals.
    required = {k: parent[k] | child[k] for k in FIELDS}
    fractions = {k: len(cap[k] & required[k]) / len(required[k]) if required[k] else None for k in FIELDS}
    contexts = {pm[p]['template'] for p in targets}
    target_fraction = len(cap['pairs'] & targets) / len(targets) if targets else None
    eligible = bool(len(targets) >= 8 and len(contexts) >= 2 and all(required[k] for k in FIELDS))
    passed = bool(eligible and not cap['false'] and all(required[k] <= cap[k] for k in FIELDS) and targets <= cap['pairs'])
    # Joint ranking has no hard retention filter: partial repairs remain visible.
    values = [0. if x is None else x for x in [target_fraction, *fractions.values()]]
    score = [int(passed), -len(cap['false']), min(values), sum(values), len(cap['pairs'] & targets),
             len(cap['ordinary_bases']), len(cap['pairs']), -cap['summary']['work']]
    return dict(metrics=cap['summary'], reference_eligible=eligible, joint_restoration_pass=passed,
                target_pairs=len(targets), target_contexts=len(contexts), retained_targets=len(cap['pairs'] & targets),
                target_fraction=target_fraction, required_counts={k: len(v) for k, v in required.items()},
                retention=fractions, lost_required={k: len(required[k]-cap[k]) for k in FIELDS}, score=score)


def nominate(items, rows, data, protected):
    caps, union, targets, pm = reference_sets(rows, data['metadata'], protected)
    features = {i: feature(c, caps['anchor/parent'], caps['anchor/child'], targets, pm) for i, c in caps.items()}
    nominations = []
    for anchor in ('parent', 'child'):
        for depth in (1, 2):
            ids = [i['id'] for i in items if i.get('anchor') == anchor and i.get('depth') == depth and i['kind'] == 'mutation']
            assert ids
            for method in ('joint', 'aggregate'):
                score = lambda i: features[i]['score'] if method == 'joint' else rank(rows[i], data['metadata'])
                chosen = min(ids, key=lambda i: (tuple(-v for v in score(i)), i))
                nominations.append(dict(label=f'{anchor}/depth{depth}/{method}', identity=chosen, anchor=anchor, depth=depth, method=method))
    for kind in ('diagnostic', 'random'):
        ids = [i['id'] for i in items if i['kind'] == kind]
        chosen = min(ids, key=lambda i: (tuple(-v for v in features[i]['score']), i))
        nominations.append(dict(label=kind+'/joint', identity=chosen, method='joint', kind=kind))
    return canonical(dict(nominations=nominations, features=features, reference_eligible=features['anchor/child']['reference_eligible']))


def summarize(items, nominations, rows, data, protected):
    caps, union, targets, pm = reference_sets(rows, data['metadata'], protected)
    meta=data['metadata']; lookup={i['id']:i for i in items}; models={}
    groups=defaultdict(set)
    queried=set(data['queries']['all'])
    for cid,m in meta.items():
        if cid in queried and m['family'] in ('ordinary_perfect','ordinary_random'):
            groups[f"{m['family']}/{m['size']}/{m['length_bin']}"].add(m['base'])
    for i,cap in caps.items():
        models[i]=dict(kind=lookup[i]['kind'], **feature(cap,caps['anchor/parent'],caps['anchor/child'],targets,pm),
          versus_parent=comparison(cap,caps['anchor/parent'],meta),versus_child=comparison(cap,caps['anchor/child'],meta),
          beyond_protected={k:len(cap[k]-union[k]) for k in (*FIELDS,'success')},
          ordinary_length_strata={k:dict(bases=len(bs),correct_both_poses=len(bs&cap['ordinary_bases'])) for k,bs in groups.items()})
    reports=[dict(**n, result=models[n['identity']]) for n in nominations]
    return canonical(dict(models=models,nominations=reports, target_pair_keys=sorted(targets),
        primary_passes=[n['label'] for n in reports if n.get('method')=='joint' and n.get('anchor') and n['result']['joint_restoration_pass']],
        diagnostic_passes=[n['label'] for n in reports if n.get('kind')=='diagnostic' and n['result']['joint_restoration_pass']],
        reference_eligible=models['anchor/child']['reference_eligible'],inputs=len(queried),
        limitation='Fixed one-/two-edit neighborhoods of two related anchors; diagnostic edits are not evolved offspring. Equal nomination inputs, not independent origins or evidence of general solving.'))
