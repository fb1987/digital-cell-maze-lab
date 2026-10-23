"""M27 endpoint edge cases and observer durability; no candidate inference."""
import gzip
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from maze_evolution.transfer_retention_metrics import gate,endpoint,compare
from maze_evolution.transfer_retention_data import component_cycles,observed,observed_hashes
from maze_evolution.copy_specialization import tasks


def caps(**changes):
    value={k:set() for k in ('pairs','corridors','ordinary_bases','correct_no_path','success','false')}
    value.update(changes)
    return value


def metadata():
    return {f'{b}/{p}':dict(base=b,family=family,path=list(range(length+1)))
            for b,family,length in [('a','ordinary_perfect',8),('b','ordinary_random',16),
                                    ('c','ordinary_perfect',12),('d','ordinary_random',24),('short','ordinary_perfect',7)]
            for p in (0,4)}


class TransferTests(unittest.TestCase):
    def test_empty_no_path_reference_cannot_pass(self):
        self.assertFalse(gate(caps(),[],caps(),1)['passes'])

    def test_exact90percent_retention_is_accepted_but_below_fails(self):
        old=caps(ordinary_bases=set(range(10)),correct_no_path={'d'})
        child=caps(ordinary_bases=set(range(9)),correct_no_path={'d'})
        self.assertTrue(gate(child,[old],old,1)['passes'])
        child['ordinary_bases'].remove(8)
        self.assertFalse(gate(child,[old],old,1)['passes'])

    def test_parent_root_and_entry_all_constrain_retention(self):
        a0=caps(correct_no_path={'n'})
        child=caps(correct_no_path={'n'})
        entry=caps(corridors={'old'},correct_no_path={'n'})
        self.assertFalse(gate(child,[a0,entry],a0,1)['passes'])

    def test_false_reachable_no_path_or_no_mutation_blocks(self):
        a0=caps(correct_no_path={'n'})
        self.assertFalse(gate(a0,[a0],a0,0)['passes'])
        self.assertFalse(gate(caps(correct_no_path={'n'},false={'reachable'}),[a0],a0,1)['passes'])

    def test_novel_complete_combination_can_be_known_as_collective_poses(self):
        child=caps(ordinary_bases={'a'},correct_no_path={'n'},success={'a/0','a/4','n'})
        portfolio=caps(success={'a/0','a/4'})
        result=endpoint(child,[],portfolio,caps(correct_no_path={'n'}),metadata(),1)
        self.assertEqual(result['raw_novel_complete8'],1)
        self.assertEqual(result['raw_novel_complete8_beyond_collective'],0)

    def test_actual_parent_success_is_excluded_from_new_bases(self):
        child=caps(ordinary_bases={'a'},correct_no_path={'n'})
        result=endpoint(child,[child],caps(),caps(correct_no_path={'n'}),metadata(),1)
        self.assertEqual(result['raw_novel_complete8'],0)

    def test_broad_transfer_requires_four_bases_both_families_and16plus(self):
        child=caps(ordinary_bases={'a','b','c','d','short'},correct_no_path={'n'})
        result=endpoint(child,[],caps(),caps(correct_no_path={'n'}),metadata(),1)
        self.assertEqual(result['primary_score'],4)
        self.assertTrue(result['broad_transfer'])
        child['ordinary_bases'].remove('d')
        self.assertFalse(endpoint(child,[],caps(),caps(correct_no_path={'n'}),metadata(),1)['broad_transfer'])

    def test_raw_gain_remains_visible_when_gate_fails(self):
        result=endpoint(caps(ordinary_bases={'b'}),[],caps(),caps(correct_no_path={'n'}),metadata(),1)
        self.assertEqual(result['raw_novel_complete8'],1)
        self.assertEqual(result['primary_score'],0)

    def test_physical_sharing_preserves_all_alias_queries(self):
        items=[dict(id=i,model={'x':1}) for i in ('parent','child')]
        spec=tasks(items,['a','b'])
        self.assertEqual(len(spec),1);self.assertEqual(len(spec[0]),1)
        self.assertEqual(spec[0][0]['aliases'],['parent','child'])
        self.assertEqual(spec[0][0]['queries'],['a','b'])

    def test_cycle_count_distinguishes_path_and_cycle(self):
        self.assertEqual(component_cycles(SimpleNamespace(cells=bytes([1,1,1,1]),w=4,start=0)),0)
        self.assertEqual(component_cycles(SimpleNamespace(cells=bytes([1,1,1,1]),w=2,start=0)),1)

    def test_failed_builder_preserves_observations_and_restores_globals(self):
        from maze_evolution import family_evolution_data,reboot_data
        from maze_evolution.evaluator import Maze
        from maze_evolution.foundation_data import layout_hash
        root=Path(__file__).resolve().parents[1]
        with gzip.open(root/'results/restoration_assay/discarded_corpus_fixture.json.gz','rt') as f:r=json.load(f)['mazes'][0]
        # Existing excluded input only; never a newly generated test maze.
        m=Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'])
        old_hash,old_make=family_evolution_data.layout_hash,reboot_data.make_case
        def fail(seed,previous):
            family_evolution_data.layout_hash(m)
            raise RuntimeError('deliberate fixture failure')
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'observed.jsonl'
            with self.assertRaisesRegex(RuntimeError,'deliberate'):
                observed(fail,0,set(),path)
            self.assertEqual(observed_hashes(path),{layout_hash(m)})
        self.assertIs(family_evolution_data.layout_hash,old_hash)
        self.assertIs(reboot_data.make_case,old_make)


if __name__=='__main__':unittest.main()
