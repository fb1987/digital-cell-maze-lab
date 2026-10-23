"""One-shot reviewed M32 completion; preserve all prior seals and journals."""
import json,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.repair_evolution_m32 import *
from tools.seal_m28_completion import published_files

def main():
    config=check();assert not (OUT/'completion.json').exists();prior=prior_check();status=json.loads((RUN/'recovery_a1_workflow_status.json').read_text())
    assert status['state']=='audited_ready_for_report'
    assert [x['phase'] for x in status['steps']]==['export','freeze','audit_search','final','analyze','audit_final'] and all(x['code']==0 for x in status['steps'])
    from tools.m32_export_recovery_a1 import approved,failure_check,A1
    approved();failure_check();assert json.loads((RUN/'workflow_status.json').read_text())['state']=='failed'
    a1launch=json.loads((A1/'launch.json').read_text());a1reg=json.loads((A1/'registration.json').read_text())
    published_files(a1launch['registration_commit'],dict(a1reg['files'],**{str((A1/'registration.json').relative_to(ROOT)):sha(A1/'registration.json')}))
    receipt=json.loads((A1/'export_receipt.json').read_text());rehearsal=json.loads((A1/'rehearsal.json').read_text())
    assert receipt['new_evolution_rounds']==receipt['new_inference_calls']==receipt['new_cases']==0 and receipt['nominees_unchanged']==18
    assert receipt['semantic_payload_hashes']==rehearsal['semantic_payload_hashes']==a1reg['semantic_payload_hashes']
    charge=json.loads((OUT/'search_session.json').read_text())['original_wall_upper_seconds']+rehearsal['wall_seconds']+receipt['wall_seconds'];assert charge<config['session_wall_seconds']
    review=json.loads((OUT/'report_review.json').read_text());assert review['status']=='PASS' and review['report_sha256']==sha(OUT/'report.md')
    reg=json.loads((OUT/'registration.json').read_text());launch=json.loads((OUT/'launch.json').read_text());freeze=json.loads((OUT/'choice_freeze.json').read_text())
    for commit in (launch['registration_commit'],freeze['commit']):subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT,check=True)
    published_files(launch['registration_commit'],dict(reg['files'],**{str((OUT/'registration.json').relative_to(ROOT)):sha(OUT/'registration.json')}))
    published_files(freeze['commit'],{str((OUT/n).relative_to(ROOT)):sha(OUT/n) for n in ('choices.json.gz','ancestry.json.gz','final_states.json.gz','search_session.json')})
    assert freeze['choices_sha256']==sha(OUT/'choices.json.gz') and freeze['published_before_final']
    sessions={};audits={}
    for name in ('source','search','final'):
        x=json.loads((OUT/(name+'_session.json')).read_text());a=json.loads((OUT/(name+'_audit.json')).read_text());sessions[name]=x;audits[name]=a
        assert x['status']=='complete' and x['usage']['uncertain_attempts']==0 and a['status']=='PASS'
        ceiling=config['session_wall_seconds'] if name=='search' else config[name+'_wall_seconds']
        assert x['wall_seconds']<ceiling and a['wall_seconds']<config['audit_wall_seconds']
        assert max(x['rss_peak_bytes'],a['rss_peak_bytes'])<config['memory_bytes']
        assert x['usage']['calls']<=config['call_cap'] and x['usage']['work']<=config['work_cap']
        assert a['all_native_replays']==a['independent_grades']==x['usage']['calls'] and a['counted_work']==x['usage']['work'] and a['all_controls_correct'] and a['prior_hashes']==prior
    dd,rr,_,usage,chain=load_finite('final');summary=summarize(dd,rr,readz(OUT/'choices.json.gz'),readz(OUT/'sources.json.gz'));summary.update(usage=usage,chain=chain)
    assert summary==json.loads((OUT/'summary.json').read_text())
    saved=json.loads((OUT/'saved_diagnostics.json').read_text());assert saved['status']=='PASS' and saved['no_new_inference'] and saved['query_filter_note']['all_primary_endpoints_and_gates_exactly_invariant']
    pres=json.loads((OUT/'preservation.json').read_text())
    for r in pres['journals'].values():
        assert sha(ROOT/r['journal']['path'])==r['journal']['sha256']
        if r['backup']['status']=='verified':assert sha(ROOT/r['backup']['path'])==r['backup']['sha256']
    for p,r in json.loads((OUT/'preparation_local_records.json').read_text()).items():assert sha(ROOT/p)==r['sha256'] and (ROOT/p).stat().st_size==r['bytes']
    assert len(load_layouts(OUT/'whole_layout_exclusions.json'))==pres['whole_layouts']
    logs=OUT/'logs';assert not logs.exists();logs.mkdir()
    for p in [*RUN.glob('*.log'),*RUN.glob('*.jsonl')]:shutil.copy2(p,logs/p.name)
    shutil.copy2(RUN/'workflow_status.json',OUT/'completed_original_failed_workflow_status.json')
    shutil.copy2(RUN/'recovery_a1_workflow_status.json',OUT/'completed_workflow_status.json')
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[ROOT/'docs/REPAIR_EVOLUTION_M32_PROGRESS.md']+list((ROOT/'tools').glob('*m32*.py'))
    files=dict(reg['files']);files.update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    local={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in RUN.rglob('*') if p.is_file() and (p.suffix in ('.sqlite','.log','.jsonl') or p.name in ('workflow_status.json','recovery_a1_workflow_status.json'))}
    assert storage()+1000000<config['storage_bytes'] and shutil.disk_usage(RUN).free>=config['disk_free_floor_bytes']
    writej(OUT/'completion.json',dict(status='complete_independent_confirmation_ALL_native_audits',files=files,local_records=local,registration_commit=launch['registration_commit'],choice_freeze_commit=freeze['commit'],all_audits_PASS=True,
        source_priors=prior,scientific_calls=sum(x['usage']['calls'] for x in sessions.values()),scientific_work=sum(x['usage']['work'] for x in sessions.values()),policy_comparison=summary['policy_comparison'],whole_layouts=pres['whole_layouts'],
        storage_bytes_before_seal=storage(),disk_free_bytes=shutil.disk_usage(RUN).free,old_histories_unchanged=True,no_final_reselection=True,approved_export_only_A1=True,recovery_registration_commit=a1launch['registration_commit'],conservative_search_wall_including_full_recovery=charge,original_failed_status_and_journals_unchanged=True,next_phase_launched=False,mutable_handoff='AGENTS.md intentionally outside seal; future audits NEW packets, never overwrite old seals/failures or rerun closed helpers.'))
    for p,h in files.items():assert sha(ROOT/p)==h,p
    print('M32 sealed',len(files),'files and',len(local),'local records',flush=True)
if __name__=='__main__':main()
