"""Read-only topology inventory after the deep campaign's generator failure.

No endpoints, maze test cases, genome inference or confirmation corpus are made.
Enumerates the finite 4x4 room-grid tree support and checks layout hashes against
the journal. Output is a new diagnostic packet; never changes the campaign.
"""
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import sqlite3
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from maze_evolution.deep_campaign import DEFAULT_RUN, ROOT, check_setup


def main():
    started = time.monotonic()
    check_setup()
    db = sqlite3.connect(f'file:{DEFAULT_RUN / "campaign.sqlite"}?mode=ro', uri=True)
    previous = {r[0] for r in db.execute('SELECT hash FROM layouts')}
    db.close()
    edges = [(p, q) for p in range(16) for q in range(p + 1, 16)
             if abs(p % 4 - q % 4) + abs(p // 4 - q // 4) == 1]
    lookup = {e: i for i, e in enumerate(edges)}
    transforms = []
    for pose in range(8):
        points = []
        for p in range(16):
            x, y = p % 4, p // 4
            if pose >= 4:
                x = 3 - x
            for _ in range(pose % 4):
                x, y = 3 - y, x
            points.append(4 * y + x)
        transforms.append([lookup[tuple(sorted((points[a], points[b])))]
                           for a, b in edges])
    pixel = lambda p: (2 * (p // 4) + 1) * 9 + 2 * (p % 4) + 1
    base = bytearray(81)
    for p in range(16):
        base[pixel(p)] = 1
    midpoints = [(pixel(a) + pixel(b)) // 2 for a, b in edges]
    orbits = set()
    trees = blocked = available = 0
    available_orbit_hashes = []
    unseen_hashes = set()
    for choice in itertools.combinations(range(24), 15):
        parents = list(range(16))
        for edge in choice:
            a, b = edges[edge]
            while parents[a] != a:
                a = parents[a]
            while parents[b] != b:
                b = parents[b]
            if a == b:
                break
            parents[a] = b
        else:
            trees += 1
            masks = {sum(1 << mapping[e] for e in choice)
                     for mapping in transforms}
            canonical = min(masks)
            if canonical in orbits:
                continue
            orbits.add(canonical)
            hashes = set()
            for mask in masks:
                cells = bytearray(base)
                for edge, p in enumerate(midpoints):
                    if mask & (1 << edge):
                        cells[p] = 1
                hashes.add(hashlib.sha256(b'9,9:' + bytes(cells)).hexdigest())
            unseen_hashes.update(hashes - previous)
            if hashes & previous:
                blocked += 1
            else:
                available += 1
                available_orbit_hashes.append(sorted(hashes))
    assert trees == 100352  # Also verified by exact Matrix-Tree determinant.
    assert blocked + available == len(orbits)
    out = ROOT / 'results/deep_campaign_run/failure_08268'
    packet = dict(
        prior_layout_count=len(previous), oriented_spanning_trees=trees,
        dihedral_orbits=len(orbits), blocked_orbits=blocked,
        eligible_orbits_at_stop=available,
        remaining_training_perfect_bases=2 * len(range(8268, 10000, 4)),
        remaining_assessment_perfect_bases=4 * 24,
        inventory_layouts_outside_journal=len(unseen_hashes),
        wall_seconds=time.monotonic() - started,
        candidate_inference_calls=0, confirmation_cases_generated=0,
        journal_mutations=0,
        method='Exhaustive 15-edge acyclic subsets of the 24-edge 4x4 grid; '
               'connectedness follows from acyclicity plus 16 vertices/15 edges. '
               'All eight D4 transforms checked against endpoint-free layout hashes.')
    with (out / 'topology_inventory.json').open('x') as f:
        json.dump(packet, f, indent=2)
        f.write('\n')
    with (out / 'topology_inventory_hashes.json.gz').open('xb') as f:
        f.write(gzip.compress(json.dumps(dict(
            eligible_orbits=available_orbit_hashes,
            inventory_hashes_outside_journal=sorted(unseen_hashes),
            note='Topology-only diagnostics; preserve these hashes with future '
                 'exclusions rather than using this inventory as a confirmation pool.'
        ), sort_keys=True).encode(), mtime=0))
    print(json.dumps(packet, indent=2))


if __name__ == '__main__':
    main()
