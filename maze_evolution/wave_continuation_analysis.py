"""M3 bounded-search audit and frozen longer-route confirmation."""
import argparse,json,time,sqlite3,hashlib,multiprocessing
from concurrent.futures import ProcessPoolExecutor
from collections import Counter,defaultdict
from .wave_continuation import OUT,RUN,ROOT,check,pushed,writej,readz,writez,organism,evaluate_task,resource_reason,controls,task_specs
from .wave_continuation_search import transition,founders
from . import wave_continuation_data as data_builder
from .deep_campaign_store import Journal,unpacked,packed,hashed,writer_lock
from . import deep_campaign as shared
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import record
from .foundation_pair_confirm import normal_row
from .routing_transfer import canonical,sha
from .wave_continuation_data import confirmation
from .deep_confirmation_analysis import capabilities,compare
from .baselines import baseline


def selected_replay(key,cid,divisor):return int(hashlib.sha256((key+'/'+cid).encode()).hexdigest(),16)%divisor==0


def audit_search():
    config=check();t=time.monotonic();j=Journal(RUN);chain=j.verify_chain()
    assert j.get('finished') and not j.pending() and j.state()[0]['generation']==j.get('nomination_stop')['generation'] and j.state()[0]['assessment_generation']==j.state()[0]['generation']
    assert not (OUT/'search_audit.json').exists()
    assert j.state()[0]['generation']<=config['max_rounds']
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
        assert [unpacked(r[0]) for r in j.db.execute('select spec from tasks where stage=? order by n',(n,))]==task_specs(states,data),(n,'task_specs')
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
    usage=j.get('usage');assert grades<=usage['calls']
    assert usage['uncertain_attempts'] or grades==usage['calls']
    result=dict(status='PASS',chain=chain,stages=stages,independent_grades=grades,native_replays=replays,births_replayed=births,
        charged_calls=usage['calls'],uncertain_attempts=usage['uncertain_attempts'],deterministic_corpora=True,all_selection_mutation_rng=True,source_hashes=True,wall_seconds=time.monotonic()-t,
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
    final_config=dict(config,phase='M3-final',call_cap=1000000,work_cap=10**14)
    with writer_lock(directory):
        j=Journal(directory);j.initialize(final_config,dict(choices_sha256=sha(OUT/'choices.json.gz')),previous);j.verify_chain()
        if j.get('latest')>=0:j.close();print('Already complete');return
        pending=j.pending()
        if pending:n,data=pending
        else:
            data=confirmation(config['confirmation_seed'],previous);writez(OUT/'confirmation.json.gz',data)
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


def complex_sets(cap,meta):
    pair_meta={(m['base'],m['pose']):m for m in meta.values() if m['family']=='paired'}
    ordinary_meta={m['base']:m for m in meta.values() if m['family'].startswith('ordinary_')}
    return dict(hard_pairs={p for p in cap['pairs'] if pair_meta[p]['prefix']>=2 or pair_meta[p]['graph']!='fork'},
        multi_pairs={p for p in cap['pairs'] if pair_meta[p]['graph']!='fork'},
        long_bases={b for b in cap['ordinary_bases'] if len(ordinary_meta[b]['path'])-1>=8})


def compute_summary(data,rows,usage,chain):
    choices=readz(OUT/'choices.json.gz');meta=data['metadata'];caps={i:capabilities(rs,meta) for i,rs in rows.items()}
    length_strata={}
    for identity,rs in rows.items():
        groups=defaultdict(set)
        for row in rs:
            m=meta[row['case']]
            if m['family'] in ('ordinary_perfect','ordinary_random'):
                groups[f"{m['family']}/{m['size']}/{m['length_bin']}"].add(m['base'])
        length_strata[identity]={key:dict(bases=len(bases),correct_both_poses=len(bases & caps[identity]['ordinary_bases'])) for key,bases in groups.items()}
    protected={i for i,roles in choices['roles'].items() if any(r[1]=='protected' for r in roles)}
    union={k:set().union(*(caps[i][k] for i in protected)) for k in ('pairs','corridors','ordinary_bases','false','success')}
    uc=complex_sets(union,meta);summaries=[]
    pair_meta={(m['base'],m['pose']):m for m in meta.values() if m['family']=='paired'}
    ordinary_meta={m['base']:m for m in meta.values() if m['family'].startswith('ordinary_')}
    for c in choices['comparisons']:
        cap=caps[c['child']];root=caps[c['root']];vs=compare(cap,root,meta);sets=complex_sets(cap,meta)
        rc=complex_sets(root,meta)
        newhard=sets['hard_pairs']-uc['hard_pairs']-rc['hard_pairs'];newlong=sets['long_bases']-uc['long_bases']-rc['long_bases'];newmulti=sets['multi_pairs']-uc['multi_pairs']-rc['multi_pairs']
        retention={k:len(cap[k]&root[k])/len(root[k]) if root[k] else None for k in ('pairs','corridors','ordinary_bases')}
        preserved=all(v is None or v>=.9 for v in retention.values()) and len(cap['false'])<=len(root['false'])
        contexts={pair_meta[p]['template'] for p in newhard}
        families={ordinary_meta[b]['family'] for b in newlong}
        long16=sum(len(ordinary_meta[b]['path'])-1>=16 for b in newlong)
        hard_gate=bool(c['mutations'] and preserved and len(newhard)>=8 and len(contexts)>=2)
        ordinary_gate=bool(c['mutations'] and preserved and len(newlong)>=4 and long16>=1 and {'ordinary_perfect','ordinary_random'}<=families)
        frozen=[i for i,roles in choices['roles'].items() if [c['condition'],'frozen',c['rank']] in roles];assert len(frozen)==1
        summaries.append(dict(**c,metrics=cap['summary'],versus_root=vs,root_retention=retention,
            versus_parent=compare(cap,caps[c['parent']],meta) if c['parent'] else None,
            frozen_reference=frozen[0],versus_frozen=compare(cap,caps[frozen[0]],meta),
            beyond_protected_union=dict(reference='new relative to BOTH exact M3 root and protected union',new_hard_pairs=len(newhard),new_contexts=len(contexts),new_multi_pairs=len(newmulti),
                new_long_bases=len(newlong),new_long16_bases=long16,new_long_by_domain=dict(Counter(ordinary_meta[b]['family']+'/'+str(ordinary_meta[b]['size']) for b in newlong)),
                new_hard_keys=sorted(newhard),new_long_keys=sorted(newlong)),
            hard_pair_acquisition=hard_gate,long_ordinary_acquisition=ordinary_gate,substantial_transfer=hard_gate and ordinary_gate and len(newmulti)>=4))
    by={(c['condition'],c['rank']):c for c in summaries};replicates=[]
    for rep in range(3):
        passes=[]
        for rank in (0,1):
            a=by[(f'modular/{rep}/mixed',rank)];b=by[(f'modular/{rep}/single',rank)]
            x=a['beyond_protected_union'];y=b['beyond_protected_union']
            passes.append(bool((a['hard_pair_acquisition'] and x['new_hard_pairs']>=y['new_hard_pairs']+8 or
                a['long_ordinary_acquisition'] and x['new_long_bases']>=y['new_long_bases']+4) and a['metrics']['false_no_path']<=b['metrics']['false_no_path']))
        replicates.append(any(passes))
    return canonical(dict(status='evaluated',independent_confirmation=True,chain=chain,usage=usage,queries=len(data['queries']['all']),
        conditions=summaries,mixed_replicate_screen=replicates,mixed_scale_screen=sum(replicates)>=2,
        protected_identities=sorted(protected),all_models={i:c['summary'] for i,c in caps.items()},ordinary_length_strata=length_strata,
        limitation='Replicates share six protected genomes and historical M2 source lineages; independent mutation histories, not independent origins. Fixed panel poses and variants correlate. No general-solver or speed claim.'))


def analyze():
    assert not (OUT/'summary.json').exists()
    check();data,rows,models,usage,chain=final_load();result=compute_summary(data,rows,usage,chain)
    writej(OUT/'summary.json',result);writez(OUT/'final_responses.json.gz',dict(rows=rows,models=models))
    print(json.dumps(dict(models=len(models),queries=result['queries'],mixed_replicate_screen=result['mixed_replicate_screen']),indent=2))


def audit_final():
    assert not (OUT/'final_audit.json').exists()
    config=check();t=time.monotonic();data,rows,models,usage,chain=final_load()
    expected=confirmation(config['confirmation_seed'],set(readz(OUT/'search_exclusions.json.gz')['hashes']))
    assert canonical(expected)==data
    cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in data['queries']['all']]);checker=Checker(cases);replays=0
    for e,rs in models:
        org=organism(e['model']);key=hashed(packed(e['model']))
        for row in rs:
            checker.row(row)
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
