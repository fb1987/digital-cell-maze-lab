import random
from maze_evolution.modular_genome import random_genome,Genome
from maze_evolution.mechanism_retention import restored,silenced,specs


def test_restoration_preserves_exact_whole_blocks_and_endpoints():
    rng=random.Random(210109);a=random_genome(rng).to_dict();b=random_genome(rng).to_dict()
    assert restored(a,b,0)==a and restored(a,b,255)==b
    for bits in range(256):
        x=restored(a,b,bits);Genome.from_dict(x)
        for k in range(8):
            for f in ('blocks','ports'):assert x[f][k]==(b if bits>>k&1 else a)[f][k]


def test_silencing_only_replaces_output_node_and_preserves_cap():
    g=random_genome(random.Random(210110));a=g.to_dict()
    for k in range(8):
        x=silenced(a,k);assert Genome.from_dict(x).instructions==g.instructions
        assert x['ports']==a['ports']
        for j in range(8):
            if j!=k:assert x['blocks'][j]==a['blocks'][j]
        assert x['blocks'][k][:-1]==a['blocks'][k][:-1]
        assert x['blocks'][k][-1]==[1,a['blocks'][k][-1][1],0,0,0,0,64]


def test_dedup_preserves_all_aliases_and_identical_case_allocation():
    g=random_genome(random.Random(210111)).to_dict()
    p=dict(items={i:dict(representation='modular',genome=g) for i in ('a','b')})
    out=specs(p,['case1','case2']);assert len(out)==1
    assert out[0][0]['aliases']==['a','b'] and out[0][0]['queries']==['case1','case2']


def test_summary_uses_saved_rows_and_canonical_json():
    import json
    from maze_evolution.mechanism_retention import summarize,readz,ROOT
    data=readz(ROOT/'results/wave_continuation/final_fixture.json.gz')
    response=readz(ROOT/'results/wave_continuation/final_control_fixture.json.gz')['entries'][0]['rows']
    ids=['a0/root','a1/root','a0/child','a1/child','a0/parent','a0/last_edit_first','a0/last_edit_second','a0/zero/6']
    p=dict(items={i:dict(kind='software_fixture') for i in ids})
    result=summarize(data,{i:response for i in ids},p)
    assert result==json.loads(json.dumps(result))
    assert all(result['last_birth_checks'].values())
    assert not result['reference_eligibility']['eligible'] and not result['qualified_diagnostic_hits']
    assert all(r['joint_retention_screen'] for r in result['models'].values())
