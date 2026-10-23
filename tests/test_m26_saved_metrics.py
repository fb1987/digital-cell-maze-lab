"""Synthetic saved rows only: no environments, organism executions or selection."""
import unittest
from tools.m26_saved_metrics import (Panel, append_reason, cohort_flags, compare,
                                     genome_info, novelty, union_profiles)


def panel_and_rows():
    meta = {}
    for base, length in [('short', 7), ('target', 8), ('long', 16)]:
        for pose in (0, 4):
            meta[f'{base}/{pose}'] = dict(family='ordinary_random', base=base, pose=pose,
                                         path=list(range(length + 1)))
    meta['disc'] = dict(family='ordinary_disconnected')
    rows = [dict(case=c, optimal=False, no_path=False, reachable=c != 'disc', status='emitted') for c in meta]
    return Panel(meta, list(meta), [c for c in meta if c != 'disc'], []), rows


class SavedMetricsTests(unittest.TestCase):
    def test_two_poses_and_length_edges(self):
        p, rows = panel_and_rows()
        for r in rows:
            r['optimal'] = r['case'] in ('short/0', 'short/4', 'target/0', 'long/0', 'long/4')
        c = p.profile(rows)
        self.assertEqual(c['ordinary'], {'short', 'long'})
        self.assertEqual(c['ordinary8'], {'long'})
        self.assertEqual(c['ordinary16'], {'long'})
        self.assertEqual(c['single8'], {'target/0', 'long/0', 'long/4'})

    def test_collective_union_is_stronger_than_complete_reference_union(self):
        p, rows = panel_and_rows()
        profiles = []
        for pose in (0, 4):
            rs = [dict(r, optimal=r['case'] == f'target/{pose}') for r in rows]
            profiles.append(p.profile(rs))
        child = p.profile([dict(r, optimal=r['case'].startswith('target/')) for r in rows])
        nov = novelty(child, union_profiles(profiles), p)
        self.assertEqual(nov['complete'], {'target'})
        self.assertFalse(nov['single'])
        self.assertFalse(nov['beyond_collective'])

    def test_new_complete_has_new_pose_when_references_fail_it(self):
        p, rows = panel_and_rows()
        child = p.profile([dict(r, optimal=r['case'].startswith('target/')) for r in rows])
        nov = novelty(child, p.profile(rows), p)
        self.assertEqual(nov['beyond_collective'], {'target'})
        self.assertEqual(len(nov['single']), 2)

    def test_comparator_missing_not_failure(self):
        p, rows = panel_and_rows()
        self.assertIsNone(compare(p.profile(rows), None))

    def test_no_path_gate_not_vacuous_and_false_claims_separate(self):
        p, rows = panel_and_rows()
        empty = p.profile(rows)
        self.assertFalse(compare(empty, empty)['domain90_and_disconnection90_zero_false'])
        parent = p.profile([dict(r, no_path=r['case'] == 'disc', status='no_path' if r['case'] == 'disc' else 'emitted') for r in rows])
        self.assertTrue(compare(parent, parent)['domain90_and_disconnection90_zero_false'])
        false = p.profile([dict(r, no_path=r['case'] == 'disc', status='no_path') for r in rows])
        self.assertFalse(compare(false, parent)['domain90_and_disconnection90_zero_false'])
        self.assertEqual(len(false['no_path']), 1)
        self.assertEqual(len(false['false']), 6)

    def test_total_instructions_count_writer_dispatch(self):
        info = genome_info({'body': {'blocks': [[0] * 10, [], [0] * 2]}})
        self.assertEqual(info['instructions'], 14)
        self.assertTrue(info['append_any_writer_eligible'])
        self.assertEqual(append_reason(126, 10), 'total128_only')
        self.assertEqual(append_reason(125, 28), 'admitted')
        self.assertEqual(append_reason(125, 29), 'writer31_only')
        self.assertEqual(append_reason(126, 29), 'both_bounds')

    def test_censored_noop_and_positive_flags_distinct(self):
        self.assertEqual(cohort_flags(dict(first=None)), {'training_censored': True})
        record = dict(noop=True, first=dict(counts={'ordinary8': 1, 'ordinary16': 0, 'false': 0},
                      novel_complete8=0, novel_single8=0, novel_complete8_beyond_collective=0,
                      parent=None, root=None))
        flags = cohort_flags(record)
        self.assertTrue(flags['ordinary8'])
        self.assertFalse(flags['genotype_changed'])
        self.assertFalse(flags['novel_complete8'])
        self.assertFalse(flags['parent_comparison_available'])

    def test_repeated_fixed_rows_do_not_change_unit_counts(self):
        p, rows = panel_and_rows()
        rows = [dict(r, optimal=r['case'].startswith('target/')) for r in rows]
        a, b = p.profile(rows), p.profile(rows)
        self.assertEqual(a['ordinary8'] | b['ordinary8'], {'target'})
        with self.assertRaises(AssertionError):
            p.profile(rows + rows)


if __name__ == '__main__':
    unittest.main()
