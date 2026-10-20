"""V12Y static crossover opportunities. No organism inference or genome editing."""
from functools import lru_cache
import hashlib
import json
import random
from .linkage_restart_operator import dependencies

LENGTHS = (2, 4, 8, 16, 32)
RULES = ('transitive', 'gate', 'unlinked', 'sham_transitive', 'sham_gate')


def seed(*parts):
    return int.from_bytes(hashlib.sha256(json.dumps(parts).encode()).digest()[:8], 'big')


@lru_cache(maxsize=4096)
def gate_groups(program):
    definitions = [set() for _ in range(64)]
    groups = []
    for i, row in enumerate(program):
        op, dst, *_, gate = row
        if op == 13:
            groups.append(tuple(sorted({i} | (definitions[gate] if gate != 64 else set()))))
        elif gate == 64:
            definitions[dst] = {i}
        else:
            definitions[dst].add(i)
    return tuple(groups)


def options(a, b, aid, bid):
    """x,y,u,v,changed,full_closed,gate_closed; same pool for all policies."""
    assert len(a) == len(aid) == len(set(aid))
    assert len(b) == len(bid) == len(set(bid))
    if a == b:
        return (), 'identical_program'
    positions = {identity: j for j, identity in enumerate(bid)}
    shared = [(i, positions[identity]) for i, identity in enumerate(aid) if identity in positions]
    if len(shared) < 2:
        return (), 'no_shared_anchors'
    if [j for _, j in shared] != sorted(j for _, j in shared):
        return (), 'inverted_shared_order'
    aligned = dict(shared)
    bits = {identity: 1 << i for i, identity in enumerate(dict.fromkeys(aid + bid))}
    abits, bbits = [bits[x] for x in aid], [bits[x] for x in bid]
    masks = []
    for fn in (dependencies, gate_groups):
        masks.append([sum(seq[i] for i in group) for program, seq in ((a, abits), (b, bbits)) for group in fn(program)])
    out = []
    for left, dleft in shared:
        x, u = left + 1, dleft + 1
        for length in LENGTHS:
            y, v = x + length, u + length
            if aligned.get(y) != v:
                continue
            changed = sum(ar != br for ar, br in zip(a[x:y], b[u:v]))
            if not changed:
                continue
            child_ids = aid[:x] + bid[u:v] + aid[y:]
            if len(child_ids) != len(set(child_ids)):
                continue
            segment = 0
            for bit in abits[x:y] + bbits[u:v]:
                segment |= bit
            closed = [all(not (group & segment) or (group & segment) == group for group in gs) for gs in masks]
            assert not closed[0] or closed[1]
            out.append((x, y, u, v, changed, *closed))
    return tuple(out), 'common_pool' if out else 'no_differing_segment'


def virtual(pool, cap, ticket_seed):
    """Shared length, shuffle and ticket; exact pre-mutation expectations also saved."""
    opts = [v for v in pool if v[1] - v[0] <= cap]
    lengths = sorted({v[1] - v[0] for v in opts})
    if not lengths:
        return {rule: dict(accepted=False, multi=False, expected_multi=0., any_multi=False,
                           length=None, selected=None) for rule in RULES}
    rng = random.Random(ticket_seed)
    length = rng.choice(lengths)
    common = [v for v in opts if v[1] - v[0] == length]
    order = list(range(len(common)))
    rng.shuffle(order)
    ticket = rng.random()
    full, gate = [v for v in common if v[5]], [v for v in common if v[6]]
    pools = dict(transitive=full, gate=gate, unlinked=common,
                 sham_transitive=[common[i] for i in order[:len(full)]],
                 sham_gate=[common[i] for i in order[:len(gate)]])
    answer = {}
    for rule, chosen_pool in pools.items():
        chosen = chosen_pool[min(int(ticket * len(chosen_pool)), len(chosen_pool)-1)] if chosen_pool else None
        expectation = 0.
        possible = False
        for size in lengths:
            cc = [v for v in opts if v[1]-v[0] == size]
            allowed = cc if rule == 'unlinked' else [v for v in cc if v[5 if 'transitive' in rule else 6]]
            if rule.startswith('sham'):
                probability = sum(v[4] >= 2 for v in cc)/len(cc) if allowed else 0.
                possible |= bool(allowed) and any(v[4] >= 2 for v in cc)
            else:
                probability = sum(v[4] >= 2 for v in allowed)/len(allowed) if allowed else 0.
                possible |= any(v[4] >= 2 for v in allowed)
            expectation += probability/len(lengths)
        answer[rule] = dict(accepted=chosen is not None, multi=chosen is not None and chosen[4] >= 2,
                            expected_multi=expectation, any_multi=possible, length=length,
                            selected=list(chosen) if chosen is not None else None)
    assert answer['transitive']['accepted'] == answer['sham_transitive']['accepted']
    assert answer['gate']['accepted'] == answer['sham_gate']['accepted']
    return answer
