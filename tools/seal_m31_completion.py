"""Seal reviewed M31 exactly once, retaining immutable science and old records."""
import json,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.output_access_m31 import ROOT,OUT,RUN,check,prior_check,readz,writej,sha,storage,load,summarize
from maze_evolution.referenced_campaign_store import load_layouts
from tools.seal_m28_completion import published_files

def main():
    config=check();assert not (OUT/'completion.json').exists();prior=prior_check()
    status=json.loads((RUN/'workflow_status.json').read_text());assert status['state']=='audited_ready_for_report'
    expected=['development','select','freeze','audit_development','trace','audit_trace','analyze_trace','final','analyze','audit_final']
    assert [s['phase'] for s in status['steps']]==expected and all(s['code']==0 for s in status['steps'])
    review=json.loads((OUT/'report_review.json').read_text());assert review['status']=='PASS' and review['report_sha256']==sha(OUT/'report.md')
    launch=json.loads((OUT/'launch.json').read_text());reg=json.loads((OUT/'registration.json').read_text());freeze=json.loads((OUT/'choice_freeze.json').read_text())
    for commit in (launch['registration_commit'],freeze['commit']):subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT,check=True)
    published_files(launch['registration_commit'],dict(reg['files'],**{str((OUT/'registration.json').relative_to(ROOT)):sha(OUT/'registration.json')}))
    published_files(freeze['commit'],{str((OUT/name).relative_to(ROOT)):sha(OUT/name) for name in ('choices.json.gz','development_summary.json.gz','development_session.json')})
    assert freeze['choices_sha256']==sha(OUT/'choices.json.gz') and freeze['published_before_fresh_generation']
    for name,key in (('pool.json.gz','pool_sha256'),('sources.json.gz','source_sha256'),('development_panel.json.gz','development_panel_sha256')):assert sha(OUT/name)==launch[key]
    sessions={};audits={}
    for name in ('development','trace','final'):
        s=json.loads((OUT/(name+'_session.json')).read_text());a=json.loads((OUT/(name+'_audit.json')).read_text());sessions[name]=s;audits[name]=a
        assert s['status']=='complete' and s['usage']['uncertain_attempts']==0
        ceiling=config['session_wall_seconds'] if name=='development' else config['trace_wall_seconds'] if name=='trace' else config['final_wall_seconds']
        assert s['wall_seconds']<ceiling and a['status']=='PASS' and a['wall_seconds']<config['audit_wall_seconds']
        assert max(s['rss_peak_bytes'],a['rss_peak_bytes'])<config['memory_bytes']
        assert s['usage']['calls']<=config['call_cap'] and s['usage']['work']<=config['work_cap']
        assert a['all_native_replays']==a['independent_grades']==s['usage']['calls'] and a['counted_work']==s['usage']['work']
        assert a['all_controls_correct'] and a['source_prior_hashes']==prior
    data,rows,models,usage,chain=load('final');summary=json.loads((OUT/'summary.json').read_text())
    assert summarize(readz(OUT/'pool.json.gz'),readz(OUT/'choices.json.gz'),data,rows,usage,chain)==summary
    pres=json.loads((OUT/'preservation.json').read_text())
    for rec in pres['journals'].values():
        assert sha(ROOT/rec['journal']['path'])==rec['journal']['sha256']
        if rec['backup']['status']=='verified':assert sha(ROOT/rec['backup']['path'])==rec['backup']['sha256']
    assert len(load_layouts(OUT/'whole_layout_exclusions.json'))==pres['whole_layouts']
    for p,r in json.loads((OUT/'preparation_local_records.json').read_text()).items():assert sha(ROOT/p)==r['sha256'] and (ROOT/p).stat().st_size==r['bytes'],p
    assert json.loads((OUT/'saved_diagnostics.json').read_text())['no_new_inference']
    assert json.loads((OUT/'trace_summary.json').read_text())['frozen_nominees_only']
    for note in ('readout_algebra_note.json','witness_review.json','fresh_pose_review.json'):assert json.loads((OUT/note).read_text())['status']=='PASS'
    logs=OUT/'logs';assert not logs.exists();logs.mkdir()
    for p in [*RUN.glob('*.log'),*RUN.glob('*.jsonl')]:shutil.copy2(p,logs/p.name)
    shutil.copy2(RUN/'workflow_status.json',OUT/'completed_workflow_status.json')
    paths=[p for p in OUT.rglob('*') if p.is_file()]
    paths += [ROOT/'docs/OUTPUT_ACCESS_M31_PROGRESS.md',ROOT/'tools/preserve_m31.py',ROOT/'tools/analyze_m31_saved.py',ROOT/'tools/verify_m31_readout.py',ROOT/'tools/review_m31_witness.py',ROOT/'tools/inspect_m31_counterparts.py',ROOT/'tools/review_m31_fresh_pose.py',ROOT/'tools/render_m31_witness.py',ROOT/'tools/report_m31.py',Path(__file__).resolve()]
    for p in (OUT/'postprocessing_failures').rglob('*'):
        if p.is_file():paths.append(p)
    files=dict(reg['files']);files.update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    local={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in RUN.rglob('*') if p.is_file() and (p.suffix in ('.sqlite','.log','.jsonl') or p.name=='workflow_status.json')}
    assert storage()+1000000<config['storage_bytes'] and shutil.disk_usage(RUN).free>=config['disk_free_floor_bytes']
    writej(OUT/'completion.json',dict(status='complete_independent_confirmation_all_native_and_trace_audits',files=files,local_records=local,
        registration_commit=launch['registration_commit'],choice_freeze_commit=freeze['commit'],policy_comparison=summary['policy_comparison'],source_priors=prior,
        scientific_calls=sum(s['usage']['calls'] for s in sessions.values()),scientific_work=sum(s['usage']['work'] for s in sessions.values()),
        all_audits_PASS=True,whole_layouts=pres['whole_layouts'],storage_bytes_before_seal=storage(),disk_free_bytes=shutil.disk_usage(RUN).free,
        no_multigeneration_evolution=True,no_final_reselection=True,old_histories_unchanged=True,next_phase_launched=False,
        mutable_handoff='AGENTS.md intentionally excluded. Future audits use NEW packets; never overwrite old seals/failures or rerun closed helpers.'))
    for p,h in files.items():assert sha(ROOT/p)==h,p
    print('M31 sealed',len(files),'files and',len(local),'local records',flush=True)

if __name__=='__main__':main()
