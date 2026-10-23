import random
import unittest
import numpy as np
from maze_evolution.connected_genome import Genome
from maze_evolution.spare_genome import Genome as Body
from maze_evolution.regulatory import Gene
from maze_evolution.connected_runtime import Organism
from maze_evolution.connected_trace import respond
from maze_evolution.state_isolation_runtime import respond_pair,writer,compile_pair
from maze_evolution.state_dependency import dependencies,sharing,cross_edges,divergence
from maze_evolution.foundation_study import read_compressed
from maze_evolution.deep_campaign_data import cases_from_manifest
from maze_evolution.foundation_calibration import ROOT
from maze_evolution.exposure_selection import record
from maze_evolution.runtime import Limits


def constant(value,stop=False):
    blocks=tuple((Gene(1,12,value if k==2 else int(k==7 and stop),0,0,0,64),) for k in range(8))+((),())
    return dict(representation='connected',genome=Genome(Body(blocks,(tuple(range(10)),)*10)).to_dict())


class IsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d=read_compressed(ROOT/'results/transfer_retention_m27/discarded_fixture.json.gz')
        cls.cases=list(cases_from_manifest(d['mazes']).values());cls.o=cls.cases[0];cls.m=cls.o.maze

    def test_independent_stop_latches_and_cost(self):
        a,b=constant(1,True),constant(0);rr,h,c=respond_pair(a,b,self.m)
        for k,model in enumerate((a,b)):
            r,n,_=respond(model,self.m);self.assertEqual(record(rr[k],self.o),record(r,self.o))
            self.assertTrue(np.array_equal(h[:len(n),k*10:k*10+10],n))
            self.assertTrue(np.all(h[len(n)-1:,k*10:k*10+10]==n[-1]))
        self.assertEqual(rr[0].steps,1);self.assertGreater(rr[1].steps,rr[0].steps)
        self.assertEqual(c['counted_work'],sum(r.neighbor_reads+r.dispatches for r in rr));self.assertEqual(c['state_channels'],20)

    def test_random_native_equivalence_and_budgets(self):
        from maze_evolution.dormant_evolution_genome import random_genome
        rng=random.Random(29)
        for _ in range(3):
            a,b=[dict(representation='connected',genome=random_genome(rng).to_dict()) for _ in range(2)]
            for limits in (Limits(256,4096,32768),Limits(3,1,10),Limits(8,1,1)):
                rr,h,c=respond_pair(a,b,self.m,limits=limits)
                for k,model in enumerate((a,b)):
                    r=Organism(Genome.from_dict(model['genome']),limits).react(self.m.cells,self.m.w,self.m.h,self.m.start,self.m.goal)
                    self.assertEqual(record(rr[k],self.o),record(r,self.o))

    def test_writer_matches_every_completed_native_tick(self):
        from maze_evolution.dormant_evolution_genome import random_genome
        g=dict(representation='connected',genome=random_genome(random.Random(292)).to_dict());r,h,_=respond(g,self.m)
        for t in range(min(8,len(h)-1)):
            for k in range(10):
                values,reads,dispatches=writer(g,self.m,h[t],k)
                self.assertTrue(np.array_equal(values,h[t+1,k]));self.assertGreaterEqual(reads+dispatches,0)

    def test_cross_edge_has_real_causal_effect_on_receiver_only(self):
        a,b=constant(0),constant(1)
        ga=Genome.from_dict(a['genome']);blocks=list(ga.body.blocks);blocks[2]=(Gene(0,12,2,0,0,0,64),)
        a=dict(representation='connected',genome=Genome(Body(tuple(blocks),ga.body.ports)).to_dict())
        pure,h,_=respond_pair(a,b,self.m);coupled,hc,_=respond_pair(a,b,self.m,edge=(0,2,2))
        self.assertEqual(sum(pure[0].mask),0);self.assertGreater(sum(coupled[0].mask),0)
        self.assertEqual(record(pure[1],self.o),record(coupled[1],self.o))
        _,hb,_=respond(b,self.m);self.assertTrue(np.array_equal(hc[:len(hb),10:],hb))

    def test_cross_bank_reads_use_previous_tick(self):
        # Both banks read C2 from the OTHER bank. Initial C2 is zero in both;
        # no same-tick leakage of a constant written by one bank into the other.
        a,b=constant(0),constant(1)
        ga=Genome.from_dict(a['genome']);bs=list(ga.body.blocks);bs[2]=(Gene(0,12,2,0,0,0,64),)
        a=dict(representation='connected',genome=Genome(Body(tuple(bs),ga.body.ports)).to_dict())
        rr,h,_=respond_pair(a,b,self.m,edge=(0,2,2),limits=Limits(2,4096,32768))
        self.assertTrue(np.all(h[1,2]==0));self.assertGreater(np.count_nonzero(h[2,2]),0)

    def test_structural_sharing_requires_closed_dependencies(self):
        a,b=constant(0),constant(1);d=sharing(a,b)
        self.assertNotIn(2,d['closed_shareable_channels']);self.assertEqual(d['conservative_copy_width'],11)
        for model in (a,b):
            g=Genome.from_dict(model['genome']);bs=list(g.body.blocks);bs[0]=(Gene(0,12,2,0,0,0,64),)
            if model is a:aa=dict(representation='connected',genome=Genome(Body(tuple(bs),g.body.ports)).to_dict())
            else:bb=dict(representation='connected',genome=Genome(Body(tuple(bs),g.body.ports)).to_dict())
        self.assertNotIn(0,sharing(aa,bb)['closed_shareable_channels'])

    def test_cones_and_slot_mapping(self):
        a=constant(0);g=Genome.from_dict(a['genome']);bs=list(g.body.blocks)
        bs[2]=(Gene(0,12,6,0,0,0,64),);a=dict(representation='connected',genome=Genome(Body(tuple(bs),g.body.ports)).to_dict())
        graph,slots=dependencies(a,True);self.assertEqual(graph[2],[6]);self.assertEqual(slots[2],[6]);self.assertIn([0,2,6],cross_edges(a,a))
        arrays=compile_pair(a,a,[0,2,6]);self.assertEqual(arrays[2][2,6],16)

    def test_divergence_is_bounded_to_recorded_common_ticks(self):
        a=np.zeros((3,10,4),np.uint16);b=a.copy();b[2,6,1]=5
        d=divergence(a,b);self.assertEqual((d['first_tick'],d['first_channel'],d['first_site']),(2,6,1))
        self.assertIsNone(divergence(a[:2],b)['first_tick'])


if __name__=='__main__':unittest.main()
