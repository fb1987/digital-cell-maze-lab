import random,unittest
from unittest.mock import patch
from maze_evolution.output_access_genome_m31 import vary,Genome,ARMS,ScopeRNG
from maze_evolution.connected_evolution_genome import ordinary
from maze_evolution.output_access_m31 import make_sources,make_pool
from maze_evolution.output_access_metrics_m31 import nominate_assessed
from maze_evolution.transfer_retention_metrics import gate
from maze_evolution.deep_campaign_store import packed,unpacked,hashed
from maze_evolution.referenced_campaign_store import compact

class OutputAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.sources=make_sources()
    def test_ordinary_matches_unmodified_operator_and_replay(self):
        for p in self.sources['parents'].values():
            g=Genome.from_dict(p['model']['genome'])
            for seed in range(60):
                actual,e=vary(g,seed,'ordinary');old,event=ordinary(g,random.Random(seed))
                self.assertEqual(actual,old);self.assertTrue(all(e[k]==v for k,v in event.items()));self.assertEqual((actual,e),vary(g,seed,'ordinary'))
    def test_targeted_scope_and_all_bounds(self):
        modes=set();kinds=set()
        for p in self.sources['parents'].values():
            g=Genome.from_dict(p['model']['genome'])
            for seed in range(160):
                for arm,scope in (('output',2),('C6',6)):
                    child,event=vary(g,seed,arm);modes.add(event['mode']);kinds.add(event['kind']);self.assertEqual(event['block'],scope)
                    self.assertLessEqual(child.instructions,256);self.assertLessEqual(len(child.body.blocks[scope]),31)
                    self.assertEqual(child.initialization,g.initialization)
                    self.assertTrue(all((g.body.blocks[k],g.body.ports[k])==(child.body.blocks[k],child.body.ports[k]) for k in range(10) if k!=scope))
                    self.assertEqual((child,event),vary(g,seed,arm))
        self.assertEqual(modes,set(range(7)));self.assertIn('ports',kinds);self.assertIn('delete',kinds);self.assertIn('copy_block',kinds)
    def test_target_matches_ordinary_when_natural_writer_matches(self):
        g=Genome.from_dict(self.sources['parents']['recipient']['model']['genome'])
        for seed in range(120):
            old,event=ordinary(g,random.Random(seed))
            if event['block'] in (2,6):
                new,e=vary(g,seed,'output' if event['block']==2 else 'C6');self.assertEqual(new,old)
    def test_pool_is_fixed_and_equal_opportunities(self):
        p=make_pool(self.sources,4);self.assertEqual(p,make_pool(self.sources,4))
        for source in p['parents']:
            for arm in ARMS:self.assertEqual(sum(c['source']==source and c['arm']==arm for c in p['conditions']),4)
        self.assertFalse(set(p['control_ids'])&set(p['historical_references']))
        self.assertEqual(len(p['historical_references']),208)
    def test_gate_nonvacuity_empty_output_and_losses(self):
        empty=dict(pairs=set(),corridors=set(),ordinary_bases=set(),correct_no_path=set(),false=set())
        parent=dict(empty,corridors={'old'},correct_no_path={'nopath'})
        a0=dict(empty,correct_no_path={'nopath'})
        self.assertFalse(gate(empty,[parent],a0,True)['passes'])
        self.assertFalse(gate(parent,[parent],empty,True)['passes'])
        self.assertTrue(gate(parent,[parent],a0,True)['passes'])
        self.assertFalse(gate(dict(parent,false={'reachable'}),[parent],a0,True)['passes'])
        self.assertFalse(gate(parent,[parent],a0,False)['passes'])
    def test_nomination_primary_cannot_be_replaced_by_exploration(self):
        pool=make_pool(self.sources,2);details=[]
        for c in pool['conditions']:
            high=c['draw']==1
            details.append(dict(c,endpoint=dict(gate={'passes':not high},raw_novel_complete8=0),controlled_route_pairs=10 if high else 0,
                retention_floor=.5 if high else 1.,correct_reachable=10 if high else 5,correct_inputs=12,work=100))
        choices,_=nominate_assessed(pool,dict(conditions=details))
        for c in choices['choices']:
            if c['role']=='INTEGRATED':self.assertEqual(c['development']['draw'],0)
            if c['role']=='OUTPUT_EXPLORATORY':self.assertEqual(c['development']['draw'],1)
        self.assertEqual(len(choices['choices']),27)
    def test_spec_key_survives_journal_compression(self):
        value=[dict(model=self.sources['parents']['recipient']['model'],queries=['old'],aliases=['fixture'])]
        self.assertEqual(hashed(packed(unpacked(compact(value)))),hashed(packed(value)))

if __name__=='__main__':unittest.main()
