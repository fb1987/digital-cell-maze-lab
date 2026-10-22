"""M21 intervention invariants, synthetic genomes only, no new mazes."""
from maze_evolution.copy_specialization import fixture_sources
from maze_evolution.specialization_genome import eligible,copy
from maze_evolution.readout_causality import Genome,intervene,terminal,COPY_MODES

def fixture():
    g=Genome.from_dict(fixture_sources()['anchors']['parent']['genome'])
    edge=eligible(g)[0];c,_=copy(g,*edge,True)
    return g,c,edge

def test_exact_intact():
    g,c,(r,d,t)=fixture();assert intervene(c,r,d,t,'intact')==c

def test_bypass_keeps_every_gene_and_seed():
    g,c,(r,d,t)=fixture();v=intervene(c,r,d,t,'bypass_keep')
    assert v.body.blocks==c.body.blocks and v.initialization==c.initialization
    assert v.body.ports[r]==g.body.ports[r]
    assert all(v.body.ports[k]==c.body.ports[k] for k in range(10) if k!=r)

def test_removal_only_changes_target_block_and_seed():
    g,c,(r,d,t)=fixture();v=intervene(c,r,d,t,'remove_only')
    assert not v.body.blocks[t] and v.initialization[t]==0 and v.body.ports==c.body.ports
    assert all(v.body.blocks[k]==c.body.blocks[k] for k in range(10) if k!=t)

def test_bypass_then_remove_restores_source_active_body():
    g,c,(r,d,t)=fixture();v=intervene(c,r,d,t,'bypass_remove')
    assert v.body.blocks==g.body.blocks and v.initialization==g.initialization
    assert v.body.ports[:8]==g.body.ports[:8]

def test_terminal_restoration_adapts_only_destination():
    g,c,(r,d,t)=fixture();old=g.body.blocks[r][-1]
    appended=terminal(c,r,old,True);restored=terminal(appended,r,old)
    assert len(restored.body.blocks[r])==len(c.body.blocks[r])+1
    assert restored.body.blocks[r][:-1]==c.body.blocks[r]
    a=restored.body.blocks[r][-1].row();b=old.row();assert a[:1]+a[2:]==b[:1]+b[2:]
    assert a[1]==12+len(restored.body.blocks[r])-1
