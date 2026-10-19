"""Preregistered V12E completed-pair transfer and within-model retention screen."""
from math import ceil
from collections import defaultdict


def level_metrics(rows):
    result = {}
    for level in range(5):
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


def replicate_screen(treatment, current, checkpoint, resample):
    def challenging(m):
        return sum(m[str(level)]['pairs'] for level in (2, 3))
    gain = challenging(treatment) > max(challenging(m) for m in (current, checkpoint, resample))
    groups = sum(treatment[str(level)]['groups_any'] for level in (2, 3)) >= 2
    all_pose = sum(treatment[str(level)]['groups_all'] for level in (2, 3)) >= 1
    adjacent = treatment['0']['pairs'] >= 44
    two_edge_threshold = ceil(.9 * checkpoint['1']['pairs'])
    two_edge = treatment['1']['pairs'] >= two_edge_threshold
    return dict(challenge_gain=gain, two_independent_challenge_groups=groups,
                all_pose_challenge_group=all_pose, adjacent_retention=adjacent,
                two_edge_retention=two_edge, two_edge_threshold=two_edge_threshold,
                passes=all((gain, groups, all_pose, adjacent, two_edge)))
