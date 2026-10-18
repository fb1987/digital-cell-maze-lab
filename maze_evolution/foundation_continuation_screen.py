"""Preregistered V12D screen, with paired accuracy and same-replicate retention."""
from collections import defaultdict


def level_metrics(rows):
    result = {}
    for level in range(4):
        subset = [r for r in rows if f'/level{level}/' in r['case']]
        groups = defaultdict(list)
        for row in subset:
            group = row['case'].rsplit('/d4-', 1)[0].rsplit('/', 1)[0]
            groups[group].append(row)
        assert len(subset) == 96 and len(groups) == 6
        assert all(len(values) == 16 for values in groups.values())
        result[str(level)] = dict(optimal=sum(r['optimal'] for r in subset),
            pairs=sum(r['pair_optimal'] for r in subset) // 2,
            groups_any=sum(any(r['pair_optimal'] for r in values) for values in groups.values()),
            groups_all=sum(all(r['pair_optimal'] for r in values) for values in groups.values()))
    return result


def replicate_screen(current, checkpoint, resample):
    paired = lambda m: sum(m[str(level)]['pairs'] for level in (1, 2, 3))
    improvement = paired(current) > max(paired(checkpoint), paired(resample))
    retention = current['0']['pairs'] >= 44  # ceil(90% of 48 adjacent pairs)
    symmetry = current['1']['groups_all'] > max(checkpoint['1']['groups_all'], resample['1']['groups_all'])
    distance = (current['2']['pairs'] > max(checkpoint['2']['pairs'], resample['2']['pairs'])
                and current['2']['groups_any'] >= 2)
    return dict(passes=bool(improvement and retention and (symmetry or distance)),
        paired_improvement=improvement, adjacent_retention=retention,
        all_pose_improvement=symmetry, distance_transfer=distance,
        nonadjacent_pairs={k: paired(v) for k, v in
            (('current', current), ('checkpoint', checkpoint), ('resample', resample))},
        adjacent_pairs=current['0']['pairs'])
