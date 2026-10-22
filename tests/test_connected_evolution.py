"""M19 meaningful operator, ancestry, allocation, endpoint and pipeline checks."""
import json,random
from copy import deepcopy
from contextlib import nullcontext
import numpy as np
from maze_evolution import connected_evolution as m
from maze_evolution.connected_evolution_genome import Genome,Body,ordinary,vary,eligible,copy,ARMS,embed
from maze_evolution.connected_evolution_checkpoint import founders,inherited_registry,lineage,CHILD
from maze_evolution.modular_genome import random_genome
from maze_evolution.connected_trace import respond
from maze_evolution.datasets import make_case
from maze_evolution.exposure_selection import record
from maze_evolution.connected_runtime import Organism
from maze_evolution.deep_campaign_store import packed,unpacked,hashed
from maze_evolution import connected_evolution_metrics as metrics


def test_matched_forks_rng_source_provenance_and_no_solver():
    states=founders(m.CONFIG['seed']);assert states==m.readz(m.OUT/'founders.json.gz')
    registry=m.readz(m.OUT/'inherited_registry.json.gz');assert len(registry)==760
    for rep in range(3):
        trio=states[rep*3:rep*3+3]
        assert all(s['rng']==trio[0]['rng'] and [i['genome'] for i in s['population']]==[i['genome'] for i in trio[0]['population']] for s in trio)
        for s in trio:
            assert len(s['protected'])==13 and len(s['population'])==96 and s['generation']==0 and s['allocation']=='explore'
            for i in s['population']:
                h=lineage(i['id'],registry,registry);assert h['phase_mutations']==0
                assert h['cumulative_mutations']==i['mutation_depth']
                assert not any(Genome.from_dict(i['genome']).body.blocks[8:])
    assert registry[CHILD]['phase']=='M15' and registry[CHILD]['events']
    assert registry[CHILD]['source_record']==m.readz(m.OUT/'sources.json.gz')['anchors']['child']


def test_common_mutation_replay_caps_and_spare_recycling():
    for arm in ARMS:
        rng=random.Random(191);g=embed(random_genome(rng));recycled=0;copied=0
        for _ in range(1000):
            state=rng.getstate();a,e=vary(g,rng,arm);end=rng.getstate();rng.setstate(state);b,f=vary(g,rng,arm)
            assert a==b and e==f and rng.getstate()==end
            assert e['before']==g.digest and e['after']==a.digest and a.instructions<=256
            assert Genome.from_dict(a.to_dict())==a and all(len(x)<=31 for x in a.body.blocks)
            recycled+=e['kind']=='deactivate_spare';copied+=e['kind'].startswith('initialized_')
            for k in (8,9):
                if not a.body.blocks[k]:assert a.initialization[k]==0
            g=a
        assert copied==0 if arm=='generic' else copied>0


def test_prospective_copy_generalized_live_edges_common_history_and_coupling():
    rng=random.Random(192);g=embed(random_genome(rng));o=make_case(1919,'m19-test',0,0,9,'random');maze=o.maze
    # Exercise the general operator after ordinary port/code changes, with one
    # unused target. Every eligible choice is structural, never final-data chosen.
    for _ in range(30):
        for edge in eligible(g)[:4]:
            a,event=copy(g,*edge,True);b,_=copy(g,*edge,False)
            _,old,_=respond(dict(genome=g.to_dict()),maze);r,h,_=respond(dict(genome=a.to_dict()),maze)
            native=Organism(a).react(maze.cells,maze.w,maze.h,maze.start,maze.goal)
            assert record(r,o)==record(native,o)
            n=min(len(h),len(old));keep=[k for k in range(10) if k!=edge[2]]
            assert np.array_equal(h[:n,keep],old[:n,keep])
            assert np.array_equal(h[:,edge[2]],h[:,edge[1]])
            assert b.body.blocks==a.body.blocks and b.initialization==a.initialization
        g,_=ordinary(g,rng)


def test_spare_slot_deletion_resets_nonzero_initialization():
    from maze_evolution.regulatory import Gene
    from maze_evolution.modular_genome import Genome as Base
    g=embed(Base(tuple((Gene(0,12,k,0,0,0,64),) for k in range(8)),(tuple(range(8)),)*8))
    # Output reader2 consumes donor0, whose generic source flag is nonzero.
    bs=list(g.body.blocks[:8]);bs[2]=(Gene(0,12,0,0,0,0,64),)
    g=embed(Base(tuple(bs),(tuple(range(8)),)*8))
    a,_=copy(g,2,0,8,True);assert a.initialization[8]==1
    for seed in range(10000):
        b,event=ordinary(a,random.Random(seed))
        if event['kind']=='deactivate_spare':
            assert event['block']==8 and not b.body.blocks[8] and b.initialization[8]==0;break
    else:raise AssertionError('Spare deletion not reachable')


def test_phase_entry_exclusion_disconnection_and_fixed_primary():
    from tests.test_exploration_allocation import gate_fixture
    child,root,union,a0,meta=gate_fixture()
    yes,_=metrics.acquisition(child,root,root,union,a0,meta,1);assert yes['upstream_acquisition']
    no,_=metrics.acquisition(child,root,child,union,a0,meta,1);assert not no['upstream_acquisition']
    no,_=metrics.acquisition(child,root,root,union,a0,meta,0);assert not no['upstream_acquisition']
    bad=deepcopy(child);bad['correct_no_path']=set();no,_=metrics.acquisition(bad,root,root,union,a0,meta,1);assert not no['retention_and_disconnection_gate']
    conditions=[]
    for rep in range(3):
        for arm in ARMS:
            for rank in range(3):
                conditions.append(dict(replicate=rep,arm=arm,rank=rank,child=f'{rep}/{arm}/{rank}',retention_and_disconnection_gate=rank!=0,
                    beyond_root_and_protected_union=dict(new_upstream_pairs=100 if arm=='connected' else 0)))
    p=metrics.policy_comparison(conditions);assert not p['descriptive_support_both'] and all(x['connected']==0 for x in p['pairs'])
    for c in conditions:
        if c['rank']==0 and c['arm']=='connected':c['retention_and_disconnection_gate']=True
    assert metrics.policy_comparison(conditions)['descriptive_support_both']


def test_rehearsal_nominal_allocations_rng_and_phase_ancestry():
    states=m.readz(m.OUT/'fixture_founders.json.gz');registry=m.readz(m.OUT/'fixture_registry.json.gz');inherited=dict(registry);births=0
    for step in m.readz(m.OUT/'rehearsal.json.gz'):
        count=[0]*9
        for task in m.task_specs(states,step['data']):
            for e in task:
                for k,identity in e['aliases']:count[k]+=len(e['queries'])
        assert count==([96*96]*9 if step['data']['kind']=='train' else [115*392]*9)
        states,events=m.transition(states,step['data'],step['receipts'])
        assert events==step['decisions'] and hashed(packed(states))==step['state_hash']
        for event in events:
            for b in event['births']:
                identity=b['item']['id'];assert identity not in registry;registry[identity]=dict(b,phase='M19');births+=1
                h=lineage(identity,registry,inherited);assert h['cumulative_mutations']==b['item']['mutation_depth']
    assert births==1404 and all(s['generation']==s['assessment_generation']==3 for s in states)


def test_complete_discarded_pipeline(tmp_path,monkeypatch):
    from maze_evolution import connected_evolution_analysis as a
    steps=m.readz(m.OUT/'rehearsal.json.gz');ss=m.readz(m.OUT/'fixture_founders.json.gz');reg=m.readz(m.OUT/'fixture_registry.json.gz')
    out=tmp_path/'out';out.mkdir();run=tmp_path/'run'
    m.writez(out/'founders.json.gz',ss);m.writez(out/'inherited_registry.json.gz',reg)
    def export(name,hashes):
        path=out/(name+'.part.json.gz');m.writez(path,dict(hashes=sorted(hashes)))
        m.writej(out/(name+'.json'),dict(count=len(hashes),parts=[dict(path=str(path),count=len(hashes),sha256=m.sha(path))]))
    export('exclusions',set());config=dict(m.CONFIG,max_rounds=3,storage_bytes=512*2**20,layout_base_manifest=str(out/'exclusions.json'))
    monkeypatch.setattr(m,'OUT',out);monkeypatch.setattr(m,'RUN',run);monkeypatch.setattr(m,'check',lambda:config)
    monkeypatch.setattr(m,'pushed',lambda _:None);monkeypatch.setattr(m,'write_layouts',export)
    monkeypatch.setattr(m.data_builder,'validation',lambda *args:deepcopy(steps[0]['data']))
    monkeypatch.setattr(m.data_builder,'training',lambda seed,g,previous:deepcopy(steps[g+1]['data']))
    monkeypatch.setattr(m,'ProcessPoolExecutor',lambda *args,**kwargs:nullcontext(None))
    def saved(j,n,data,*args):
        for k,spec,status in j.tasks(n):
            receipt=steps[n]['receipts'][k];j.reserve(n,k,receipt['calls'],receipt['work']);j.receipt(n,k,receipt,receipt['work'])
        return None
    monkeypatch.setattr(m.shared,'run_stage',saved)
    m.run();session=json.loads((out/'session.json').read_text());assert session['generation']==3
    original=(out/'choices.json.gz').read_bytes();m.run();assert (out/'choices.json.gz').read_bytes()==original
    monkeypatch.setattr(a,'OUT',out);monkeypatch.setattr(a,'RUN',run);monkeypatch.setattr(a,'check',lambda:config)
    monkeypatch.setattr(a,'pushed',lambda _:None);monkeypatch.setattr(a,'founders',lambda seed:ss)
    a.audit_search();assert json.loads((out/'search_audit.json').read_text())['births_replayed']==1404
    # Native final execution; the saved-stage adapter is search-only.
    monkeypatch.undo()
    monkeypatch.setattr(m,'OUT',out);monkeypatch.setattr(m,'RUN',run)
    monkeypatch.setattr(a,'OUT',out);monkeypatch.setattr(a,'RUN',run);monkeypatch.setattr(a,'check',lambda:config)
    monkeypatch.setattr(a,'pushed',lambda _:None)
    monkeypatch.setattr(a,'confirmation',lambda *args:deepcopy(m.readz(m.ROOT/'results/connected_evolution/final_fixture.json.gz')))
    a.final();a.analyze();a.audit_final()
    summary=json.loads((out/'summary.json').read_text());audit=json.loads((out/'final_audit.json').read_text())
    assert summary['phase']=='M19' and len(summary['conditions'])==27 and audit['native_replays']==summary['usage']['calls']


def test_copy_of_spare_and_instruction_ceiling():
    from maze_evolution.regulatory import Gene
    from maze_evolution.modular_genome import Genome as Base
    bs=[(Gene(0,12,k,0,0,0,64),) for k in range(8)];bs[2]=(Gene(0,12,0,0,0,0,64),)
    g=embed(Base(tuple(bs),(tuple(range(8)),)*8));a,_=copy(g,2,0,8,True)
    assert (2,8,9) in eligible(a);b,e=copy(a,2,8,9,True)
    assert b.initialization[9]==1 and b.body.ports[2][0]==9
    m0=make_case(1919,'m19-test',0,0,9,'random').maze
    _,old,_=respond(dict(genome=a.to_dict()),m0);_,h,_=respond(dict(genome=b.to_dict()),m0)
    n=min(len(old),len(h));assert np.array_equal(old[:n,:9],h[:n,:9]) and np.array_equal(h[:,8],h[:,9])
    blocks=tuple(tuple(Gene(0,12+i,k if k!=2 else 0,0,0,0,64) for i in range(31)) for k in range(8))
    g=embed(Base(blocks,(tuple(range(8)),)*8));assert g.instructions==256
    child,event=copy(g,2,0,8,True);assert child==g and event['kind']=='bounded_noop'
