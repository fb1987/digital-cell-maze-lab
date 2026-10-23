"""M25 complete transition/RNG/grade audit and frozen fresh confirmation."""
import argparse,json,time,sqlite3,hashlib,multiprocessing
from concurrent.futures import ProcessPoolExecutor
from collections import Counter,defaultdict
from .skill_integration import OUT,RUN,ROOT,check,pushed,writej,readz,writez,organism,evaluate_task,resource_reason,controls,task_specs,load_layouts,clock,elapsed
from .skill_integration_search import transition
from .skill_integration_checkpoint import founders
from . import skill_integration_data as data_builder
from .deep_campaign_store import unpacked,packed,hashed,writer_lock
from .referenced_campaign_store import Journal
from . import deep_campaign as shared
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import record
from .foundation_pair_confirm import normal_row
from .routing_transfer import canonical,sha
from .skill_integration_data import confirmation
from .deep_confirmation_analysis import capabilities,compare
from .baselines import baseline


def selected_replay(key,cid,divisor):return int(hashlib.sha256((key+'/'+cid).encode()).hexdigest(),16)%divisor==0


def audit_search():
    config=check();t=clock();j=Journal(RUN);chain=j.verify_chain()
    assert j.get('finished') and not j.pending() and j.state()[0]['generation']==j.get('nomination_stop')['generation'] and j.state()[0]['assessment_generation']==j.state()[0]['generation']
    assert not (OUT/'search_audit.json').exists()
    assert j.state()[0]['generation']<=config['max_rounds']
    states=readz(OUT/'founders.json.gz');assert states==founders(config['seed'])
    inherited_roots={i['root'] for s in states for i in s['population']+s['archive']+s['protected']}
    assert states[0]['generation']==config['start_generation']
    previous=load_layouts(ROOT/config['layout_base_manifest']);validation=None;grades=replays=births=stages=0
    exposure=defaultdict(Counter);variation=defaultdict(Counter);copy_survival=defaultdict(Counter);recent_births={}
    exploration_counts=defaultdict(Counter);logical=defaultdict(Counter);birth_allocation=defaultdict(Counter);reserved=defaultdict(Counter)
    for n,blob,decision,expected_state_hash in j.db.execute('select n,input,decision,state_hash from stages where complete=1 order by n'):
        assert resource_reason(RUN,dict(config,session_wall_seconds=config['audit_wall_seconds']),t) is None,'Audit resource guard'
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
        stage_logical=Counter()
        for task in task_specs(states,data):
            for e in task:
                for k,identity in e['aliases']:stage_logical[k]+=len(e['queries'])
        expected_queries=115*392 if data['kind']=='assessment' else 96*120
        assert stage_logical==Counter({k:expected_queries for k in range(6)}),(n,'equal nominal allocations')
        for k,count in stage_logical.items():logical[states[k]['name']][data['kind']]+=count
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
        if data['kind']=='train':
            from .skill_integration_search import PARENT
            from .breeding_allocation_metrics import capabilities_plus
            for result in results:
                for entry in result['entries']:
                    for k,identity in entry['aliases']:
                        if identity!=PARENT:continue
                        cap=capabilities_plus(entry['rows'],data['metadata'])
                        for label,wanted in [('fresh',set(data['common_queries'])),('persistent',set(data['persistent_queries'][states[k]['curriculum']]))]:
                            subset=[r for r in entry['rows'] if r['case'] in wanted]
                            subcap=capabilities_plus(subset,data['metadata'])
                            exposure[states[k]['name']][label+'_parent_successful_ordinary_presentations']+=len(subcap['ordinary_bases'])
                            exposure[states[k]['name']][label+'_ordinary_base_presentations']+=len({data['metadata'][r['case']]['base'] for r in subset if data['metadata'][r['case']]['family'] in ('ordinary_perfect','ordinary_random')})
                        exposure[states[k]['name']]['parent_successful_ordinary_bases']+=len(cap['ordinary_bases'])
                        exposure[states[k]['name']]['parent_complete_pairs']+=len(cap['pairs'])
                        seen_bases=set()
                        for row in entry['rows']:
                            m=data['metadata'][row['case']]
                            if m['family'] not in ('ordinary_perfect','ordinary_random') or m['base'] in seen_bases:continue
                            seen_bases.add(m['base'])
                            domain=f"{m['family']}/{m['size']}/{m['length_bin']}"
                            exposure[states[k]['name']]['exposed/'+domain]+=1
                            if m['base'] in cap['ordinary_bases']:exposure[states[k]['name']]['parent_success/'+domain]+=1
        states,events=transition(states,data,results)
        for event in events:
            if 'survivors' in event:
                survivors=set(event['survivors'])
                for identity,kind in recent_births.get(event['name'],[]):
                    copy_survival[event['name']][kind+'/presentations']+=1
                    copy_survival[event['name']][kind+'/survive_next_train']+=identity in survivors
                recent_births[event['name']]=[(b['item']['id'],b['events'][0]['kind']) for b in event['births'] if b['events']]
            for birth in event['births']:
                for edit in birth['events']:
                    variation[event['name']]['kind/'+edit['kind']]+=1
                    variation[event['name']]['bucket/'+str(edit['opportunity'])]+=1
                    variation[event['name']]['tuning_fallback']+=bool(edit['tuning_fallback'])
                    variation[event['name']]['wrapper_presentations']+=edit['recognized_wrappers']
                    variation[event['name']]['genotype_noop']+=edit['before']==edit['after']

        assert events==unpacked(decision) and hashed(packed(states))==expected_state_hash,(n,'selection/RNG')
        births+=sum(len(e['births']) for e in events);stages+=1
        for event in events:
            if 'exploration' in event:
                exploration_counts[event['name']]['selected_explorer_presentations']+=len(event['explorer_ids'])
                exploration_counts[event['name']]['training_stages_with_explorers']+=int(bool(event['explorer_ids']))
                exploration_counts[event['name']]['eligible_behavior_cells']+=event['exploration'].get('quality_eligible_distinct_cells',0)
            for b in event['births']:
                exploration_counts[event['name']][b['parent_policy']]+=1
                if b['events']:
                    root=b['item']['root'];category=root if root in inherited_roots else 'M25_new_random_origin'
                    birth_allocation[event['name']][category]+=1
                    reserved[event['name']][b['events'][0]['operator']]+=1
        if n%16==0:print('AUDIT',n,grades,replays,flush=True)
    assert states==j.state() and previous==j.layouts()
    from . import skill_integration as runner
    frozen={};original_writez=runner.writez;original_layouts=runner.write_layouts
    try:
        runner.writez=lambda path,value:frozen.__setitem__(path,canonical(value))
        runner.write_layouts=lambda name,value:frozen.__setitem__(OUT/(name+'.json'),set(value))
        runner.freeze(j,guard=lambda:resource_reason(RUN,dict(config,session_wall_seconds=config['audit_wall_seconds']),t))
    finally:runner.writez=original_writez;runner.write_layouts=original_layouts
    for path,value in frozen.items():assert (load_layouts(path) if isinstance(value,set) else readz(path))==value,(str(path),'frozen artifacts')
    usage=j.get('usage');assert grades<=usage['calls']
    assert usage['uncertain_attempts'] or grades==usage['calls']
    result=dict(status='PASS',chain=chain,stages=stages,independent_grades=grades,native_replays=replays,births_replayed=births,
        variation_counts={k:dict(v) for k,v in variation.items()},immediate_birth_survival={k:dict(v) for k,v in copy_survival.items()},exploration_allocation_counts={k:dict(v) for k,v in exploration_counts.items()},logical_query_counts={k:dict(v) for k,v in logical.items()},training_retention_opportunities={k:dict(v) for k,v in exposure.items()},mutation_births_per_root={k:dict(v) for k,v in birth_allocation.items()},reserved_birth_counts={k:dict(v) for k,v in reserved.items()},equal_nominal_allocations=True,
        charged_calls=usage['calls'],uncertain_attempts=usage['uncertain_attempts'],deterministic_corpora=True,all_selection_mutation_rng=True,frozen_artifacts_verified=True,source_hashes=True,wall_seconds=elapsed(t),
        limitation='Shared production reproduction and native runtime replay; independent raster grader, not a second full VM.')
    writej(OUT/'search_audit.json',result);j.close();print(json.dumps(result,indent=2))


def final_specs(choices,ids):
    models={}
    for identity,i in choices['items'].items():
        m=dict(representation=choices['representations'][identity],genome=i['genome']);k=hashed(packed(m))
        models.setdefault(k,dict(model=m,queries=ids,aliases=[]))['aliases'].append(identity)
    for c in choices.get('comparison_archive',[])+choices['controls']:
        m=dict(representation=c['representation'],genome=c['genome']);k=hashed(packed(m))
        models.setdefault(k,dict(model=m,queries=ids,aliases=[]))['aliases'].append(c['id'])
    return [[models[k]] for k in sorted(models)]


def final():
    config=check();pushed(OUT/'choices.json.gz');choices=readz(OUT/'choices.json.gz')
    assert json.loads((OUT/'search_audit.json').read_text())['status']=='PASS'
    directory=RUN/'final';directory.mkdir(exist_ok=True);previous=load_layouts(OUT/'search_exclusions.json');started=clock()
    shared.evaluate_task=evaluate_task;shared.resource_reason=lambda directory,c,t:resource_reason(RUN,c,t)
    # This separate allowance is declared in the protocol; it does not restart training.
    final_config=dict(config,layout_base_manifest=str(OUT/'search_exclusions.json'),phase='M25-final',session_wall_seconds=900,call_cap=1000000,work_cap=10**14)
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
        writej(OUT/'final_session.json',dict(status='checkpoint' if reason else 'complete',reason=reason,usage=j.get('usage'),wall_seconds=elapsed(started),rss_peak_bytes=shared._peak_rss));j.close()
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
    from .skill_integration_metrics import build_summary
    return build_summary(readz(OUT/'choices.json.gz'),data,rows,usage,chain)


def analyze():
    assert not (OUT/'summary.json').exists()
    check();data,rows,models,usage,chain=final_load();result=compute_summary(data,rows,usage,chain)
    writej(OUT/'summary.json',result);writez(OUT/'final_responses.json.gz',dict(rows=rows,models=models))
    print(json.dumps(dict(models=len(models),queries=result['queries'],passing_nominees=sum(c['upstream_acquisition'] for c in result['conditions'])),indent=2))


def audit_final():
    assert not (OUT/'final_audit.json').exists()
    config=check();t=clock();data,rows,models,usage,chain=final_load()
    assert [e for e,rs in models]==[t[0] for t in final_specs(readz(OUT/'choices.json.gz'),data['queries']['all'])]
    for identity,rs in rows.items():
        if identity.startswith('control/'):assert all(r['optimal'] or r['no_path'] for r in rs)
    expected=confirmation(config['confirmation_seed'],load_layouts(OUT/'search_exclusions.json'))
    assert canonical(expected)==data
    cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in data['queries']['all']]);checker=Checker(cases);replays=0
    for e,rs in models:
        assert resource_reason(RUN,dict(config,session_wall_seconds=config['audit_wall_seconds']),t) is None,'Audit resource guard'
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
    result=dict(status='PASS',source_and_corpus_hashes=True,independent_candidate_grades=usage['calls'],native_replays=replays,conventional_calls=3*len(cases),wall_seconds=elapsed(t),metrics_recomputed=True)
    writej(OUT/'final_audit.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['audit_search','final','analyze','audit_final']);a=p.parse_args()
    if a.action in ('audit_search','audit_final'):
        with writer_lock(RUN if a.action=='audit_search' else RUN/'final'):globals()[a.action]()
    else:globals()[a.action]()
