"""M20 bounded copy-specialization assay, durable and separately registered."""
import argparse,json,random,time,sqlite3,shutil,multiprocessing,hashlib
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz,compressed_json as writez
from .deep_confirmation import writej
from .routing_transfer import sha,canonical
from .deep_campaign_store import writer_lock,packed,unpacked,hashed
from .referenced_campaign_store import Journal,load_layouts,write_reference
from . import deep_campaign as shared
from .connected_evolution import controls,pushed
from .connected_evaluation import organism,evaluate_task
from .specialization_genome import make_pool,Genome
from .specialization_metrics import nominate,summarize
from .restoration_data import screen,confirmation
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import record

OUT=ROOT/'results/copy_specialization';RUN=ROOT/'runs/copy_specialization_m20'
PRIOR=ROOT/'results/connected_evolution';DIAG=ROOT/'results/connected_history_diagnosis'
CONFIG=dict(phase='M20',pool_seed=2026102212,screen_seed=2026102213,final_seed=2026102214,
    fixture_seed=202610221280,draws_per_anchor=512,workers=10,
    call_cap=2000000,work_cap=10**13,session_wall_seconds=1800,final_wall_seconds=900,
    audit_wall_seconds=1800,memory_bytes=8*2**30,storage_bytes=6*2**30,disk_free_floor_bytes=16*2**30,
    layout_base_manifest='results/copy_specialization/exclusions.json')


def verify_prior():
    result={}
    for directory in (PRIOR,DIAG):
        seal=json.loads((directory/'completion.json').read_text())
        for p,h in seal['files'].items():assert sha(ROOT/p)==h,p
        for p,e in seal.get('local_records',{}).items():assert sha(ROOT/p)==e['sha256'],p
        result[str(directory.relative_to(ROOT))]=dict(files=len(seal['files']),local_records=len(seal.get('local_records',{})),sha256=sha(directory/'completion.json'))
    return result


def check():
    r=json.loads((OUT/'registration.json').read_text())
    for p,h in r['files'].items():assert sha(ROOT/p)==h,p
    now=shared.source_manifest();assert all(r[k]==now[k] for k in ('python','dependencies'))
    verify_prior();return json.loads((OUT/'config.json').read_text())


def references(sources):
    refs=[dict(id='anchor/'+k,kind='reference',model=dict(representation='connected',genome=v['genome']),source=v['id']) for k,v in sources['anchors'].items()]
    refs += [dict(id=i,kind='protected',model=dict(representation='connected',genome=v['genome']),source=i) for i,v in sources['protected'].items()]
    refs += [dict(id=c['id'],kind='control',model={k:c[k] for k in ('representation','genome')}) for c in controls()]
    return refs


def tasks(items,ids):
    grouped={}
    for i in items:
        h=hashed(packed(i['model']));grouped.setdefault(h,dict(model=i['model'],queries=ids,aliases=[]))['aliases'].append(i['id'])
    values=[grouped[h] for h in sorted(grouped)]
    return [values[n:n+4] for n in range(0,len(values),4)]


def guard(directory,config,started):
    if time.monotonic()-started>=config['session_wall_seconds']:return 'wall'
    if shared.process_resources()>=config['memory_bytes']:return 'memory'
    if shutil.disk_usage(RUN).free<config['disk_free_floor_bytes']:return 'disk_free'
    if sum(p.stat().st_size for base in (RUN,OUT) for p in base.rglob('*') if p.is_file())>=config['storage_bytes']:return 'storage'


def prepare():
    assert not OUT.exists();prior=verify_prior();OUT.mkdir();RUN.mkdir(parents=True,exist_ok=True)
    assert shutil.disk_usage(RUN).free>=CONFIG['disk_free_floor_bytes']+CONFIG['storage_bytes']
    states=readz(PRIOR/'founders.json.gz');protected={i['id']:i for i in states[0]['protected']}
    assert len(protected)==13
    registry=readz(PRIOR/'inherited_registry.json.gz')
    anchors={name:dict(id=i,genome=protected[i]['genome'],inherited_record=registry[i]) for name,i in
        [('parent','m14/reference/gated_specialist'),('child','m14/modular/1/explore/g320/b48')]}
    sources=dict(anchors=anchors,protected=protected,source_study='Preserved M15 specialist and actual parent, embedded unchanged in M18 at M19 entry',
        prior=prior,old_histories_untouched=True)
    writez(OUT/'sources.json.gz',sources);writej(OUT/'config.json',CONFIG)
    write_reference(OUT/'exclusions.json',PRIOR/'whole_layout_exclusions.json',load_layouts(PRIOR/'whole_layout_exclusions.json'))


def fixture_sources():
    from .modular_genome import Genome as Base
    from .connected_genome import embed
    from .regulatory import Gene
    anchors={}
    for k in ('parent','child'):
        blocks=[(Gene(0,12,n,0,0,0,64),) for n in range(8)]
        if k=='child':blocks[2]=(Gene(0,12,1,0,0,0,64),)
        g=embed(Base(tuple(blocks),(tuple(range(8)),)*8))
        anchors[k]=dict(id='fake/'+k,genome=g.to_dict())
    return dict(anchors=anchors,protected={'m14/reference/anchor/0':anchors['parent']})


def fixture_evaluate(items,data):
    ids=data['queries']['all'];mazes=[m for m in data['mazes'] if m['case_id'] in ids]
    receipts=[evaluate_task(t,mazes,'m20fixture/'+hashed(packed(ids))) for t in tasks(items,ids)]
    rows={i:e['rows'] for r in receipts for e in r['entries'] for i in e['aliases']}
    return receipts,rows


def selected_items(items,nominations):
    lookup={i['id']:i for i in items};wanted={n['identity'] for n in nominations}
    wanted|={lookup[i]['copy_base'] for i in list(wanted)}
    wanted|={i['id'] for i in items if i['kind'] in ('reference','protected','control')}
    return [lookup[i] for i in sorted(wanted)]


def preflight():
    assert not (OUT/'registration.json').exists() and not (OUT/'preflight.json').exists()
    t=time.monotonic();sources=fixture_sources();p=make_pool(sources,CONFIG['fixture_seed'],2)
    assert p==make_pool(sources,CONFIG['fixture_seed'],2)
    items=p['items']+references(sources)
    data=readz(ROOT/'results/restoration_assay/discarded_corpus_fixture.json.gz')
    # Reuse every discarded fixture case, not scientific or fresh cases.
    receipts,rows=fixture_evaluate(items,data);ns=nominate(items,rows,data,list(sources['protected']))
    final_items=selected_items(items,ns['nominations'])
    final=readz(PRIOR/'final_fixture.json.gz')
    excluded=load_layouts(OUT/'exclusions.json')
    assert set(data['new_layouts'])<=excluded and set(final['new_layouts'])<=excluded
    rr,fr=fixture_evaluate(final_items,final);summary=summarize(final_items,ns['nominations'],fr,final,list(sources['protected']))
    assert summary==summarize(final_items,ns['nominations'],fr,final,list(sources['protected']))
    grades=replays=0
    for data0,rs in ((data,rows),(final,fr)):
        cases=cases_from_manifest([m for m in data0['mazes'] if m['case_id'] in data0['queries']['all']]);checker=Checker(cases)
        for i in controls():assert all(r['optimal'] or r['no_path'] for r in rs[i['id']])
        # All fixture rows independently checked; fixed native sample tests replay path.
        lookup={i['id']:i for i in (items if rs is rows else final_items)}
        for identity,records in rs.items():
            org=organism(lookup[identity]['model'])
            for r in records:
                checker.row(r);grades+=1
                if int(hashlib.sha256((identity+'/'+r['case']).encode()).hexdigest(),16)%32==0:
                    o=cases[r['case']];m=o.maze;assert record(org.react(m.cells,m.w,m.h,m.start,m.goal),o)==r;replays+=1
    writez(OUT/'preflight_receipts.json.gz',dict(pool=p,screen_receipts=receipts,final_receipts=rr,nominations=ns,summary=summary))
    writej(OUT/'preflight.json',dict(status='PASS',scientific_calls=0,fixture_calls=sum(x['calls'] for x in receipts+rr),
        independent_fixture_alias_grades=grades,fixed_native_fixture_replays=replays,candidate_seconds=sum(x['candidate_seconds'] for x in receipts+rr),
        wall_seconds=time.monotonic()-t,controls_all_correct=True,prior_hashes_verified=verify_prior()))


def register():
    assert not (OUT/'registration.json').exists() and (OUT/'preflight.json').exists()
    r=shared.source_manifest();paths=[*[p for p in OUT.rglob('*') if p.is_file()],ROOT/'docs/COPY_SPECIALIZATION.md',
        ROOT/'tests/test_copy_specialization.py',ROOT/'tools/run_m20_workflow.py',PRIOR/'completion.json',DIAG/'completion.json']
    r['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths});r.update(phase='M20',scientific_calls=0,scientific_pool_generated=False)
    writej(OUT/'registration.json',r)


def pool():
    config=check();pushed(OUT/'registration.json');assert not (OUT/'pool.json.gz').exists()
    p=make_pool(readz(OUT/'sources.json.gz'),config['pool_seed'],config['draws_per_anchor']);writez(OUT/'pool.json.gz',p)
    items=p['items']+references(readz(OUT/'sources.json.gz'))
    writej(OUT/'pool_counts.json',dict(aliases=len(items),physical_models=sum(map(len,tasks(items,[]))),
        max_screen_calls=sum(map(len,tasks(items,[])))*712,arm_queries_each=2*config['draws_per_anchor']*712,
        edit_opportunities_each_arm=2*config['draws_per_anchor']*4,case_generation_started=False))


def run_phase(final=False):
    config=check();name='final' if final else 'screen';directory=RUN/name
    pushed(OUT/('choices.json.gz' if final else 'pool.json.gz'))
    if final:assert json.loads((OUT/'screen_audit.json').read_text())['status']=='PASS'
    assert not (directory/'campaign.sqlite').exists(),'No implicit resume/replacement'
    directory.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    if final:
        config=dict(config,session_wall_seconds=config['final_wall_seconds'],call_cap=1000000,work_cap=10**14,
            layout_base_manifest=str(OUT/'screen_exclusions.json'))
        items=readz(OUT/'choices.json.gz')['items']
    else:items=readz(OUT/'pool.json.gz')['items']+references(readz(OUT/'sources.json.gz'))
    previous=load_layouts(ROOT/config['layout_base_manifest']);shared.evaluate_task=evaluate_task;shared.resource_reason=guard
    with writer_lock(directory):
        j=Journal(directory);j.initialize(config,dict(items_sha256=hashed(packed(items))),previous)
        data=(confirmation if final else screen)(config['final_seed'] if final else config['screen_seed'],previous)
        assert not (OUT/f'{name}_cases.json.gz').exists();writez(OUT/f'{name}_cases.json.gz',data)
        n=j.prepare(data,tasks(items,data['queries']['all']))
        with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
            reason=shared.run_stage(j,n,data,ex,config,started,[False])
        if not reason:j.commit(n,j.state(),dict(no_evolution=True,no_adaptive_cases=True))
        writej(OUT/f'{name}_session.json',dict(status='complete' if reason is None else 'stopped',reason=reason,usage=j.get('usage'),
            wall_seconds=time.monotonic()-started,rss_peak_bytes=shared._peak_rss));j.close();assert reason is None,reason
    write_reference(OUT/f'{name}_exclusions.json',ROOT/config['layout_base_manifest'],previous|set(data['new_layouts']))


def load(final=False):
    name='final' if final else 'screen';con=sqlite3.connect(f'file:{RUN/name}/campaign.sqlite?mode=ro',uri=True);rows={};models=[]
    assert con.execute('select count(*) from stages where complete=1').fetchone()[0]==1
    for spec,result,h in con.execute('select spec,result,result_hash from tasks order by n'):
        assert hashed(result)==h;ss=unpacked(spec);rr=unpacked(result)['entries'];assert len(ss)==len(rr)
        for e,r in zip(ss,rr):
            assert e['aliases']==r['aliases'] and e['queries']==[v['case'] for v in r['rows']]
            for i in e['aliases']:assert i not in rows;rows[i]=r['rows']
            models.append((e,r['rows']))
    con.close();return readz(OUT/f'{name}_cases.json.gz'),rows,models


def select():
    check();assert not (OUT/'choices.json.gz').exists();data,rows,_=load();sources=readz(OUT/'sources.json.gz')
    items=readz(OUT/'pool.json.gz')['items']+references(sources);ns=nominate(items,rows,data,list(sources['protected']))
    writez(OUT/'selection.json.gz',ns);writez(OUT/'choices.json.gz',dict(items=selected_items(items,ns['nominations']),nominations=ns['nominations']))


def analyze():
    check();assert not (OUT/'summary.json').exists();data,rows,models=load(True);choices=readz(OUT/'choices.json.gz')
    result=summarize(choices['items'],choices['nominations'],rows,data,list(readz(OUT/'sources.json.gz')['protected']))
    writej(OUT/'summary.json',result);writez(OUT/'final_responses.json.gz',dict(models=[dict(aliases=e['aliases'],rows=rs) for e,rs in models]))


def audit(final=False):
    config=check();name='final' if final else 'screen';assert not (OUT/f'{name}_audit.json').exists();started=time.monotonic()
    data,rows,models=load(final);sources=readz(OUT/'sources.json.gz');p=readz(OUT/'pool.json.gz')
    assert p==make_pool(sources,config['pool_seed'],config['draws_per_anchor'])
    base=OUT/'screen_exclusions.json' if final else OUT/'exclusions.json'
    assert canonical((confirmation if final else screen)(config['final_seed'] if final else config['screen_seed'],load_layouts(base)))==data
    all_items=p['items']+references(sources);choices=readz(OUT/'choices.json.gz');items=choices['items'] if final else all_items
    directory=RUN/name;con=sqlite3.connect(f'file:{directory}/campaign.sqlite?mode=ro',uri=True)
    assert [unpacked(r[0]) for r in con.execute('select spec from tasks order by n')]==tasks(items,data['queries']['all']);con.close()
    cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in data['queries']['all']]);checker=Checker(cases);grades=replays=0
    for e,rs in models:
        assert guard(directory,dict(config,session_wall_seconds=config['audit_wall_seconds']),started) is None
        org=organism(e['model']);key=hashed(packed(e['model']))
        for row in rs:
            checker.row(row);grades+=1
            if final or int(hashlib.sha256((key+'/'+row['case']).encode()).hexdigest(),16)%32==0:
                o=cases[row['case']];m=o.maze;assert record(org.react(m.cells,m.w,m.h,m.start,m.goal),o)==row;replays+=1
    for c in controls():assert all(r['optimal'] or r['no_path'] for r in rows[c['id']])
    if final:
        assert summarize(items,choices['nominations'],rows,data,list(sources['protected']))==json.loads((OUT/'summary.json').read_text())
        from .baselines import baseline
        from .foundation_pair_confirm import normal_row
        baselines={}
        for method in ('compiled_bfs','compiled_astar','wave_bit'):
            baselines[method]=[]
            for o in cases.values():
                m=o.maze;r=canonical(normal_row(baseline(method,m.cells,m.w,m.h,m.start,m.goal),o));checker.row(r);assert r['optimal'] or r['no_path'];baselines[method].append(r)
        writez(OUT/'baselines.json.gz',baselines)
    else:
        ns=nominate(items,rows,data,list(sources['protected']));assert ns==readz(OUT/'selection.json.gz')
        assert selected_items(items,ns['nominations'])==choices['items'] and ns['nominations']==choices['nominations']
    with writer_lock(directory):
        j=Journal(directory);chain=j.verify_chain();assert not j.pending() and grades==j.get('usage')['calls'];j.close()
    writej(OUT/f'{name}_audit.json',dict(status='PASS',independent_grades=grades,native_replays=replays,chain=chain,wall_seconds=time.monotonic()-started,
        conventional_calls=3*len(cases) if final else 0,pool_rng_all_edits_corpus_tasks_replayed=True,nomination_replayed=not final,summary_replayed=final,
        limitation='Shared unchanged production VM/operator; independent raster grader. Fixed1/32native screen sample, ALL-native final.'))
    print(name,'AUDIT PASS',grades,replays,flush=True)


if __name__=='__main__':
    actions=dict(prepare=prepare,preflight=preflight,register=register,pool=pool,screen=run_phase,select=select,screen_audit=audit,
        final=lambda:run_phase(True),analyze=analyze,final_audit=lambda:audit(True))
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=actions);args=parser.parse_args();actions[args.action]()
