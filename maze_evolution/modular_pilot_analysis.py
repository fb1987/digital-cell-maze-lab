"""M1 frozen analysis, sampled native audit and untouched final comparison."""
import argparse,json,time,sqlite3,hashlib,multiprocessing
from concurrent.futures import ProcessPoolExecutor
from collections import Counter,defaultdict
from .modular_pilot import OUT,RUN,ROOT,check,pushed,writej,readz,writez,organism,evaluate_task,resource_reason,controls
from .modular_pilot_search import transition,founders
from . import modular_pilot_data as data_builder
from .deep_campaign_store import Journal,unpacked,packed,hashed,writer_lock
from . import deep_campaign as shared
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import record
from .foundation_pair_confirm import normal_row
from .routing_transfer import canonical,sha
from .reboot_data import confirmation
from .deep_confirmation_analysis import capabilities,compare
from .baselines import baseline


def selected_replay(key,cid,divisor):return int(hashlib.sha256((key+'/'+cid).encode()).hexdigest(),16)%divisor==0


def audit_search():
    config=check();t=time.monotonic();j=Journal(RUN);chain=j.verify_chain()
    assert not j.pending() and j.state()[0]['generation']==config['rounds'] and j.state()[0]['assessment_generation']==config['rounds']
    states=readz(OUT/'founders.json.gz');assert states==founders(config['seed'])
    previous=set(readz(OUT/'exclusions.json.gz')['hashes']);validation=None;grades=replays=births=stages=0
    for n,blob,decision,expected_state_hash in j.db.execute('select n,input,decision,state_hash from stages where complete=1 order by n'):
        data=unpacked(blob)
        if data['kind']=='assessment':
            if validation is None:validation=data_builder.validation(config['validation_seed'],previous)
            regenerated=canonical(validation.copy());regenerated['generation']=data['generation']
            if data['generation']:regenerated['new_layouts']=[]
        else:regenerated=data_builder.training(config['seed'],data['generation'],previous)
        assert canonical(regenerated)==data,(n,'corpus')
        previous.update(data['new_layouts']);ids={c for q in data['queries'].values() for c in q}
        cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in ids]);checker=Checker(cases)
        results=[]
        for spec,result,h in j.db.execute('select spec,result,result_hash from tasks where stage=? order by n',(n,)):
            assert hashed(result)==h;result=unpacked(result);spec=unpacked(spec);results.append(result)
            assert len(spec)==len(result['entries'])
            for e,r in zip(spec,result['entries']):
                assert e['aliases']==r['aliases'] and e['queries']==[x['case'] for x in r['rows']]
                org=organism(e['model']);key=hashed(packed(e['model']))
                for row in r['rows']:
                    checker.row(row);grades+=1
                    if selected_replay(key,row['case'],32 if data['kind']=='assessment' else 256):
                        o=cases[row['case']];m=o.maze;actual=record(org.react(m.cells,m.w,m.h,m.start,m.goal),o)
                        assert actual==row,(n,e['aliases'],row['case']);replays+=1
        states,events=transition(states,data,results)
        assert events==unpacked(decision) and hashed(packed(states))==expected_state_hash,(n,'selection/RNG')
        births+=sum(len(e['births']) for e in events);stages+=1
        if n%16==0:print('AUDIT',n,grades,replays,flush=True)
    assert states==j.state() and previous==j.layouts()
    usage=j.get('usage');assert usage['uncertain_attempts']==0
    assert grades==usage['calls']
    result=dict(status='PASS',chain=chain,stages=stages,independent_grades=grades,native_replays=replays,births_replayed=births,
        deterministic_corpora=True,all_selection_mutation_rng=True,source_hashes=True,wall_seconds=time.monotonic()-t,
        limitation='Shared production reproduction and native runtime replay; independent raster grader, not a second full VM.')
    writej(OUT/'search_audit.json',result);j.close();print(json.dumps(result,indent=2))


def final_specs(choices,ids):
    models={}
    for identity,i in choices['items'].items():
        m=dict(representation=choices['representations'][identity],genome=i['genome']);k=hashed(packed(m))
        models.setdefault(k,dict(model=m,queries=ids,aliases=[]))['aliases'].append(identity)
    for c in choices['controls']:
        m=dict(representation=c['representation'],genome=c['genome']);k=hashed(packed(m));assert k not in models
        models[k]=dict(model=m,queries=ids,aliases=[c['id']])
    return [[models[k]] for k in sorted(models)]


def final():
    config=check();pushed(OUT/'choices.json.gz');choices=readz(OUT/'choices.json.gz')
    assert json.loads((OUT/'search_audit.json').read_text())['status']=='PASS'
    directory=RUN/'final';directory.mkdir(exist_ok=True);previous=set(readz(OUT/'search_exclusions.json.gz')['hashes']);started=time.monotonic()
    shared.evaluate_task=evaluate_task;shared.resource_reason=lambda directory,c,t:resource_reason(RUN,c,t)
    # This separate allowance is declared in the protocol; it does not restart training.
    final_config=dict(config,phase='M1-final',call_cap=1000000,work_cap=10**14)
    with writer_lock(directory):
        j=Journal(directory);j.initialize(final_config,dict(choices_sha256=sha(OUT/'choices.json.gz')),previous);j.verify_chain()
        if j.get('latest')>=0:j.close();print('Already complete');return
        pending=j.pending()
        if pending:n,data=pending
        else:
            data=confirmation(config['confirmation_seed'],previous);data['queries']={'all':data['queries']};writez(OUT/'confirmation.json.gz',data)
            tasks=final_specs(choices,data['queries']['all']);assert sum(len(e['queries']) for t in tasks for e in t)<=final_config['call_cap']
            n=j.prepare(data,tasks)
        assert [s for _,s,_ in j.tasks(n)]==final_specs(choices,data['queries']['all'])
        with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as pool:
            reason=shared.run_stage(j,n,data,pool,final_config,started,[False])
        if not reason:j.commit(n,j.state(),dict(no_reselection=True))
        writej(OUT/'final_session.json',dict(status='checkpoint' if reason else 'complete',reason=reason,usage=j.get('usage'),wall_seconds=time.monotonic()-started,rss_peak_bytes=shared._peak_rss));j.close()
        print('FINAL',reason or 'complete',flush=True)


def final_load():
    j=Journal(RUN/'final');chain=j.verify_chain();assert j.get('latest')==0
    data=unpacked(j.db.execute('select input from stages where n=0').fetchone()[0]);rows={};models=[]
    for spec,result in j.db.execute('select spec,result from tasks where stage=0 order by n'):
        e=unpacked(spec)[0];r=unpacked(result)['entries'][0];assert e['aliases']==r['aliases']
        for identity in e['aliases']:rows[identity]=r['rows']
        models.append((e,r['rows']))
    usage=j.get('usage');j.close();return data,rows,models,usage,chain


def compute_summary(data,rows,usage,chain):
    choices=readz(OUT/'choices.json.gz');meta=data['metadata'];caps={i:capabilities(rs,meta) for i,rs in rows.items()}
    summaries=[]
    for c in choices['comparisons']:
        a=caps[c['child']];vs=compare(a,caps[c['root']],meta)
        ordinary_retained=len(a['ordinary_bases']&caps[c['root']]['ordinary_bases'])/len(caps[c['root']]['ordinary_bases']) if caps[c['root']]['ordinary_bases'] else None
        vs['ordinary_retention']=ordinary_retained
        vs['evolved_acquisition']=bool(c['mutations'] and vs['acquisition_gate'])
        vs['broad_acquisition']=bool(c['mutations'] and vs['broad_transfer_flag'] and (ordinary_retained is None or ordinary_retained>=.9))
        frozen=[identity for identity,rs in choices['roles'].items() if [c['condition'],'frozen',c['rank']] in rs];assert len(frozen)==1
        summaries.append(dict(**c,metrics=a['summary'],versus_root=vs,versus_parent=compare(a,caps[c['parent']],meta) if c['parent'] else None,
            frozen_reference=frozen[0],versus_frozen=compare(a,caps[frozen[0]],meta)))
    # Describe predeclared replicate screens; no inferential claim from three replicates.
    gates=[]
    by={(s['condition'],s['rank']):s for s in summaries}
    for rep in ('flat','modular'):
        for curriculum in ('familiar','broad'):
            passed=[]
            for r in range(3):
                ok=False
                for rank in (0,1):
                    a=by[(f'{rep}/{r}/{curriculum}/mutation',rank)];b=by[(f'{rep}/{r}/{curriculum}/resample',rank)]
                    ok|=a['versus_root']['broad_acquisition'] and a['versus_frozen']['new_ordinary_bases']-a['versus_frozen']['lost_ordinary_bases']>=4 and a['metrics']['ordinary_bases_both_poses']>=b['metrics']['ordinary_bases_both_poses']+4 and a['metrics']['false_no_path']<=b['metrics']['false_no_path']
                passed.append(bool(ok))
            gates.append(dict(representation=rep,curriculum=curriculum,replicate_passes=passed,scale_screen=sum(passed)>=2))
    return dict(status='evaluated',independent_confirmation=True,chain=chain,usage=usage,queries=len(data['queries']['all']),conditions=summaries,
        scale_screens=gates,controls={i:caps[i]['summary'] for i in caps if i.startswith('control/')},
        limitation='Three fresh replicate founders per representation, shared paired evaluation panels; representation and mutation are a package. No causal private-memory claim, general solver or speedup claim.')


def analyze():
    check();data,rows,models,usage,chain=final_load();result=compute_summary(data,rows,usage,chain)
    writej(OUT/'summary.json',result);writez(OUT/'final_responses.json.gz',dict(rows=rows,models=models))
    print(json.dumps(dict(models=len(models),queries=result['queries'],gates=result['scale_screens']),indent=2))


def audit_final():
    config=check();t=time.monotonic();data,rows,models,usage,chain=final_load()
    expected=confirmation(config['confirmation_seed'],set(readz(OUT/'search_exclusions.json.gz')['hashes']));expected['queries']={'all':expected['queries']}
    assert canonical(expected)==data
    cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in data['queries']['all']]);checker=Checker(cases);replays=0
    for e,rs in models:
        org=organism(e['model']);key=hashed(packed(e['model']))
        for row in rs:
            checker.row(row)
            if e['aliases'][0].startswith('control/') or selected_replay(key,row['case'],32):
                o=cases[row['case']];m=o.maze;assert record(org.react(m.cells,m.w,m.h,m.start,m.goal),o)==row;replays+=1
    baseline_rows={}
    for name in ('compiled_bfs','compiled_astar','wave_bit'):
        rs=[]
        for o in cases.values():
            m=o.maze;r=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));checker.row(r);assert r['optimal'] or r['no_path'];rs.append(r)
        baseline_rows[name]=rs
    writez(OUT/'baselines.json.gz',baseline_rows)
    assert canonical(compute_summary(data,rows,usage,chain))==json.loads((OUT/'summary.json').read_text())
    result=dict(status='PASS',source_and_corpus_hashes=True,independent_candidate_grades=usage['calls'],native_replays=replays,conventional_calls=3*len(cases),wall_seconds=time.monotonic()-t,metrics_recomputed=True)
    writej(OUT/'final_audit.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['audit_search','final','analyze','audit_final']);a=p.parse_args();globals()[a.action]()
