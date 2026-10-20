"""Prepared survivor policy for a NEW controlled experiment, not applied to X/Y.

Ranked records carry id, family, genotype, gene_ids, genes and behavior. The caller
provides fitness ordering. Family records are immutable random-origin ancestry
labels, not inferred from matching instructions. No maze fitness is invented here.
"""


def distance(a, b):
    if a['genotype'] == b['genotype']:
        return 0.
    aa = dict(zip(a['gene_ids'], map(tuple, a['genes'])))
    bb = dict(zip(b['gene_ids'], map(tuple, b['genes'])))
    loci = set(aa) | set(bb)
    return sum(aa.get(i) != bb.get(i) for i in loci)/max(1,len(loci))


def retain(ranked, protected_ids, policy, count=44, merit_slots=4,
           family_count=5, variants_per_family=4):
    assert policy in ('current','family')
    registry = {r['id']:r for r in ranked}
    assert len(registry)==len(ranked) and len(ranked)>=count
    assert len(protected_ids)==len(set(protected_ids))
    assert set(protected_ids)<=set(registry)
    assert len(protected_ids)+merit_slots+family_count*variants_per_family<=count
    for item in ranked:
        assert len(item['gene_ids'])==len(item['genes'])==len(set(item['gene_ids']))
    selected=[];seen=set();reserved=[]

    def add(item, reason):
        if len(selected)<count and item['id'] not in seen:
            selected.append(item);seen.add(item['id'])
            reserved.append(dict(id=item['id'],reason=reason,family=item['family']))
            return True
        return False

    for identity in protected_ids:
        add(registry[identity],'protected')
    target=len(selected)+merit_slots
    for item in ranked:
        if len(selected)>=target:
            break
        add(item,'merit')
    families=[]
    if policy=='family':
        for item in ranked:
            if item['id'] not in seen and item['family'] not in families:
                families.append(item['family'])
                if len(families)==family_count:
                    break
        rank_index={r['id']:i for i,r in enumerate(ranked)}
        for _ in range(variants_per_family):
            for family in families:
                existing=[r for r in selected if r['family']==family]
                genotypes={r['genotype'] for r in existing}
                available=[r for r in ranked if r['family']==family and r['id'] not in seen and r['genotype'] not in genotypes]
                if not available:
                    continue
                # Start with the best-ranked member; then maximize minimum
                # inherited-locus distance, breaking ties by original fitness rank.
                if existing:
                    available.sort(key=lambda r:(-min(distance(r,e) for e in existing),rank_index[r['id']]))
                add(available[0],'family_variant')
    behaviors={r['behavior'] for r in selected}
    for item in ranked:
        if item['behavior'] not in behaviors:
            add(item,'behavior');behaviors.add(item['behavior'])
    for item in ranked:
        add(item,'rank_fill')
    assert len(selected)==len({r['id'] for r in selected})==count
    assert set(protected_ids)<=seen
    return selected,dict(policy=policy,families=families,selection=reserved,
                        family_reserved=sum(r['reason']=='family_variant' for r in reserved))
