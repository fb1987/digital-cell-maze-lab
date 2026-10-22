"""M17 matched generic copy into spare state assay."""
import argparse,json,random,time,sqlite3,shutil,multiprocessing
from copy import deepcopy
from concurrent.futures import ProcessPoolExecutor
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz,compressed_json as writez
from .deep_confirmation import writej
from .routing_transfer import sha,canonical
from .deep_campaign_store import writer_lock,packed,unpacked,hashed
from .referenced_campaign_store import Journal,load_layouts,write_reference
from . import deep_campaign as shared
from .exploration_continuation import controls,pushed
from .spare_evaluation import organism,evaluate_task
from .spare_genome import Genome as SpareGenome,embed,duplicate,mutate as spare_mutate
from .modular_genome import Genome,random_genome,mutate
from .regulatory import Gene
from .restoration_data import screen,confirmation
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import record
from .spare_metrics import nominate,summarize

OUT=ROOT/'results/spare_state_assay';RUN=ROOT/'runs/spare_state_assay_m17'
PRIOR=ROOT/'results/restoration_assay'
TARGET='m14/modular/1/explore/g320/b48'
CONFIG=dict(phase='M17',pool_seed=2026102205,screen_seed=2026102206,final_seed=2026102207,
    fixture_seed=202610220580,draws_per_anchor=512,random_draws=256,workers=10,
    call_cap=4000000,work_cap=10**13,session_wall_seconds=1200,final_wall_seconds=300,
    audit_wall_seconds=1800,memory_bytes=8*2**30,
    storage_bytes=6*2**30,disk_free_floor_bytes=16*2**30,
    layout_base_manifest='results/spare_state_assay/exclusions.json')


def verify_prior():
    prior=json.loads((PRIOR/'completion.json').read_text())
    for p,h in prior['files'].items():assert sha(ROOT/p)==h,p
    for p,e in prior['local_records'].items():assert sha(ROOT/p)==e['sha256'],p
    return prior


def check():
    r=json.loads((OUT/'registration.json').read_text())
    for p,h in r['files'].items():assert sha(ROOT/p)==h,p
    now=shared.source_manifest();assert all(r[k]==now[k] for k in ('python','dependencies'))
    verify_prior();return json.loads((OUT/'config.json').read_text())


def make_pool(sources,seed,count,random_count):
    rng=random.Random(seed);initial=rng.getstate();items=[]
    for anchor in ('parent','child'):
        base=Genome.from_dict(sources['anchors'][anchor]['genome'])
        for n in range(count):
            depth=3+2*(n%2);donor=rng.randrange(8)
            overwrite=rng.choice([i for i in range(8) if i!=donor]);spare=rng.choice((8,9))
            first_seed=rng.getrandbits(64);later_seed=rng.getrandbits(64)
            for arm in ('unchanged','overwrite','spare'):
                g=embed(base) if arm=='spare' else base
                first=random.Random(first_seed);later=random.Random(later_seed)
                if arm=='unchanged':g,e=mutate(g,first)
                else:g,e=duplicate(g,donor,spare if arm=='spare' else overwrite)
                events=[e]
                for _ in range(depth-1):
                    g,e=(spare_mutate if arm=='spare' else mutate)(g,later);events.append(e)
                items.append(dict(id=f'{arm}/{anchor}/mutation/{n:04d}',kind='mutation',arm=arm,anchor=anchor,depth=depth,
                    paired_draw=n,donor=donor,overwrite_target=overwrite,spare_target=spare,
                    first_seed=first_seed,later_seed=later_seed,first_rng_final=first.getstate(),later_rng_final=later.getstate(),
                    model=dict(representation='spare' if arm=='spare' else 'modular',genome=g.to_dict()),events=events))
    for n in range(random_count):
        g=random_genome(rng)
        for arm,gg in [('unchanged',g),('spare',embed(g))]:
            items.append(dict(id=f'{arm}/random/{n:04d}',kind='random',arm=arm,
                model=dict(representation='spare' if arm=='spare' else 'modular',genome=gg.to_dict()),events=[]))
    return canonical(dict(items=items,seed=seed,rng_initial=initial,rng_final=rng.getstate()))


def references(sources):
    refs=[dict(id='anchor/'+k,kind='reference',model=dict(representation='modular',genome=v['genome']),source=v['id']) for k,v in sources['anchors'].items()]
    refs += [dict(id=i,kind='protected',model=dict(representation='modular',genome=v['genome']),source=i) for i,v in sources['protected'].items()]
    refs += [dict(id=c['id'],kind='control',model={k:c[k] for k in ('representation','genome')}) for c in controls()]
    for r in list(refs):
        if r['model']['representation']=='modular':
            refs.append(dict(id='embedded/'+r['id'],kind='embedding',source=r['id'],
                model=dict(representation='spare',genome=embed(Genome.from_dict(r['model']['genome'])).to_dict())))
    return refs


def verify_embeddings(items,rows):
    count=0
    for i in items:
        if i['kind']=='embedding':
            for a,b in zip(rows[i['id']],rows[i['source']]):
                assert {k:v for k,v in a.items() if k!='array_bytes'}=={k:v for k,v in b.items() if k!='array_bytes'},(i['id'],a,b)
                n=(a['array_bytes']-b['array_bytes']-152)//8
                assert n>0 and a['array_bytes']-b['array_bytes']==8*n+152
                count+=1
    return count


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
    assert not OUT.exists();verify_prior();OUT.mkdir();RUN.mkdir(parents=True,exist_ok=True)
    sources=readz(PRIOR/'sources.json.gz')
    writez(OUT/'sources.json.gz',sources);writej(OUT/'config.json',CONFIG)
    from .datasets import make_case
    from .foundation_data import transform_maze,layout_hash
    excluded=load_layouts(PRIOR/'whole_layout_exclusions.json');old_count=len(excluded)
    for family in ('perfect','random','disconnected'):
        maze=make_case(817,'m17-test',0,0,9,family).maze
        excluded.update(layout_hash(transform_maze(maze,p)) for p in range(8))
    write_reference(OUT/'test_exclusions.json',PRIOR/'whole_layout_exclusions.json',excluded)
    writej(OUT/'test_layout_exclusions.json',dict(previous=old_count,total=len(excluded),new_discarded=len(excluded)-old_count,test_cases=3,poses=8))


def preflight():
    assert not (OUT/'registration.json').exists() and not (OUT/'preflight.json').exists()
    data=readz(PRIOR/'discarded_corpus_fixture.json.gz');ids=data['queries']['all']
    rng=random.Random(CONFIG['fixture_seed'])
    fake=dict(anchors={k:dict(id='fake/'+k,genome=random_genome(rng).to_dict()) for k in ('parent','child')},protected={})
    fake['protected']={'fake/reference':fake['anchors']['parent']}
    pp=make_pool(fake,CONFIG['fixture_seed'],8,4);assert pp==make_pool(fake,CONFIG['fixture_seed'],8,4)
    items=pp['items']+references(fake);ts=tasks(items,ids);mz=[m for m in data['mazes'] if m['case_id'] in ids]
    started=time.monotonic();warm=tasks(references(fake),ids[:1]);warm_receipts=[evaluate_task(t,mz,'warm') for t in warm]
    with ProcessPoolExecutor(10,mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
        rr=list(ex.map(evaluate_task,ts,[mz]*len(ts),['fixture']*len(ts)))
    rows={i:e['rows'] for r in rr for e in r['entries'] for i in e['aliases']}
    for c in controls():assert all(r['optimal'] or r['no_path'] for r in rows[c['id']])
    assert all(r['optimal'] or r['no_path'] for r in rows['embedded/control/intact_modular'])
    embeddings=verify_embeddings(items,rows)
    selected=nominate(items,rows,data,list(fake['protected']));assert selected==nominate(items,rows,data,list(fake['protected']))
    summary=summarize(items,selected['nominations'],rows,data,list(fake['protected']))
    assert summary==summarize(items,selected['nominations'],rows,data,list(fake['protected']))
    write_reference(OUT/'exclusions.json',OUT/'test_exclusions.json',load_layouts(OUT/'test_exclusions.json'))
    writez(OUT/'preflight_receipts.json.gz',dict(pool=pp,receipts=rr,selection=selected,summary=summary))
    writej(OUT/'preflight.json',dict(scientific_calls=0,fixture_calls=sum(r['calls'] for r in rr),
        warmup_calls=sum(r['calls'] for r in warm_receipts),embedding_comparisons=embeddings,
        candidate_seconds=sum(r['candidate_seconds'] for r in rr),wall_seconds=time.monotonic()-started,
        controls_all_correct=True,pool_rng_selection_summary_reproduced=True))


def register():
    assert not (OUT/'registration.json').exists();r=shared.source_manifest();assert (OUT/'preflight.json').exists()
    paths=[*[p for p in OUT.rglob('*') if p.is_file()],ROOT/'docs/SPARE_STATE_ASSAY.md',ROOT/'tests/test_spare_state.py',
           ROOT/'tools/run_m17_workflow.py',PRIOR/'completion.json',PRIOR/'whole_layout_exclusions.json']
    r['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths});r.update(phase='M17',scientific_calls=0,scientific_pool_generated=False)
    writej(OUT/'registration.json',r)


def pool():
    config=check();pushed(OUT/'registration.json');assert not (OUT/'pool.json.gz').exists()
    pp=make_pool(readz(OUT/'sources.json.gz'),config['pool_seed'],config['draws_per_anchor'],config['random_draws']);writez(OUT/'pool.json.gz',pp)
    specs=tasks(pp['items']+references(readz(OUT/'sources.json.gz')),[])
    writej(OUT/'pool_counts.json',dict(aliases=len(pp['items']),physical_models=sum(map(len,specs)),max_screen_calls=sum(map(len,specs))*712,scientific_cases_generated=False))


def run_phase(final=False):
    config=check();name='final' if final else 'screen';directory=RUN/name
    pushed(OUT/('choices.json.gz' if final else 'pool.json.gz'))
    if final:assert json.loads((OUT/'screen_audit.json').read_text())['status']=='PASS'
    assert not (directory/'campaign.sqlite').exists(),'Existing phase cannot be silently resumed or replaced'
    directory.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    if final:
        prev=json.loads((OUT/'screen_session.json').read_text());config=dict(config,session_wall_seconds=config['final_wall_seconds'],layout_base_manifest=str(OUT/'screen_exclusions.json'))
        config['call_cap']-=prev['usage']['calls'];config['work_cap']-=prev['usage']['work']
        items=readz(OUT/'choices.json.gz')['items']
    else:items=readz(OUT/'pool.json.gz')['items']+references(readz(OUT/'sources.json.gz'))
    previous=load_layouts(ROOT/config['layout_base_manifest'])
    shared.evaluate_task=evaluate_task;shared.resource_reason=guard
    with writer_lock(directory):
        j=Journal(directory);j.initialize(config,dict(items_sha256=hashed(packed(items))),previous)
        data=(confirmation if final else screen)(config['final_seed'] if final else config['screen_seed'],previous)
        assert not (OUT/f'{name}_cases.json.gz').exists();writez(OUT/f'{name}_cases.json.gz',data)
        n=j.prepare(data,tasks(items,data['queries']['all']))
        with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
            reason=shared.run_stage(j,n,data,ex,config,started,[False])
        if not reason:j.commit(n,j.state(),dict(no_evolution=True,no_adaptive_cases=True))
        writej(OUT/f'{name}_session.json',dict(status='complete' if reason is None else 'stopped',reason=reason,usage=j.get('usage'),wall_seconds=time.monotonic()-started,rss_peak_bytes=shared._peak_rss))
        j.close();assert reason is None,reason
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


def frozen_selection(data,rows):
    sources=readz(OUT/'sources.json.gz');items=readz(OUT/'pool.json.gz')['items']+references(sources)
    selected=nominate(items,rows,data,list(sources['protected']));lookup={i['id']:i for i in items}
    kept={i['id']:i for i in references(sources)}
    for n in selected['nominations']:kept[n['identity']]=lookup[n['identity']]
    return canonical(dict(items=[kept[i] for i in sorted(kept)],nominations=selected['nominations'],screen_features=selected['features']))


def freeze():
    check();assert not (OUT/'choices.json.gz').exists();data,rows,_=load();writez(OUT/'choices.json.gz',frozen_selection(data,rows))


def analyze():
    check();assert not (OUT/'summary.json').exists();data,rows,models=load(True);choices=readz(OUT/'choices.json.gz')
    result=summarize(choices['items'],choices['nominations'],rows,data,list(readz(OUT/'sources.json.gz')['protected']))
    writej(OUT/'summary.json',result);writez(OUT/'final_responses.json.gz',dict(models=[dict(aliases=e['aliases'],rows=rs) for e,rs in models]))


def audit(final=False):
    config=check();name='final' if final else 'screen';assert not (OUT/f'{name}_audit.json').exists();started=time.monotonic()
    data,rows,models=load(final);sources=readz(OUT/'sources.json.gz');pp=readz(OUT/'pool.json.gz')
    assert pp==make_pool(sources,config['pool_seed'],config['draws_per_anchor'],config['random_draws'])
    base=OUT/'screen_exclusions.json' if final else OUT/'exclusions.json'
    assert canonical((confirmation if final else screen)(config['final_seed'] if final else config['screen_seed'],load_layouts(base)))==data
    choices=readz(OUT/'choices.json.gz');items=choices['items'] if final else pp['items']+references(sources)
    directory=RUN/name;con=sqlite3.connect(f'file:{directory}/campaign.sqlite?mode=ro',uri=True)
    assert [unpacked(r[0]) for r in con.execute('select spec from tasks order by n')]==tasks(items,data['queries']['all']);con.close()
    cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in data['queries']['all']]);checker=Checker(cases);grades=replays=0
    for e,rs in models:
        assert guard(directory,dict(config,session_wall_seconds=config['audit_wall_seconds']),started) is None
        org=organism(e['model']);key=hashed(packed(e['model']))
        for row in rs:
            checker.row(row);grades+=1
            if final or any(i.startswith(('anchor/','m14/reference/','control/','embedded/')) for i in e['aliases']) or int(hashed(packed([key,row['case']])),16)%32==0:
                o=cases[row['case']];m=o.maze;assert record(org.react(m.cells,m.w,m.h,m.start,m.goal),o)==row;replays+=1
    for c in controls():assert all(r['optimal'] or r['no_path'] for r in rows[c['id']])
    embedding_comparisons=verify_embeddings(items,rows)
    if final:
        assert summarize(items,choices['nominations'],rows,data,list(sources['protected']))==json.loads((OUT/'summary.json').read_text())
        from .baselines import baseline
        from .foundation_pair_confirm import normal_row
        baseline_rows={}
        for name0 in ('compiled_bfs','compiled_astar','wave_bit'):
            baseline_rows[name0]=[]
            for o in cases.values():
                m=o.maze;r=canonical(normal_row(baseline(name0,m.cells,m.w,m.h,m.start,m.goal),o));checker.row(r);assert r['optimal'] or r['no_path'];baseline_rows[name0].append(r)
        assert not (OUT/'baselines.json.gz').exists();writez(OUT/'baselines.json.gz',baseline_rows)
    else:assert frozen_selection(data,rows)==choices
    with writer_lock(directory):
        j=Journal(directory);chain=j.verify_chain();assert not j.pending();assert grades==j.get('usage')['calls'];j.close()
    writej(OUT/f'{name}_audit.json',dict(status='PASS',independent_grades=grades,native_replays=replays,chain=chain,wall_seconds=time.monotonic()-started,
        conventional_calls=3*len(cases) if final else 0,pool_rng_corpus_tasks_replayed=True,selection_replayed=not final,summary_replayed=final,embedding_comparisons=embedding_comparisons,
        limitation='Shared native VM and mutation operator; independent raster grader; fixed screen native sampling, ALL-native final.'))
    print(name,'AUDIT PASS',grades,replays,flush=True)


if __name__=='__main__':
    actions=dict(prepare=prepare,preflight=preflight,register=register,pool=pool,screen=run_phase,freeze=freeze,
        screen_audit=audit,final=lambda:run_phase(True),analyze=analyze,final_audit=lambda:audit(True))
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=actions);args=parser.parse_args();actions[args.action]()
