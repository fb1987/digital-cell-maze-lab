"""Independent exact-work checks at the expanded hard ceiling."""
import numpy as np
from maze_evolution.growth import Genome
from maze_evolution.regulatory import Gene
from maze_evolution.growth_runtime import Organism,observe
from maze_evolution.runtime import Limits


def test_256_gene_runtime_and_probe_work_limits_are_exact():
    cells=bytes([1]*9);g=Genome(tuple(Gene(0,12,12) for _ in range(256)))
    organism=Organism(g,'evolved',goal_pulse=True,gene_limit=256)
    r=organism.react(cells,3,3,0,8)
    assert r.status=='no_path' and r.steps==4 and r.dispatches==r.active_instructions==9*256*4 and r.spatial_reads==0
    assert not r.mask.any() and not organism.program.flags.writeable
    for source in (True,False):
        p=observe(organism,cells,3,3,0,8,16,source)
        expected=np.zeros((8,9),dtype=np.uint16);expected[0,0]=int(source);expected[1,8]=1
        assert np.array_equal(p.state,expected) and p.steps==16 and p.dispatches==p.active==9*256*16 and p.reads==0
    small=Organism(Genome(g.genes[:128]),'evolved',goal_pulse=True,gene_limit=128).react(cells,3,3,0,8)
    assert r.array_bytes-small.array_bytes==128*7*4
    tight=Organism(g,'evolved',Limits(instructions_per_site=1),goal_pulse=True).react(cells,3,3,0,8)
    assert tight.status=='instruction_budget' and tight.steps==0 and tight.dispatches==9 and tight.spatial_reads==0
    remote=Genome(tuple(Gene(14,12,0,0,radius=3) for _ in range(256)))
    for ablate in (True,False):
        r=Organism(remote,'evolved',Limits(reads_per_site=1),ablate,True).react(cells,3,3,0,8)
        assert r.status=='read_budget' and r.steps==0 and r.dispatches==10 and r.spatial_reads==9 and r.range_reads==(0,0,0,9)
        assert r.active_instructions==9 and not r.mask.any()
