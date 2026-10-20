"""Amendment A1: ordinary perfect rasters 11x11; other construction unchanged.

Copied from the sealed deep_campaign_data and family_evolution_data ordinary
constructor. Their original versions remain untouched.
"""
from cellular_maze_lab import neighbors
from .datasets import make_case, manifest, seed_for
from .evaluator import Maze, Oracle, distances
from .family_evolution_data import AccessData
from .foundation_data import layout_hash, transform_maze
from .deep_campaign_perfect11 import wilson_case
from .selectivity_data import SPECS


def cases_from_manifest(rows):
    cases = {}
    for r in rows:
        m = Maze(bytes.fromhex(r['cells_hex']), r['w'], r['h'], r['start'],
                 r['goal'], r['family'], r['seed'], r['split'], r['case_id'])
        assert m.digest == r['sha256']
        o = Oracle.build(m)
        assert len(o.path) == r['oracle_length']
        o._from_start = distances(m, m.start)
        cases[m.case_id] = o
    return cases


def ordinary_training(d, g):
    """Six new bases, all poses excluded, one pose queried per base."""
    queried = []
    for family in ('perfect', 'random', 'disconnected'):
        for index in range(2):
            split = f'train/{g}/ordinary/{family}'
            for salt in range(4000):
                o = (wilson_case(d.seed, split, index, salt) if family == 'perfect'
                     else make_case(d.seed, split, index, salt, 9, family))
                if family == 'disconnected' and any(
                    not any(o.maze.cells[q] for q in neighbors(p, 9, 9))
                    for p in (o.maze.start, o.maze.goal)
                ):
                    continue
                poses = [transform_maze(o.maze, p) for p in range(8)]
                orbit = {layout_hash(m) for m in poses}
                if orbit & d.layouts:
                    continue
                for pose, m in enumerate(poses):
                    q = Oracle.build(m)
                    assert bool(q.path) == (family != 'disconnected')
                    q._from_start = distances(m, m.start)
                    d.cache[m.case_id] = q
                    d.metadata[m.case_id] = dict(
                        family='ordinary_' + family, base=o.maze.case_id,
                        template=o.maze.case_id, index=index, pose=pose,
                        prefix=-1, graph=family, side=0, path=q.path)
                    if pose == (g // 4) % 8:
                        queried.append(m.case_id)
                d.layouts.update(orbit)
                break
            else:
                raise RuntimeError('Ordinary training construction exhausted')
    return queried


def batch(seed, kind, generation, previous, frontiers):
    d = AccessData(seed_for(seed, kind, 0, generation), previous)
    split = f'{kind}/{generation}'
    if kind == 'assessment':
        for length, shape, stress in SPECS:
            d.context(split, len(d.contexts), length, shape, (0, 1, 2, 4, 8), stress)
        ordinary(d, split)
        ids = [
            c for c, m in d.metadata.items()
            if (m['family'] == 'paired' and m['pose'] % 2 == 0)
            or (m['family'] == 'corridor' and m['pose'] == 0)
            or (m['family'] == 'disconnected' and m['prefix'] == 0 and m['pose'] == 0)
            or (m['family'].startswith('ordinary_') and m['pose'] in (0, 4))
        ]
        queries = {str(i): ids for i in range(3)}
    elif kind == 'train':
        queries = {}
        levels = (0, 1, 2, 4, 8)
        # Common contexts and poses; only the requested prefix may differ by island.
        easy = {levels[max(0, levels.index(f) - 1)] for f in frontiers}
        target = {levels[min(4, levels.index(f) + (generation % 7 == 6))]
                  for f in frontiers}
        length, shape, _ = SPECS[generation % 4]
        d.context(split, 0, length, shape, tuple(sorted(easy)))
        stress = generation % 5 == 4
        d.context(split, 1, (4, 6) if stress else length,
                  'straight' if stress else shape, tuple(sorted(target)), stress)
        graph = ('two_junction', 'cycle')[(generation // 5) % 3 == 2] if stress else 'fork'
        pose = generation % 8
        extra = ordinary_training(d, generation) if generation % 4 == 0 else []
        for i, f in enumerate(frontiers):
            p0 = levels[max(0, levels.index(f) - 1)]
            p1 = levels[min(4, levels.index(f) + (generation % 7 == 6))]
            queries[str(i)] = [
                c for c, m in d.metadata.items() if not m['family'].startswith('ordinary_')
                and m['pose'] == pose and
                ((m['index'] == 0 and m['prefix'] == p0) or
                 (m['index'] == 1 and m['prefix'] == p1 and m['graph'] == graph))
            ] + extra
            assert len(queries[str(i)]) == 12 + len(extra)
    else:
        raise ValueError(kind)
    return dict(kind=kind, generation=generation, mazes=manifest(d.cache.values()),
                metadata=d.metadata, contexts=d.contexts, queries=queries,
                new_layouts=sorted(d.layouts - previous))


def ordinary(d,split):
    """Same assessment counts and sampling; perfect rasters alone are 11x11."""
    from .datasets import make_case
    from .foundation_data import layout_hash,transform_maze
    from .evaluator import Oracle,distances
    for family,count in (('perfect',24),('random',24),('disconnected',16)):
        for index in range(count):
            for salt in range(4000):
                if family=='perfect':
                    from .deep_campaign_perfect11 import wilson_case
                    o=wilson_case(d.seed,split+'/ordinary/'+family,0,index*4000+salt)
                else:o=make_case(d.seed,split+'/ordinary/'+family,0,index*4000+salt,9,family)
                if family=='disconnected' and (not any(o.maze.cells[q] for q in neighbors(o.maze.start,9,9)) or not any(o.maze.cells[q] for q in neighbors(o.maze.goal,9,9))):
                    d.rejections+=1;continue
                orbit={layout_hash(transform_maze(o.maze,pose)) for pose in range(8)}
                if orbit&d.layouts:d.rejections+=1;continue
                for pose in range(8):
                    m=transform_maze(o.maze,pose);q=Oracle.build(m);q._from_start=distances(m,m.start)
                    assert bool(q.path)==(family!='disconnected')
                    d.cache[m.case_id]=q;d.metadata[m.case_id]=dict(family='ordinary_'+family,
                        base=o.maze.case_id,template=o.maze.case_id,index=index,pose=pose,
                        path=q.path,prefix=-1,stress=False,graph=family,side=0)
                d.layouts.update(orbit);break
            else:raise RuntimeError('No unseen ordinary case')

