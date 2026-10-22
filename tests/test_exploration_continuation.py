"""M15 continuation-specific checks; no scientific or fresh confirmation draws."""
import json,random,sqlite3
from copy import deepcopy
from contextlib import nullcontext
from maze_evolution import exploration_continuation as m
from maze_evolution.exploration_continuation_checkpoint import founders,lineage,source_registry,START
from maze_evolution.exploration_allocation_search import transition
from maze_evolution.deep_campaign_store import packed,unpacked,hashed


def test_exact_checkpoint_rng_registry_and_no_reset():
    states=founders(1);assert states==founders(999)==m.readz(m.OUT/'founders.json.gz')
    assert states==m.readz(m.ROOT/'results/exploration_allocation/final_states.json.gz')
    registry=source_registry();assert registry==m.readz(m.OUT/'inherited_registry.json.gz')
    assert len(registry)==20484
    for s in states:
        assert s['generation']==s['assessment_generation']==64
        for group in ('population','archive','protected','nominees','frozen'):
            for i in s[group]:
                assert registry[i['id']]['item']==i
                h=lineage(i['id'],registry,registry)
                assert h['phase_mutations']==0 and h['phase_entry']==i['id']
                assert h['cumulative_mutations']==i['mutation_depth']


def test_rehearsal_continues_exact_transition_budgets_and_ancestry():
    ss=founders();registry=m.readz(m.OUT/'inherited_registry.json.gz');inherited=dict(registry);count=0
    for step in m.readz(m.OUT/'rehearsal.json.gz'):
        counts=[0]*6
        for task in m.task_specs(ss,step['data']):
            for e in task:
                for k,i in e['aliases']:counts[k]+=len(e['queries'])
        assert counts==([96*96]*6 if step['data']['kind']=='train' else [115*392]*6)
        states,events=transition(unpacked(packed(ss)),step['data'],step['receipts'])
        assert events==step['decisions'] and hashed(packed(states))==step['state_hash']
        if step['data']['kind']=='assessment':assert states==ss
        for event in events:
            for b in event['births']:
                assert b['item']['id'] not in registry
                registry[b['item']['id']]=dict(b,phase='M15');count+=1
                h=lineage(b['item']['id'],registry,inherited)
                assert h['phase_mutations']==(0 if not b['item']['parent'] else lineage(b['item']['parent'],registry,inherited)['phase_mutations']+1)
                assert h['cumulative_mutations']==b['item']['mutation_depth']
                assert b['item']['birth']>64
        ss=states
    assert count==1248 and all(s['generation']==68 for s in ss)


def test_phase_entry_for_new_immigrant_and_inherited_descendant():
    root=dict(id='old',parent=None,mutation_depth=0)
    old=dict(id='prior-child',parent='old',mutation_depth=1)
    inherited={'old':dict(item=root,events=[]),'prior-child':dict(item=old,events=[{}])}
    reg=deepcopy(inherited)
    reg['new']=dict(item=dict(id='new',parent='prior-child',mutation_depth=2),events=[{}])
    h=lineage('new',reg,inherited)
    assert h['phase_entry']=='prior-child' and h['phase_mutations']==h['inherited_mutations']==1
    reg['immigrant']=dict(item=dict(id='immigrant',parent=None,mutation_depth=0),events=[])
    reg['immigrant-child']=dict(item=dict(id='immigrant-child',parent='immigrant',mutation_depth=1),events=[{}])
    h=lineage('immigrant-child',reg,inherited)
    assert h['phase_entry']=='immigrant' and h['phase_mutations']==1 and h['inherited_mutations']==0


def test_exact_reused_bank_and_all_fixtures_excluded():
    old=m.ROOT/'results/exploration_allocation'
    for name in ('source_panels.json.gz','source_panel.json.gz'):
        assert m.readz(m.OUT/name)==m.readz(old/name)
    oldset=m.load_layouts(old/'whole_layout_exclusions.json');current=m.load_layouts(m.OUT/'exclusions.json')
    assert len(oldset)==3049007 and oldset<=current
    added=set()
    for step in m.readz(m.OUT/'rehearsal.json.gz')[1:]:
        new=set(step['data']['new_layouts']);assert not new&(oldset|added);added|=new
    final=set(m.readz(m.OUT/'final_fixture.json.gz')['new_layouts']);assert not final&(oldset|added)
    assert current==oldset|added|final


# Reuse the already sealed boundary tests for unchanged mutation/selection/gates.
from tests.test_exploration_allocation import (
    test_common_global_operator_exact_replay_and_all_blocks,
    test_no_path_gate_nonvacuous_and_explicit_loss,
    test_novelty_false_no_path_mutation_and_prefix_boundaries,
    test_integration_gate_requires_all_parent_and_specialist_skills,
    test_policy_endpoint_does_not_reselect_or_reward_failed_integration,
    test_quality_profile_rejects_empty_flood_wall_timeout_and_false_no_path,
    test_exploration_samples_cells_not_clone_count_and_keeps_cap,
)


def test_nonzero_generation_full_pipeline(tmp_path,monkeypatch):
    from maze_evolution import exploration_continuation_analysis as a
    steps=m.readz(m.OUT/'rehearsal.json.gz');fixture=steps[0];train=steps[1]
    finalfixture=m.readz(m.OUT/'final_fixture.json.gz');ss=founders()
    inherited=m.readz(m.OUT/'inherited_registry.json.gz')
    out=tmp_path/'out';out.mkdir();run=tmp_path/'run'
    m.writez(out/'founders.json.gz',ss);m.writez(out/'inherited_registry.json.gz',inherited)
    def export(name,hashes):
        path=out/(name+'.part.json.gz');m.writez(path,dict(hashes=sorted(hashes)))
        m.writej(out/(name+'.json'),dict(count=len(hashes),parts=[dict(path=str(path),count=len(hashes),sha256=m.sha(path))]))
    export('exclusions',set())
    config=dict(m.CONFIG,max_rounds=65,storage_bytes=256*2**20,layout_base_manifest=str(out/'exclusions.json'))
    monkeypatch.setattr(m,'OUT',out);monkeypatch.setattr(m,'RUN',run)
    monkeypatch.setattr(m,'check',lambda:config);monkeypatch.setattr(m,'pushed',lambda _:None)
    monkeypatch.setattr(m,'write_layouts',export)
    monkeypatch.setattr(m.data_builder,'validation',lambda *args:deepcopy(fixture['data']))
    monkeypatch.setattr(m.data_builder,'training',lambda *args:deepcopy(train['data']))
    monkeypatch.setattr(m,'ProcessPoolExecutor',lambda *args,**kwargs:nullcontext(None))
    def saved_or_native(j,n,data,*args):
        tasks=j.tasks(n)
        for k,spec,status in tasks:
            receipt=(train['receipts'][k] if data['kind']=='train' else
                m.evaluate_task(spec,data['mazes'],hashed(packed(data['mazes']))))
            j.reserve(n,k,receipt['calls'],receipt['work']);j.receipt(n,k,receipt,receipt['work'])
        return None
    monkeypatch.setattr(m.shared,'run_stage',saved_or_native)
    m.run();session=json.loads((out/'session.json').read_text())
    assert session['new_rounds']==1 and session['generation']==65
    frozen=(out/'choices.json.gz').read_bytes();m.run();assert frozen==(out/'choices.json.gz').read_bytes()
    choices=m.readz(out/'choices.json.gz');ancestry=m.readz(out/'ancestry.json.gz')
    assert all(c['mutations']<=1 and c['cumulative_mutations']>=c['mutations'] for c in choices['comparisons'])
    for c in choices['comparisons']:
        assert c['phase_entry'] in choices['items']
        assert lineage(c['child'],ancestry,inherited)['phase_mutations']==c['mutations']
    monkeypatch.setattr(a,'OUT',out);monkeypatch.setattr(a,'RUN',run)
    monkeypatch.setattr(a,'check',lambda:config);monkeypatch.setattr(a,'pushed',lambda _:None)
    a.audit_search();audit=json.loads((out/'search_audit.json').read_text())
    assert audit['status']=='PASS' and audit['births_replayed']==312 and audit['stages']==2
    monkeypatch.setattr(a,'confirmation',lambda *args:deepcopy(finalfixture))
    monkeypatch.setattr(a,'ProcessPoolExecutor',lambda *args,**kwargs:nullcontext(None))
    a.final();a.analyze();a.audit_final()
    summary=json.loads((out/'summary.json').read_text());audit=json.loads((out/'final_audit.json').read_text())
    assert summary['phase']=='M15' and summary['start_generation']==64
    assert audit['status']=='PASS' and audit['native_replays']==summary['usage']['calls']
    for c in summary['conditions']:
        if not c['mutations']:
            assert not c['integration']['integration_pass'] and not c['upstream_acquisition'] and not c['long_ordinary_acquisition']
        assert c['phase_start_nominee'] in summary['all_models']
