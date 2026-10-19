"""V12O bounds, ancestry, equal budgets and independent metrics on saved fixtures."""
import json
from types import SimpleNamespace
import numpy as np
import pytest
from maze_evolution.foundation_study import read_compressed
from maze_evolution.mutation_depth_data import OUT,FIXTURES,ARMS,TOPS,query
from maze_evolution.branch_pressure_study import loaded
from maze_evolution.branch_pressure_audit import geometry
from maze_evolution.mutation_depth_metrics import summarize,compare,nominate,supply
from maze_evolution.mutation_depth_audit import independent_scores,independent_comparison
from maze_evolution.mutation_depth_study import Budget
from maze_evolution.exposure_genome import Individual
from maze_evolution.growth import replay_mutation

@pytest.fixture(scope='module')
def pool():return read_compressed(OUT/'pools.json.gz')


def test_complete_orientation_coverage():
    d=loaded(FIXTURES);assert geometry(d)==480;ids=query(d,True);assert len(ids)==480
    for c in d.contexts:assert {p['pose'] for p in c['poses']}==set(range(8))


def test_equal_terminal_budgets_and_reference_roots(pool):
    assert len(pool['entries'])==3168
    for rep,arms in pool['groups'].items():
        assert set(arms)==set(ARMS) and all(len(ids)==192 for ids in arms.values()) and len(pool['roots'][rep])==96
        for arm,ids in arms.items():
            assert len({pool['entries'][i]['reference'] for i in ids})==96
            for i in ids:
                e=pool['entries'][i];assert e['reference'] in pool['roots'][rep]
                if arm=='resample':assert e['item']['parent'] is None
                elif arm=='single':assert e['item']['parent']==e['reference']


def test_walks_preserve_all_steps_and_concrete_replay(pool):
    events=read_compressed(OUT/'events.json.gz');assert len(events)==9792
    by={i:e['item'] for i,e in pool['entries'].items() if e['arm']=='frozen'}
    for event in events:
        child=Individual.load(event['item']);parent=Individual.load(by[child.parent]);assert replay_mutation(parent.genome.program,event['event'],256)==child.genome.program
        assert child.genome.exposure==parent.genome.exposure and len(child.genome.genes)<=256;by[child.identity]=event['item']
    walks=read_compressed(OUT/'walks.json.gz');assert len(walks)==576
    for w in walks:
        assert set(w['checkpoints'])=={'1','4','16'} and set(w['checkpoint_rng'])=={'1','4','16'}
        assert w['after']==w['checkpoint_rng']['16']


def test_neutral_exposure_and_physical_aliases(pool):
    models=read_compressed(OUT/'models.json.gz');aliases=read_compressed(OUT/'aliases.json.gz')
    for top in TOPS:
        assert set(aliases[top])==set(pool['entries'])
        for i,pid in aliases[top].items():
            assert models[pid]['topology']==top and models[pid]['genome']['exposure']==7
            assert models[pid]['genome']['genes']==pool['entries'][i]['item']['genome']['genes']


def artificial(behavior):
    d=loaded(FIXTURES);rows=[]
    for cid in query(d,True):
        o=d.cache[cid];m=d.metadata[cid];points=set(o.path)
        if behavior=='flood' and m['family']=='paired':
            sibling=next(c for c in d.metadata if d.metadata[c]['base']==m['base'] and d.metadata[c]['pose']==m['pose'] and d.metadata[c]['family']=='paired' and d.metadata[c]['side']!=m['side']);points|=set(d.metadata[sibling]['path'])
        elif behavior=='markers':points={o.maze.start,o.maze.goal} if o.path else set()
        mask=np.zeros(81,np.uint8);mask[list(points)]=1;optimal=behavior=='correct' and bool(o.path)
        rows.append(dict(case=cid,mask=np.packbits(mask,bitorder='little').tobytes().hex(),status='emitted' if o.path else 'no_path',optimal=optimal,valid=optimal,no_path=not o.path,reachable=bool(o.path),partial=0.,steps=1,active=1,reads=1,dispatches=1,range_reads=[1,0,0,0],exposure_checks=0))
    return rows,d.metadata


@pytest.mark.parametrize('behavior',['correct','flood','markers'])
def test_independent_score_signed_and_signature(behavior):
    rows,meta=artificial(behavior);m=summarize(rows,meta);independent_scores(rows,meta,m)
    assert m['mean_score']==(1 if behavior=='correct' else 0)
    assert m['mean_signed']==(1 if behavior=='correct' else 0)
    assert compare(m,m)['new_positive_pairs']==0 and not compare(m,m)['useful']


def test_new_response_requires_actual_improvement():
    a,meta=artificial('correct');b,_=artificial('flood');child,root=summarize(a,meta),summarize(b,meta);c=independent_comparison(child,root)
    assert c['useful'] and c['new_positive_pairs']==48 and c['new_positive_templates']==6
    assert not independent_comparison(root,child)['useful']


def test_shared_budget_has_no_final_reset():
    b=Budget(720,2);r=SimpleNamespace(spatial_reads=2,dispatches=3,exposure_checks=1)
    b.call(lambda:r);continued=Budget(720,2,saved=b.save());continued.call(lambda:r)
    assert continued.calls==2 and continued.work==12
    with pytest.raises(TimeoutError):continued.call(lambda:r)
    with pytest.raises(AssertionError):Budget(720,3,saved=b.save())


def test_unchanged_anchors_and_no_resampling_ancestry(pool):
    old=read_compressed(OUT.parent/'exposure_calibration/pools.json.gz');sel=read_compressed(OUT.parent/'exposure_calibration/selections.json.gz')
    for rep in pool['roots']:
        for i in old[f'fresh/{rep}']['items']:assert pool['entries'][i['id']]['item']==i
        assert set(pool['anchors'][rep])=={sel[f'fresh/{rep}'][a]['item']['id'] for a in ('neutral','local')}


def test_nomination_counts_inherited_skill_separately_from_new_supply():
    a,meta=artificial('correct');b,_=artificial('flood');correct,flood=summarize(a,meta),summarize(b,meta)
    entries={'new':{'reference':'root0','program_digest':'b'},'inherited':{'reference':'root1','program_digest':'a'}}
    metrics={'new':correct,'inherited':correct,'root0':flood,'root1':correct};aliases={k:k for k in metrics}
    n=nominate(['inherited','new'],entries,metrics,aliases)
    assert n['best']=='new' and n['comparisons']['new']['useful'] and not n['comparisons']['inherited']['useful']
    s=supply(['inherited','new'],entries,metrics,aliases)
    assert s['candidates']==2 and s['useful_count']==1 and s['useful_behaviors']==1
