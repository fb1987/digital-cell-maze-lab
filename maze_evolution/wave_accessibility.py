"""M2: a bounded fixed-parent assay; never writes to earlier scientific phases."""
import argparse, hashlib, json, multiprocessing, random, shutil, signal, sqlite3, time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz, compressed_json as writez
from .deep_confirmation import writej
from .deep_campaign_store import Journal, packed, unpacked, hashed, writer_lock
from . import deep_campaign as shared
from .modular_genome import Genome, mutate, random_genome
from .modular_pilot import organism, evaluate_task, controls, pushed
from .modular_pilot_search import rank
from .deep_confirmation_analysis import capabilities, compare
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .family_evolution_data import AccessData
from .selectivity_data import SPECS
from .reboot_data import ordinary, confirmation
from .datasets import manifest
from .routing_transfer import sha, canonical
from .baselines import baseline
from .foundation_pair_confirm import normal_row
from .exposure_selection import record

OUT=ROOT/'results/wave_accessibility';RUN=ROOT/'runs/wave_accessibility_m2'
PRIOR=ROOT/'results/modular_pilot'
CONFIG=dict(phase='M2',seed=2026102101,screen_seed=2026102102,final_seed=2026102103,
 fixture_seed=202610210101,draws=4096,workers=10,session_wall_seconds=5400,
 memory_bytes=12*2**30,storage_bytes=8*2**30,disk_free_floor_bytes=16*2**30,
 call_cap=12000000,work_cap=10**15)


def anchors():
    a=json.loads((PRIOR/'development_wave_ancestry.json').read_text())['events'][-1]['item']
    b=json.loads((PRIOR/'development_delayed_wave_mechanism.json').read_text())
    assert a['id']=='m1/modular/0/familiar/mutation/g24/b39'
    return [dict(id=a['id'],genome=a['genome'],representation='modular',root=a['root'],kind='accumulating'),
            dict(id=b['identity'],genome=b['genome'],representation='modular',root=b['root'],kind='delayed')]


def pool(seed,count,aa):
    rng=random.Random(seed);initial=rng.getstate();items=[]
    for k,a in enumerate(aa):
        for depth in (1,2):
            for n in range(count):
                g=Genome.from_dict(a['genome']);events=[];intermediate=None
                for step in range(depth):
                    if step:intermediate=g.to_dict()
                    g,e=mutate(g,rng);events.append(e)
                items.append(dict(id=f'm2/a{k}/d{depth}/{n:05}',anchor=a['id'],depth=depth,
                    representation='modular',genome=g.to_dict(),events=events,intermediate=intermediate,
                    changed=g.to_dict()!=a['genome'],kind='mutant'))
    for n in range(count):
        items.append(dict(id=f'm2/random/{n:05}',representation='modular',genome=random_genome(rng).to_dict(),
            anchor=None,depth=0,events=[],intermediate=None,changed=None,kind='random'))
    return canonical(dict(items=items,rng_initial=initial,rng_final=rng.getstate(),seed=seed,count=count))


def screen(seed,previous):
    d=AccessData(seed,previous)
    for i,(length,shape,stress) in enumerate(SPECS):
        d.context('m2_screen',i,length,shape,(0,1,2,4,8),stress)
    ids=[c for c,m in d.metadata.items() if (m['family']=='paired' and m['pose'] in (0,4)) or
        (m['family']=='corridor' and m['pose']==0) or
        (m['family']=='disconnected' and m['prefix']==0 and m['pose']==0)]
    ids+=ordinary(d,'m2_screen',[(f,n,12) for f,n in [('perfect',11),('random',9),('disconnected',9)]])
    return dict(kind='assessment',generation=0,mazes=manifest(d.cache.values()),metadata=d.metadata,
        contexts=d.contexts,queries={'all':ids},new_layouts=sorted(d.layouts-set(previous)),rejections=d.rejections)


def tasks(items,ids):
    grouped={}
    for i in items:
        model=dict(representation=i['representation'],genome=i['genome']);key=hashed(packed(model))
        grouped.setdefault(key,dict(model=model,queries=ids,aliases=[]))['aliases'].append(i['id'])
    values=list(grouped.values())
    return [values[n:n+4] for n in range(0,len(values),4)]


def route_precision(rows,meta):
    """Only unique-route structured tasks; zero reward for missing any route cell."""
    full=0;total=0;precision=0.;excess=0
    for r in rows:
        m=meta[r['case']]
        if m['family'] not in ('paired','corridor') or m['graph']!='fork':continue
        path=m['path']
        if not path:continue
        total+=1;mask=int.from_bytes(bytes.fromhex(r['mask']),'little')
        target=sum(1<<p for p in path)
        if r['status']=='emitted' and mask&target==target:
            full+=1;precision+=len(path)/mask.bit_count();excess+=mask.bit_count()-len(path)
    return dict(full=full,total=total,precision=round(precision/max(1,total),12),excess=excess)


def feature(rows,meta,parents):
    c=capabilities(rows,meta);pr=route_precision(rows,meta);vs={}
    for identity,b in parents.items():
        v=compare(c,b,meta)
        v['eligible']=b['success']<=c['success'] and c['false']<=b['false']
        v['ordinary_retention']=len(c['ordinary_bases']&b['ordinary_bases'])/len(b['ordinary_bases']) if b['ordinary_bases'] else None
        v['acquisition_gate'] &= v['ordinary_retention'] is None or v['ordinary_retention']>=.9
        v['broad_transfer_flag'] &= v['acquisition_gate']
        # Detailed case membership is kept for nominees in final analysis, not every draw.
        for key in ('new_pair_keys','lost_pair_keys','new_ordinary_base_keys'):v.pop(key)
        vs[identity]=v
    return dict(rank=list(rank(rows,meta)),metrics=c['summary'],route=pr,versus=vs)


def selection_score(f):
    return (f['metrics']['paired'],f['metrics']['ordinary_bases_both_poses'],
            f['route']['full'],f['route']['precision'],*f['rank'])


def select(items,features,aa):
    choices=[]
    def pick(candidates,label,method,anchor=None):
        allowed=[i for i in candidates if method=='original' or features[i['id']]['versus'][anchor]['eligible']]
        best=min(allowed,key=lambda i:(tuple(-v for v in (features[i['id']]['rank'] if method=='original' else selection_score(features[i['id']]))),i['id']))
        choices.append(dict(label=label,method=method,anchor=anchor,item=best))
    for k,a in enumerate(aa):
        for depth in (1,2):
            group=[i for i in items if i.get('anchor')==a['id'] and i['depth']==depth]+[a]
            for method in ('original','selective'):pick(group,f'a{k}/d{depth}/{method}',method,a['id'])
    randoms=[i for i in items if i['kind']=='random']
    pick(randoms,'random/original','original')
    for k,a in enumerate(aa):pick(randoms+[a],f'random/retained_a{k}','selective',a['id'])
    return choices


def resource_reason(directory,config,started):
    if time.monotonic()-started>=config['session_wall_seconds']:return 'session_wall'
    if shared.process_resources()>=config['memory_bytes']:return 'memory'
    if shutil.disk_usage(RUN).free<config['disk_free_floor_bytes']:return 'disk_free'
    if sum(p.stat().st_size for base in (RUN,OUT) for p in base.rglob('*') if p.is_file())>=config['storage_bytes']:return 'storage'


def check():
    r=json.loads((OUT/'registration.json').read_text())
    for p,h in r['files'].items():assert sha(ROOT/p)==h,p
    now=shared.source_manifest();assert all(now[k]==r[k] for k in ('python','dependencies'))
    return json.loads((OUT/'config.json').read_text())


def prepare():
    assert not (OUT/'registration.json').exists();OUT.mkdir(parents=True,exist_ok=True)
    seal=json.loads((PRIOR/'completion.json').read_text())
    for p,h in seal['files'].items():assert sha(ROOT/p)==(h['sha256'] if isinstance(h,dict) else h),p
    aa=anchors();writej(OUT/'anchors.json',aa);writej(OUT/'config.json',CONFIG)
    previous=set(readz(PRIOR/'whole_layout_exclusions.json.gz')['hashes'])
    fixture=screen(CONFIG['fixture_seed'],previous);writez(OUT/'fixture.json.gz',fixture)
    previous.update(fixture['new_layouts']);writez(OUT/'exclusions.json.gz',dict(count=len(previous),hashes=sorted(previous)))
    # Calibration entirely random, never evaluates scientific anchors.
    rng=random.Random(CONFIG['fixture_seed']);fake=[dict(id=f'fixture/{k}',genome=random_genome(rng).to_dict(),representation='modular',root=f'fixture/{k}',kind='fixture') for k in range(2)]
    p=pool(CONFIG['fixture_seed'],16,fake);assert pool(CONFIG['fixture_seed'],16,fake)==p
    writez(OUT/'fixture_pool.json.gz',dict(anchors=fake,pool=p))
    ts=tasks(fake+p['items']+controls(),fixture['queries']['all']);mazes=[m for m in fixture['mazes'] if m['case_id'] in set(fixture['queries']['all'])]
    # Warm production signature before measured profile; same read-only bytes/dtypes.
    evaluate_task([dict(model=ts[0][0]['model'],queries=fixture['queries']['all'][:1],aliases=['warmup'])],mazes,'m2warm')
    start=time.monotonic()
    with ProcessPoolExecutor(10,mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
        rr=list(ex.map(evaluate_task,ts,[mazes]*len(ts),['m2fixture']*len(ts)))
    writez(OUT/'fixture_receipts.json.gz',rr)
    rows={a:e['rows'] for r in rr for e in r['entries'] for a in e['aliases']}
    assert all(all(r['optimal'] or r['no_path'] for r in rows[c['id']]) for c in controls())
    parents={a['id']:capabilities(rows[a['id']],fixture['metadata']) for a in fake}
    fs={i:feature(r,fixture['metadata'],parents) for i,r in rows.items()}
    choices=select(p['items'],fs,fake);assert len(choices)==11
    writez(OUT/'fixture_selection.json.gz',choices)
    writej(OUT/'profile.json',dict(calls=sum(r['calls'] for r in rr),candidate_seconds=sum(r['candidate_seconds'] for r in rr),
        wall_seconds=time.monotonic()-start,queries=len(fixture['queries']['all']),models=sum(len(t) for t in ts),
        controls_all_correct=True,pool_rng_replay=True,selection_exercised=True,scientific_calls=0))
    print(json.dumps(json.loads((OUT/'profile.json').read_text()),indent=2))


def register():
    assert not (OUT/'registration.json').exists();r=shared.source_manifest()
    paths=[*OUT.glob('*.json'),*OUT.glob('*.json.gz'),ROOT/'docs/WAVE_ACCESSIBILITY.md',ROOT/'tests/test_wave_accessibility.py',PRIOR/'completion.json']
    r['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    r.update(phase='M2',scientific_calls=0,scientific_cases_generated=0)
    writej(OUT/'registration.json',r)


def run(final=False):
    config=check();pushed(OUT/'choices.json.gz' if final else OUT/'registration.json')
    if final:config=dict(config,call_cap=100000,work_cap=10**14)
    directory=RUN/'final' if final else RUN;directory.mkdir(parents=True,exist_ok=True)
    shared.evaluate_task=evaluate_task;shared.resource_reason=resource_reason
    previous=set(readz(OUT/'exclusions.json.gz')['hashes']);aa=json.loads((OUT/'anchors.json').read_text())
    if final:
        previous.update(readz(OUT/'screen.json.gz')['new_layouts']);items=final_panel()['items']
    else:
        if not (OUT/'pool.json.gz').exists():writez(OUT/'pool.json.gz',pool(config['seed'],config['draws'],aa))
        items=aa+readz(OUT/'pool.json.gz')['items']+controls()
    started=time.monotonic();stop=[False]
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stop.__setitem__(0,True))
    with writer_lock(directory):
        j=Journal(directory);j.initialize(config,dict(items_hash=hashed(packed(items))),previous);j.verify_chain()
        if j.get('latest')>=0:j.close();return
        pending=j.pending()
        if pending:n,data=pending
        else:
            data=confirmation(config['final_seed'],previous) if final else screen(config['screen_seed'],previous)
            if final:data['queries']={'all':data['queries']}
            writez(OUT/('confirmation.json.gz' if final else 'screen.json.gz'),data)
            n=j.prepare(data,tasks(items,data['queries']['all']))
        assert [s for _,s,_ in j.tasks(n)]==tasks(items,data['queries']['all'])
        print('START', 'final' if final else 'screen',len(items),len(data['queries']['all']),len(j.tasks(n)),flush=True)
        with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
            reason=shared.run_stage(j,n,data,ex,config,started,stop)
        if not reason:j.commit(n,j.state(),dict(no_reproduction=True))
        writej(OUT/('final_session.json' if final else 'screen_session.json'),dict(status='checkpoint' if reason else 'complete',reason=reason,
            usage=j.get('usage'),rss_peak_bytes=shared._peak_rss,wall_seconds=time.monotonic()-started))
        j.close();print('STOP',reason,flush=True)


def connect(final=False):
    directory=RUN/'final' if final else RUN
    db=sqlite3.connect(f'file:{directory}/campaign.sqlite?mode=ro',uri=True)
    j=Journal.__new__(Journal);j.db=db;j.directory=directory
    assert j.get('latest')==0;chain=j.verify_chain()
    data=unpacked(db.execute('select input from stages where n=0').fetchone()[0])
    return db,data,j.get('usage'),chain


def entries(db):
    for spec,blob,h in db.execute('select spec,result,result_hash from tasks where stage=0 order by n'):
        assert hashed(blob)==h;spec=unpacked(spec);receipt=unpacked(blob)
        for s,e in zip(spec,receipt['entries'],strict=True):
            assert s['aliases']==e['aliases'] and s['queries']==[r['case'] for r in e['rows']]
            yield s,e['rows']


def screening():
    db,data,usage,chain=connect();aa=json.loads((OUT/'anchors.json').read_text());anchor_ids={a['id'] for a in aa};parents={}
    for s,rr in entries(db):
        for a in set(s['aliases'])&anchor_ids:parents[a]=capabilities(rr,data['metadata'])
        if len(parents)==len(aa):break
    features={};physical=0
    for s,rr in entries(db):
        physical+=1;f=feature(rr,data['metadata'],parents)
        for a in s['aliases']:features[a]=f
    p=readz(OUT/'pool.json.gz');choices=select(p['items'],features,aa);counts={}
    for k,a in enumerate(aa):
        for depth in (1,2):
            group=[i for i in p['items'] if i['anchor']==a['id'] and i['depth']==depth]
            counts[f'a{k}/d{depth}']=dict(draws=len(group),changed=sum(i['changed'] for i in group),
                distinct_genotypes=len({hashed(packed(i['genome'])) for i in group}),
                retained=sum(features[i['id']]['versus'][a['id']]['eligible'] for i in group),
                gained_pairs=sum(features[i['id']]['versus'][a['id']]['new_pairs']>0 for i in group),
                acquisition=sum(i['changed'] and features[i['id']]['versus'][a['id']]['acquisition_gate'] for i in group),
                broad=sum(i['changed'] and features[i['id']]['versus'][a['id']]['broad_transfer_flag'] for i in group))
    result=dict(label='development only',usage=usage,chain=chain,physical_models=physical,logical_slots=len(p['items'])+len(aa)+2,
        queries=len(data['queries']['all']),cohorts=counts,anchors={a:features[a] for a in anchor_ids},
        nominees=[dict(label=c['label'],identity=c['item']['id'],feature=features[c['item']['id']]) for c in choices])
    db.close();return choices,features,result


def freeze():
    check();assert not (OUT/'choices.json.gz').exists()
    choices,features,result=screening();writez(OUT/'choices.json.gz',choices)
    writez(OUT/'screen_features.json.gz',features);writej(OUT/'screen_summary.json',result)
    writez(OUT/'final_panel.json.gz',final_panel());print(json.dumps(dict(cohorts=result['cohorts'],nominees=[(n['label'],n['identity'],n['feature']['metrics']['paired']) for n in result['nominees']]),indent=2))


def final_panel():
    aa=json.loads((OUT/'anchors.json').read_text());choices=readz(OUT/'choices.json.gz');items={i['id']:i for i in aa+controls()}
    for c in choices:
        i=c['item'];items[i['id']]=i
        if i.get('intermediate') is not None:
            identity=i['id']+'/intermediate';items[identity]=dict(id=identity,representation='modular',genome=i['intermediate'],anchor=i['anchor'],kind='intermediate')
    return dict(items=list(items.values()),choices=choices)


def final_analysis():
    db,data,usage,chain=connect(True);panel=final_panel();parents={};rows={};physical=0
    for s,rr in entries(db):
        physical+=1
        for a in s['aliases']:rows[a]=rr;parents[a]=capabilities(rr,data['metadata'])
    aa=json.loads((OUT/'anchors.json').read_text());anchor_ids={a['id'] for a in aa};nominees=[]
    for c in panel['choices']:
        i=c['item'];f=feature(rows[i['id']],data['metadata'],{a:parents[a] for a in anchor_ids})
        for identity,v in f['versus'].items():
            eligible=i.get('kind')=='mutant' and i.get('changed',False) and i.get('anchor')==identity
            v['acquisition_gate'] &= eligible;v['broad_transfer_flag'] &= eligible
        intermediate=i['id']+'/intermediate'
        nominees.append(dict(label=c['label'],identity=i['id'],kind=i['kind'],anchor=c['anchor'],feature=f,
            versus_intermediate=compare(parents[i['id']],parents[intermediate],data['metadata']) if intermediate in parents else None))
    for c in controls():assert len(parents[c['id']]['success'])==len(data['queries']['all'])
    result=dict(label='untouched confirmation; no reselection',usage=usage,chain=chain,physical_models=physical,
        queries=len(data['queries']['all']),nominees=nominees,all_models={i:c['summary'] for i,c in parents.items()})
    db.close();return result


def analyze():
    check();assert not (OUT/'final_summary.json').exists();writej(OUT/'final_summary.json',final_analysis())
    db,data,_,_=connect(True);db.close();cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in set(data['queries']['all'])]);checker=Checker(cases);base={};start=time.monotonic()
    for name in ('compiled_bfs','compiled_astar','wave_bit'):
        base[name]=[]
        for cid in data['queries']['all']:
            o=cases[cid];m=o.maze;r=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));checker.row(r);assert r['optimal'] or r['no_path'];base[name].append(r)
    writez(OUT/'baselines.json.gz',base);writej(OUT/'baseline_usage.json',dict(calls=sum(map(len,base.values())),wall_seconds=time.monotonic()-start,all_correct=True))


def audit(final=False):
    start=time.monotonic();config=check();out=OUT/('final_audit.json' if final else 'screen_audit.json');assert not out.exists()
    aa=json.loads((OUT/'anchors.json').read_text());assert aa==anchors()
    assert pool(config['seed'],config['draws'],aa)==readz(OUT/'pool.json.gz')
    previous=set(readz(OUT/'exclusions.json.gz')['hashes'])
    if final:previous.update(readz(OUT/'screen.json.gz')['new_layouts'])
    expected=confirmation(config['final_seed'],previous) if final else screen(config['screen_seed'],previous)
    if final:expected['queries']={'all':expected['queries']}
    db,data,usage,chain=connect(final);assert expected==data
    items=final_panel()['items'] if final else aa+readz(OUT/'pool.json.gz')['items']+controls()
    assert [unpacked(r[0]) for r in db.execute('select spec from tasks where stage=0 order by n')]==tasks(items,data['queries']['all'])
    cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in set(data['queries']['all'])]);checker=Checker(cases);native=grades=0
    for s,rr in entries(db):
        org=organism(s['model']);key=hashed(packed(s['model']))
        for r in rr:
            checker.row(r);grades+=1
            if final or int(hashlib.sha256((key+'/'+r['case']).encode()).hexdigest()[:8],16)%64==0:
                o=cases[r['case']];m=o.maze;assert record(org.react(m.cells,m.w,m.h,m.start,m.goal),o)==r;native+=1
    db.close();bc=0
    if final:
        assert final_analysis()==json.loads((OUT/'final_summary.json').read_text())
        for name,rr in readz(OUT/'baselines.json.gz').items():
            for r in rr:
                o=cases[r['case']];m=o.maze;assert canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o))==r;checker.row(r);bc+=1
    else:
        choices,features,summary=screening();assert choices==readz(OUT/'choices.json.gz');assert features==readz(OUT/'screen_features.json.gz');assert summary==json.loads((OUT/'screen_summary.json').read_text())
    writej(out,dict(passed=True,source_hashes=True,pool_draws_replayed=5*config['draws'],mutation_events_replayed=6*config['draws'],corpus_recreated=True,task_specs_recreated=True,
        decisions_recomputed=True,chain=chain,independent_grades=grades,native_replays=native,baseline_replays=bc,
        second_vm=False,wall_seconds=time.monotonic()-start,usage=usage));print(out,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','register','run','freeze','final','analyze','audit','final-audit']);args=parser.parse_args()
    if args.action=='final':run(True)
    elif args.action=='audit':audit()
    elif args.action=='final-audit':audit(True)
    else:globals()[args.action]()
