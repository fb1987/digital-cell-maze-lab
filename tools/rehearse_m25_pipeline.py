"""M25 full discarded pipeline on old fixtures; no scientific genomes/new cases."""
import sys,time,json,multiprocessing
from pathlib import Path
from copy import deepcopy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution import skill_integration as m
from maze_evolution import skill_integration_analysis as a
from maze_evolution import skill_integration_checkpoint as cp
from maze_evolution.deep_campaign_store import packed,unpacked,hashed,writer_lock
from maze_evolution.referenced_campaign_store import Journal,load_layouts,write_reference
from maze_evolution.routing_transfer import canonical


def main():
    original_out=m.OUT;assert not (original_out/'registration.json').exists() and not (original_out/'pipeline_rehearsal.json').exists()
    packet=original_out/'pipeline_rehearsal';run=m.ROOT/'runs/skill_integration_m25/preparation_pipeline';packet.mkdir();run.mkdir(parents=True)
    initial=m.readz(original_out/'fixture_founders.json.gz');registry=m.readz(original_out/'fixture_registry.json.gz')
    for s in initial:s.setdefault('nominees',deepcopy(s['protected'][:3]))
    steps=m.readz(original_out/'rehearsal.json.gz');config=dict(m.CONFIG,layout_base_manifest=str(original_out/'registered_exclusions.json'))
    m.OUT=a.OUT=packet;m.RUN=a.RUN=run;m.check=a.check=lambda:config;m.pushed=a.pushed=lambda path:None
    a.founders=lambda seed:deepcopy(initial)
    m.writez(packet/'founders.json.gz',initial);m.writez(packet/'inherited_registry.json.gz',registry)
    fake=initial[0]['protected'][0]['genome']
    m.writez(packet/'comparison_archive.json.gz',[dict(id='archive/artificial-fixture',representation='connected',genome=fake)])
    layouts=load_layouts(original_out/'registered_exclusions.json');write_reference(packet/'exclusions.json',original_out/'registered_exclusions.json',layouts)
    for step in steps:
        # Validate every observed fixture layout against the historical exclusion ledger.
        from maze_evolution.deep_campaign_data import cases_from_manifest
        from maze_evolution.foundation_data import layout_hash,transform_maze
        for o in cases_from_manifest(step['data']['mazes']).values():
            assert all(layout_hash(transform_maze(o.maze,p)) in layouts for p in range(8))
    start=time.time();j=Journal(run);j.initialize(config,initial,layouts)
    for st in steps:
        data=st['data'];specs=m.task_specs(j.state(),data);assert len(specs)==len(st['receipts'])
        n=j.prepare(data,specs)
        for k,(spec,result) in enumerate(zip(specs,st['receipts'])):
            assert [e['aliases'] for e in spec]==[e['aliases'] for e in result['entries']]
            sizes={r['case_id']:r['w']*r['h'] for r in data['mazes']};calls,work=m.shared.reservation(spec,sizes)
            j.reserve(n,k,calls,work);j.receipt(n,k,result,work)
        states,decisions=m.transition(j.state(),data,j.results(n));assert decisions==st['decisions'] and hashed(packed(states))==st['state_hash']
        j.commit(n,states,decisions)
    j.put('finished',True);j.put('nomination_stop',dict(generation=j.state()[0]['generation'],reason='discarded_fixture'));j.db.commit()
    cp.freeze(j);search_usage=j.get('usage');j.close()
    fixture_validation=deepcopy(steps[0]['data']);fixture_validation['generation']=0
    m.data_builder.validation=lambda seed,previous:deepcopy(fixture_validation)
    lookup={s['data']['generation']:s['data'] for s in steps if s['data']['kind']=='train'}
    m.data_builder.training=lambda seed,g,previous:deepcopy(lookup[g])
    with writer_lock(run):a.audit_search()
    fixture=m.readz(m.ROOT/'results/connected_evolution/final_fixture.json.gz');fixture['new_layouts']=[]
    a.confirmation=lambda seed,previous:deepcopy(fixture)
    a.final();a.analyze()
    with writer_lock(run/'final'):a.audit_final()
    audits={name:json.loads((packet/name).read_text()) for name in ('search_audit.json','final_audit.json')}
    assert all(v['status']=='PASS' for v in audits.values())
    summary=json.loads((packet/'summary.json').read_text());assert not summary['policy_comparison']['descriptive_support']
    final=json.loads((packet/'final_session.json').read_text())
    m.writej(original_out/'pipeline_rehearsal.json',dict(status='PASS',scientific_cases=0,scientific_model_calls=0,artificial_models=True,reused_excluded_layouts_only=True,
        search_receipts_reused_without_new_inference=search_usage,search_audit_native=audits['search_audit.json']['native_replays'],
        final_usage=final['usage'],final_audit_native=audits['final_audit.json']['native_replays'],conventional_calls=audits['final_audit.json']['conventional_calls'],
        all_transition_grade_rng_freeze_summary_replayed=True,all_native_final=True,wall_seconds=time.time()-start))

if __name__=='__main__':main()
