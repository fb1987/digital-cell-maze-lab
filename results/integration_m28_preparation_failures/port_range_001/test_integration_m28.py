import random
import unittest
from maze_evolution.integration_genome import *
from maze_evolution.connected_runtime import Organism


def constant(value):
    blocks=tuple((Gene(1,12,value if k==2 else 0,0,0,0,ALWAYS),) for k in range(8))+((),())
    return Genome(Body(blocks,(tuple(range(10)),)*10))


class IntegrationTests(unittest.TestCase):
    def test_splice_coherent(self):
        a,b=constant(1),constant(0);c,e=splice(a,b,2,3)
        self.assertEqual(c.body.blocks[2],b.body.blocks[2]);self.assertEqual(c.body.blocks[1],a.body.blocks[1])
        self.assertEqual(splice(a,b,0,8)[0].body,b.body)

    def test_alpha_and_ports(self):
        ports=(2,1,0,3,4,5,6,7,8,9)
        block=(Gene(0,12,0,0,0,0,1),Gene(6,13,0,2,0,0,12),Gene(12,14,12,13,9,0,64))
        x=remap_block(block,tuple(range(10)),ports,5)
        self.assertEqual(x[0],Gene(0,17,2,0,0,0,1))
        self.assertEqual(x[1],Gene(6,18,2,2,0,0,17))
        self.assertEqual(x[2],Gene(12,19,17,18,9,0,64))

    def test_unavailable_local_rejected(self):
        ports=(8,1,2,3,4,5,6,7,0,9)
        with self.assertRaises(ValueError):remap_block((Gene(0,12,0,0,0,0,64),),tuple(range(10)),ports,1)
        # The same physical channel is available to a neighbor read.
        self.assertEqual(remap_block((Gene(6,12,0,0,0,0,64),),tuple(range(10)),ports,1)[0].a,8)

    def test_selector_semantics_and_cost(self):
        a,b=constant(1),constant(0)
        false,_=fuse(a,b,2,Gene(1,14,0,0,0,0,64));true,_=fuse(a,b,2,Gene(1,14,1,0,0,0,64))
        cells=bytes([1]*9)
        ra=Organism(a).react(cells,3,3,0,8);rf=Organism(false).react(cells,3,3,0,8);rt=Organism(true).react(cells,3,3,0,8)
        self.assertEqual(ra.mask.tolist(),rf.mask.tolist());self.assertEqual(ra.status,rf.status)
        self.assertGreater(rf.dispatches,ra.dispatches)
        self.assertEqual(sum(rt.mask),0);self.assertEqual(sum(rf.mask),9)

    def test_capacity_rejection(self):
        a=constant(1);blocks=list(a.body.blocks);blocks[2]=tuple(Gene(1,12+i,1,0,0,0,64) for i in range(30))
        a=Genome(Body(tuple(blocks),a.body.ports));c,e=fuse(a,constant(0),2,Gene(1,43,1,0,0,0,64))
        self.assertEqual(a,c);self.assertEqual(e['reason'],'capacity')

    def test_rng_replay_and_validity(self):
        from maze_evolution.dormant_evolution_genome import random_genome
        for arm in ARMS:
            rng=random.Random(28);a=random_genome(rng);b=random_genome(rng)
            for _ in range(120):
                state=rng.getstate();c,e=vary(a,b,rng,arm);after=rng.getstate()
                again=random.Random();again.setstate(state);d,f=vary(a,b,again,arm)
                self.assertEqual((c,e,after),(d,f,again.getstate()));self.assertEqual(c,Genome.from_dict(c.to_dict()))
                self.assertLessEqual(c.instructions,256);a,b=b,c


if __name__=='__main__':unittest.main()
