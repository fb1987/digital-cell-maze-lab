"""M24 structural and saved-data checks; no new maze or scientific inference."""
from maze_evolution.branch_causality import *


def pool():
    a=readz(PRIOR/'ancestry.json.gz');s=readz(PRIOR/'sources.json.gz')
    return a,s,make_variants(a,s)


def test_exact_chain_and_last_edit():
    a,s,v=pool();chain=lineage(a)
    assert len(chain)==17 and all(len(e['events'])==1 for e in chain[1:])
    g=Genome.from_dict(chain[-1]['item']['genome']);p=Genome.from_dict(chain[-2]['item']['genome'])
    assert g==factorial(g,p,False,False,True)
    assert p==factorial(g,p,False,False,False)
    assert g.body.ports[2][3]==8 and p.body.ports[2][3]==2
    assert not g.body.blocks[8] and g.initialization[8]==0


def test_full_factorial_material_and_specific_changes():
    a,s,v=pool();g=Genome.from_dict(a[FOCAL]['item']['genome'])
    for i in v['items']:
        if i['kind']!='factorial':continue
        h=Genome.from_dict(i['model']['genome'])
        assert h.body.instructions==g.body.instructions==113 and h.initialization==g.initialization
        assert list(map(len,h.body.blocks))==list(map(len,g.body.blocks))
        for m,(b,c) in enumerate(zip(h.body.blocks,g.body.blocks)):
            for n,(left,right) in enumerate(zip(b,c)):
                if (m,n) in ((0,12),(7,15)) and i['bypass0' if m==0 else 'bypass7']:
                    assert left.op==right.op==12 and left.b==left.c==right.c
                    assert left.a==right.a and left.gate==right.gate
                else:assert left==right
        assert all(h.body.ports[m]==g.body.ports[m] for m in range(10) if m!=2)
    assert sum(i['kind']=='factorial' for i in v['items'])==8
    assert sum(i['kind']=='protected' for i in v['items'])==13


def test_bypass_select_keeps_dispatch_and_gate():
    a,s,v=pool();g=Genome.from_dict(a[FOCAL]['item']['genome']);p=Genome.from_dict(a[a[FOCAL]['item']['parent']]['item']['genome'])
    h=factorial(g,p,True,True,True)
    for m,n in BRANCHES:
        saved=g.body.blocks[m][n+2];bypassed=h.body.blocks[m][n+2]
        for condition in (0,1,8):
            regs=[0]*64;regs[saved.a]=condition;regs[saved.b]=7;regs[saved.c]=19
            assert (regs[bypassed.b] if regs[bypassed.a] else regs[bypassed.c])==19
        assert saved.op==bypassed.op and saved.gate==bypassed.gate==64


def test_reused_panel_and_frozen_trace_rule():
    d,t=panel_and_traces();assert not d['new_layouts'] and not d['independent_confirmation']
    assert len(d['queries']['all'])==1680 and GAIN in t['selected_cases'] and COUNTERPOSE in t['selected_cases']
    assert len(t['selected_cases'])==10
    old=readz(PRIOR/'confirmation.json.gz')
    assert d['mazes']==old['mazes'] and d['metadata']==old['metadata'] and d['queries']==old['queries']


def test_summary_replay_on_artificial_saved_rows(tmp_path,monkeypatch):
    import maze_evolution.branch_causality as study
    a,s,v=pool();d,t=panel_and_traces();writez(tmp_path/'variants.json.gz',v)
    old=readz(PRIOR/'final_responses.json.gz')['rows']
    rows={i['id']:old.get(i['id'],old[FOCAL]) for i in v['items']}
    monkeypatch.setattr(study,'OUT',tmp_path)
    result=study.summary(d,rows)
    assert len(result['factorial'])==8 and len(result['lineage'])==17 and result['archive_aliases']==103
    assert not result['independent_confirmation']
    assert result==study.summary(d,rows)
