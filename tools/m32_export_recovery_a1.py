"""PROPOSED M32 export-only A1. Apply is blocked without published user approval.

Rehearsal reads saved nominees without selection, evolution, inference or cases.
Original registered code, journal and failed workflow records never change.
"""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution import repair_evolution_m32 as m

A1=m.OUT/'recovery_a1'
FAILURE=m.OUT/'failures/export_001'
ARTIFACTS=('choices.json.gz','ancestry.json.gz','final_states.json.gz')

def failure_check():
    seal=json.loads((FAILURE/'failure_seal.json').read_text());add=json.loads((FAILURE/'stdout_seal_addendum_001.json').read_text())
    assert add['original_failure_seal_sha256']==m.sha(FAILURE/'failure_seal.json')
    for p,h in seal['files'].items():assert m.sha(m.ROOT/p)==h,p
    records=dict(seal['local_records']);records.update(add['local_record_overrides'])
    for p,r in records.items():assert m.sha(m.ROOT/p)==r['sha256'] and (m.ROOT/p).stat().st_size==r['bytes'],p
    return json.loads((FAILURE/'preservation.json').read_text())

def checkpoint():
    j=m.readonly('search')
    try:
        assert j.get('latest')==66 and not j.pending() and not j.get('finished')
        chain=j.verify_chain();states=j.state();assert len(states)==6 and all(st['generation']==st['assessment_generation']==62 for st in states)
        sources=m.readz(m.OUT/'sources.json.gz');registry=m.collect_registry(j,sources)
        items={i['id']:dict(id=i['id'],model=i['model']) for i in sources['items']};choices=[];needed=set()
        for st in states:
            for c in st['nominees']:
                # Minimal fix: c already owns role. Attach only absent context.
                assert not {'population','replicate','arm'}&set(c)
                i=c['item'];choices.append(dict(c,population=st['name'],replicate=st['replicate'],arm=st['arm']))
                for identity in (i['id'],i['entry'],i['parent']):
                    if identity:items[identity]=dict(id=identity,model=registry[identity]['item']['model'])
                cursor=i['id']
                while cursor and cursor not in needed:
                    needed.add(cursor);cursor=registry[cursor]['item']['parent']
        assert len(choices)==18
        assert [(c['population'],c['role'],c['item'],c['development']) for c in choices]==[(st['name'],c['role'],c['item'],c['development']) for st in states for c in st['nominees']]
        return dict(choices=dict(choices=choices,items=[items[i] for i in sorted(items)],historical_references=sources['historical_references'],control_ids=sources['control_ids'],chain=chain),
            ancestry={i:registry[i] for i in sorted(needed)},final_states=states),j.get('usage'),chain
    finally:j.close()

def approved():
    cfg=m.check();p=A1/'registration.json';assert p.exists(),'A1 is only a proposal; explicit user approval and published registration required'
    r=json.loads(p.read_text());assert r['user_approved'] and r['additional_evolution_rounds']==0 and r['selection_changes']==0
    for name,h in r['files'].items():assert m.sha(m.ROOT/name)==h,name
    m.pushed(p);return cfg

def rehearse():
    start=m.clock();cfg=m.check();e=failure_check();assert not (A1/'rehearsal.json').exists();target=A1/'rehearsal';assert not target.exists();target.mkdir(parents=True)
    journal=m.RUN/'search/campaign.sqlite';before=m.sha(journal)
    with m.writer_lock(m.RUN/'workflow'),m.writer_lock(m.RUN/'search'):
        payload,usage,chain=checkpoint();digests={k:m.hashed(m.packed(v)) for k,v in payload.items()}
        for key,value in payload.items():m.writez(target/(key+'.json.gz'),value);assert m.readz(target/(key+'.json.gz'))==value
        for st in payload['final_states']:
            for c in st['nominees']:
                try:dict(population=st['name'],role=c['role'],**c)
                except TypeError:pass
                else:raise AssertionError('Original duplicate-role regression not reproduced')
        try:approved()
        except AssertionError as err:assert 'only a proposal' in str(err)
        else:raise AssertionError('Unapproved apply guard failed')
    assert before==m.sha(journal)==e['journals']['search']['original']['sha256']
    elapsed=m.elapsed(start);assert e['original_search_wall_upper_seconds']+elapsed<cfg['session_wall_seconds']
    m.writej(A1/'rehearsal.json',dict(status='PASS',approval_required=True,exact_saved_nominees=18,unique_nominee_identities=len({c['item']['id'] for c in payload['choices']['choices']}),
        registry_closure=len(payload['ancestry']),semantic_payload_hashes=digests,chain=chain,usage_unchanged=usage,original_journal_byte_hash_unchanged=before,
        original_duplicate_role_error_reproduced=True,unapproved_apply_rejected=True,new_inference_calls=0,new_cases=0,new_generations=0,wall_seconds=elapsed,
        remaining_hard_search_export_seconds=cfg['session_wall_seconds']-e['original_search_wall_upper_seconds']-elapsed))
    print('Proposed A1 rehearsal PASS; zero evolution/inference/cases; original journal unchanged',flush=True)

def export():
    start=m.clock();cfg=approved();e=failure_check();r=json.loads((A1/'rehearsal.json').read_text());assert r['status']=='PASS'
    status=json.loads((m.RUN/'recovery_a1_workflow_status.json').read_text())
    assert status['state']=='running' and status['phase']=='export' and status['child_pid']==m.os.getpid() and status['pid']==m.os.getppid(),'Only the approved workflow holding the exclusive workflow lock may invoke export'
    assert not (A1/'export_receipt.json').exists() and not (m.OUT/'search_session.json').exists()
    assert all(not (m.OUT/n).exists() for n in ARTIFACTS)
    remaining=cfg['session_wall_seconds']-e['original_search_wall_upper_seconds']-r['wall_seconds'];bounded=dict(cfg,session_wall_seconds=remaining)
    # Parent recovery workflow owns workflow lock. Child owns only search lock;
    # attempting to reacquire the parent's flock here would correctly fail.
    with m.writer_lock(m.RUN/'search'):
        m.ensure(bounded,start);payload,usage,chain=checkpoint()
        assert {k:m.hashed(m.packed(v)) for k,v in payload.items()}==r['semantic_payload_hashes']
        for key,value in payload.items():m.ensure(bounded,start);m.writez(m.OUT/(key+'.json.gz'),value)
        m.ensure(bounded,start);charge=e['original_search_wall_upper_seconds']+r['wall_seconds']+m.elapsed(start)
        m.writej(m.OUT/'search_session.json',dict(status='complete',reason='soft_wall',generation=62,usage=usage,wall_seconds=charge,rss_peak_bytes=max(3565289472,m.shared._peak_rss),chain=chain,
            recovered_export_only=True,original_workflow_stays_failed=True,original_wall_upper_seconds=e['original_search_wall_upper_seconds'],rehearsal_seconds=r['wall_seconds'],
            timing_note='Conservative original subprocess interval plus read-only rehearsal and export work; inactive approval gap excluded. Original journal never changed.'))
    assert m.sha(m.RUN/'search/campaign.sqlite')==e['journals']['search']['original']['sha256']
    m.writej(A1/'export_receipt.json',dict(status='PASS',new_evolution_rounds=0,new_inference_calls=0,new_cases=0,nominees_unchanged=18,original_journal_byte_hash_unchanged=True,wall_seconds=m.elapsed(start),search_session_sha256=m.sha(m.OUT/'search_session.json'),
        artifact_hashes={n:m.sha(m.OUT/n) for n in ARTIFACTS},semantic_payload_hashes=r['semantic_payload_hashes']))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['rehearse','export']);a=p.parse_args();globals()[a.action]()
