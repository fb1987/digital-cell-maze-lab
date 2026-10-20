"""Independent set/backwards implementation of V12Y static segment admissibility."""
from .linkage_restart_audit import independent_groups


def gate_groups(program):
    result = []
    for i, row in enumerate(program):
        if row[0] != 13:
            continue
        group = {i}
        if row[6] != 64:
            for j in range(i-1, -1, -1):
                earlier = program[j]
                if earlier[0] != 13 and earlier[1] == row[6]:
                    group.add(j)
                    if earlier[6] == 64:
                        break
        result.append(tuple(sorted(group)))
    return tuple(result)


def options(a, b, aid, bid):
    if a == b:
        return (), 'identical_program'
    shared = set(aid) & set(bid)
    aa = [i for i in aid if i in shared]
    bb = [i for i in bid if i in shared]
    if len(shared) < 2:
        return (), 'no_shared_anchors'
    if aa != bb:
        return (), 'inverted_shared_order'
    groups = []
    for fn in (independent_groups, gate_groups):
        groups.append([{ids[j] for j in group} for program, ids in ((a, aid), (b, bid)) for group in fn(program)])
    result = []
    apos, bpos = {x:i for i,x in enumerate(aid)}, {x:i for i,x in enumerate(bid)}
    for identity in aa:
        x, u = apos[identity]+1, bpos[identity]+1
        for size in (2,4,8,16,32):
            y, v = x+size, u+size
            if y >= len(aid) or v >= len(bid) or aid[y] != bid[v]:
                continue
            assembled = list(aid[:x])+list(bid[u:v])+list(aid[y:])
            if len(assembled) != len(set(assembled)):
                continue
            changed = sum(a[x+j] != b[u+j] for j in range(size))
            if not changed:
                continue
            segment = set(aid[x:y]) | set(bid[u:v])
            closed = [all(not segment.intersection(g) or g.issubset(segment) for g in gs) for gs in groups]
            result.append((x,y,u,v,changed,*closed))
    return tuple(result), 'common_pool' if result else 'no_differing_segment'
