"""M5 registered fixed-parent accessibility assay; immutable prior studies."""
import argparse,json,random,time,sqlite3,shutil,multiprocessing
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from .wave_continuation import ROOT,readz,writez,writej,sha,pushed,controls,organism as old_organism
from .holding_genome import Genome
from .holding_runtime import Organism
from .modular_genome import Genome as Base,mutate,random_genome
from . import deep_campaign as shared
from .deep_campaign_store import Journal,writer_lock,packed,unpacked,hashed
from .wave_accessibility import screen
from .wave_continuation_data import confirmation
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .deep_confirmation_analysis import capabilities
from .modular_pilot_search import rank
from .exposure_selection import record
from .routing_transfer import canonical
OUT=ROOT/'results/holding_assay';RUN=ROOT/'runs/holding_assay_m5';PRIOR=ROOT/'results/mechanism_retention'
CONFIG=dict(phase='M5',pool_seed=2026102109,screen_seed=2026102110,final_seed=2026102111,fixture_seed=202610210501,
 draws=1024,workers=10,session_wall_seconds=900,memory_bytes=8*2**30,storage_bytes=6*2**30,
 disk_free_floor_bytes=16*2**30,call_cap=4000000,work_cap=3*10**12)
_cache={}

def embed(base,gates=None,holds=None):return dict(representation='holding',genome=Genome(Base.from_dict(base),tuple(gates or [64]*8),tuple(holds or [0]*8)).to_dict())
def organism(model):return Organism(Genome.from_dict(model['genome'])) if model['representation']=='holding' else old_organism(model)
def engineering():
    cc=[dict(id=c['id'],model={k:c[k] for k in ('representation','genome')},kind='control') for c in controls()]
    modular=next(c for c in controls() if c['representation']=='modular')['genome']
    for hold in (0,1):cc.append(dict(id=f'control/embedded/{hold}',model=embed(modular,holds=[hold]*8),kind='control'))
    return cc

def pool(seed,count,anchors):
    rng=random.Random(seed);initial=rng.getstate();items=[]
    for k,a in enumerate(anchors):
        for n in range(count):
            depth=1+n%2;base=Base.from_dict(a['base']);events=[]
            if depth==2:base,e=mutate(base,rng);events.append(e)
            block=rng.randrange(8);gate=rng.choice([*range(12+len(base.blocks[block])),64]);gates=[64]*8;gates[block]=gate
            for arm in ('zero','hold'):
                holds=[0]*8;holds[block]=int(arm=='hold')
                items.append(dict(id=f'a{k}/{arm}/{n:04}',anchor=k,arm=arm,depth=depth,draw=n,kind='mutant',
                    model=embed(base.to_dict(),gates,holds),events=events+[dict(kind='conditional_writer',block=block,gate=gate,fallback=arm)]))
            g=Base.from_dict(a['base']);ee=[]
            for _ in range(depth):g,e=mutate(g,rng);ee.append(e)
            items.append(dict(id=f'a{k}/standard/{n:04}',anchor=k,arm='standard',depth=depth,draw=n,kind='mutant',model=embed(g.to_dict()),events=ee))
    for n in range(count):items.append(dict(id=f'random/{n:04}',anchor=None,arm='random',depth=0,draw=n,kind='random',model=embed(random_genome(rng).to_dict()),events=[]))
    return canonical(dict(items=items,rng_initial=initial,rng_final=rng.getstate(),seed=seed,count=count))

def tasks(items,ids):
    grouped={}
    for i in items:
        h=hashed(packed(i['model']));grouped.setdefault(h,dict(model=i['model'],queries=ids,aliases=[]))['aliases'].append(i['id'])
    vals=[grouped[h] for h in sorted(grouped)];return [vals[n:n+4] for n in range(0,len(vals),4)]

def evaluate_task(spec,maze_rows,data_hash):
    global _cache
    cpu=time.process_time()
    if _cache.get('hash')!=data_hash:
        cc=cases_from_manifest(maze_rows);_cache=dict(hash=data_hash,cases=cc,checker=Checker(cc))
    entries=[];seconds=work=calls=0
    for e in spec:
        org=organism(e['model']);rr=[]
        for cid in e['queries']:
            o=_cache['cases'][cid];m=o.maze;t=time.perf_counter();response=org.react(m.cells,m.w,m.h,m.start,m.goal);seconds+=time.perf_counter()-t
            r=record(response,o);_cache['checker'].row(r);rr.append(r);calls+=1;work+=r['reads']+r['dispatches']+r['exposure_checks']
        entries.append(dict(aliases=e['aliases'],rows=rr))
    return dict(entries=entries,calls=calls,work=work,candidate_seconds=seconds,cpu_seconds=time.process_time()-cpu,independently_graded=calls)

def guard(directory,config,started):
    if time.monotonic()-started>=config['session_wall_seconds']:return 'wall'
    if shared.process_resources()>=config['memory_bytes']:return 'memory'
    if shutil.disk_usage(RUN).free<config['disk_free_floor_bytes']:return 'disk_free'
    if sum(p.stat().st_size for base in (RUN,OUT) for p in base.rglob('*') if p.is_file())>=config['storage_bytes']:return 'storage'

def check():
    r=json.loads((OUT/'registration.json').read_text())
    for p,h in r['files'].items():assert sha(ROOT/p)==h,p
    now=shared.source_manifest();assert all(now[k]==r[k] for k in ('python','dependencies'));return CONFIG

def upstream(cap,meta):
    pm={(m['base'],m['pose']):m for m in meta.values() if m['family']=='paired'}
    return {p for p in cap['pairs'] if (pm[p]['graph']!='fork' and pm[p]['prefix']>=1) or pm[p]['prefix']>=2}

def feature(rs,meta,ref):
    c=capabilities(rs,meta);new=upstream(c,meta)-upstream(ref,meta)
    pm={(m['base'],m['pose']):m for m in meta.values() if m['family']=='paired'}
    retention={k:len(c[k]&ref[k])/len(ref[k]) if ref[k] else None for k in ('pairs','corridors','ordinary_bases')}
    retained=all(x is None or x>=.9 for x in retention.values()) and not c['false']
    hard={p for p in c['pairs']-ref['pairs'] if pm[p]['graph']!='fork' or pm[p]['prefix']>=2}
    score=[len(new),len(hard),len(c['ordinary_bases']),len(c['pairs']),len(c['corridors']),-len(c['false']),*rank(rs,meta),-c['summary']['work']]
    return dict(metrics=c['summary'],retention=retention,retained=retained,new_upstream_pairs=len(new),new_upstream_contexts=len({pm[p]['template'] for p in new}),
        new_hard_pairs=len(hard),new_ordinary=len(c['ordinary_bases']-ref['ordinary_bases']),lost_ordinary=len(ref['ordinary_bases']-c['ordinary_bases']),score=score,
        acquisition_gate=retained and len(new)>=8 and len({pm[p]['template'] for p in new})>=2)

def select(items,rows,data,anchors):
    fs={};choices=[];refs=[capabilities(rows[f'anchor/{k}'],data['metadata']) for k in range(len(anchors))]
    lookup={i['id']:i for i in items}
    for k in range(len(anchors)):
        for arm in ('hold','zero','standard'):
            group=[i for i in items if i.get('anchor')==k and i.get('arm')==arm]
            for i in group:fs[i['id']]=feature(rows[i['id']],data['metadata'],refs[k])
            fallback=lookup[f'anchor/{k}'];fs[fallback['id']]=feature(rows[fallback['id']],data['metadata'],refs[k])
            for method in ('retained','exploratory'):
                allowed=[i for i in group+[fallback] if method=='exploratory' or fs[i['id']]['retained']]
                absent=not allowed
                if absent:allowed=[fallback]
                chosen=min(allowed,key=lambda i:(tuple(-v for v in fs[i['id']]['score']),i['id']))
                choices.append(dict(label=f'a{k}/{arm}/{method}',anchor=k,arm=arm,method=method,item=chosen,no_eligible=absent))
    randoms=[i for i in items if i['kind']=='random']
    chosen=min(randoms,key=lambda i:(tuple(-v for v in rank(rows[i['id']],data['metadata'])),i['id']))
    choices.append(dict(label='random/reference',anchor=None,arm='random',method='aggregate',item=chosen,no_eligible=False))
    return canonical(dict(choices=choices,features=fs))

def prepare():
    assert not OUT.exists();OUT.mkdir()
    seal=json.loads((PRIOR/'completion.json').read_text())
    for p,h in seal['files'].items():assert sha(ROOT/p)==h,p
    source=readz(PRIOR/'sources.json.gz');targets=['m3/modular/0/mixed/g669/b31','m3/modular/2/single/g800/b15'];anchors=[];refs=[]
    for k,i in enumerate(targets):
        item=source['items'][i];anchors.append(dict(id=i,base=item['genome'],source=item))
        for role,v in [('anchor',item),('root',source['items'][item['root']]),('parent',source['items'][item['parent']])]:
            refs.append(dict(id=f'{role}/{k}',model=embed(v['genome']),kind='reference',source=v['id']))
        refs.append(dict(id=f'legacy/{k}',model=dict(representation='modular',genome=item['genome']),kind='legacy_reference'))
    writej(OUT/'anchors.json',anchors);writez(OUT/'references.json.gz',refs+engineering());writej(OUT/'config.json',CONFIG)
    # Entirely excluded M2/M3 software fixtures; no fresh case generation.
    fixture=readz(ROOT/'results/wave_accessibility/fixture.json.gz');rng=random.Random(CONFIG['fixture_seed'])
    fake=[dict(id=f'fake/{k}',base=random_genome(rng).to_dict()) for k in range(2)]
    pp=pool(CONFIG['fixture_seed'],16,fake);assert pp==pool(CONFIG['fixture_seed'],16,fake)
    items=pp['items']+[dict(id=f'anchor/{k}',model=embed(a['base']),kind='reference') for k,a in enumerate(fake)]+engineering()
    ids=fixture['queries']['all'];mz=[m for m in fixture['mazes'] if m['case_id'] in ids];ts=tasks(items,ids)
    # Warm both implementations with production read-only signatures before timing.
    evaluate_task([dict(model=e['model'],queries=ids[:1],aliases=[e['id']]) for e in items[-4:]],mz,'warm')
    started=time.monotonic()
    with ProcessPoolExecutor(10,mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:rr=list(ex.map(evaluate_task,ts,[mz]*len(ts),['fixture']*len(ts)))
    rows={a:e['rows'] for r in rr for e in r['entries'] for a in e['aliases']}
    for c in engineering():assert all(r['optimal'] or r['no_path'] for r in rows[c['id']])
    chosen=select(items,rows,fixture,fake);assert chosen==select(items,rows,fixture,fake)
    # Exact real-anchor embedding equivalence is a discarded software check on old fixture only.
    embedding=evaluate_task([dict(model=e['model'],queries=ids,aliases=[e['id']]) for e in refs if e['id'].startswith(('anchor/','legacy/'))],mz,'embedding')
    er={a:e['rows'] for e in embedding['entries'] for a in e['aliases']}
    for k in range(2):
        for a,b in zip(er[f'legacy/{k}'],er[f'anchor/{k}']):assert dict(a,array_bytes=a['array_bytes']+64)==b
    writez(OUT/'software_fixture.json.gz',dict(pool=pp,fake_anchors=fake,receipts=rr,embedding=embedding,selection=chosen))
    writej(OUT/'profile.json',dict(calls=sum(r['calls'] for r in rr)+embedding['calls'],candidate_seconds=sum(r['candidate_seconds'] for r in rr)+embedding['candidate_seconds'],
        wall_seconds=time.monotonic()-started,queries=len(ids),pool_reproduced=True,selection_reproduced=True,controls_all_correct=True,embedding_all_fields_except_plus64_bytes=True,new_layouts=0,scientific_calls=0,
        additional_warmup_calls=4,total_preflight_calls=sum(r['calls'] for r in rr)+embedding['calls']+4,warmup_timing='Excluded from measured candidate/wall seconds; old excluded fixture, no scientific calls'))
    print('preflight complete',flush=True)

def register():
    assert not (OUT/'registration.json').exists();r=shared.source_manifest()
    paths=[*OUT.glob('*.json'),*OUT.glob('*.json.gz'),ROOT/'docs/HOLDING_ASSAY.md',ROOT/'tests/test_holding.py',PRIOR/'completion.json',PRIOR/'whole_layout_exclusions.json.gz']
    r['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths});r.update(phase='M5',scientific_calls=0)
    writej(OUT/'registration.json',r)

def make_pool():
    check();pushed(OUT/'registration.json');assert not (OUT/'pool.json.gz').exists()
    pp=pool(CONFIG['pool_seed'],CONFIG['draws'],json.loads((OUT/'anchors.json').read_text()));writez(OUT/'pool.json.gz',pp)
    ts=tasks(pp['items']+readz(OUT/'references.json.gz'),[])
    writej(OUT/'pool_counts.json',dict(aliases=len(pp['items']),physical_models=sum(map(len,ts)),max_screen_calls=sum(map(len,ts))*392,all_variants_fixed_before_fresh_screen=True))

def run_phase(final=False):
    check();pushed(OUT/('choices.json.gz' if final else 'pool.json.gz'))
    if final:assert json.loads((OUT/'screen_audit.json').read_text())['status']=='PASS'
    directory=RUN/('final' if final else 'screen');assert not (directory/'campaign.sqlite').exists(),'No silent restart'
    directory.mkdir(parents=True,exist_ok=True);started=time.monotonic();prior=set(readz(PRIOR/'whole_layout_exclusions.json.gz')['hashes']);config=dict(CONFIG)
    if final:
        previous=json.loads((OUT/'screen_session.json').read_text());prior.update(readz(OUT/'screen_cases.json.gz')['new_layouts'])
        for field in ('calls','work'):config[{'calls':'call_cap','work':'work_cap'}[field]]-=previous['usage'][field]
        config['session_wall_seconds']-=previous['wall_seconds'];items=readz(OUT/'choices.json.gz')['items'];data=confirmation(CONFIG['final_seed'],prior)
    else:
        pp=readz(OUT/'pool.json.gz');assert pp==pool(CONFIG['pool_seed'],CONFIG['draws'],json.loads((OUT/'anchors.json').read_text()))
        items=pp['items']+readz(OUT/'references.json.gz');data=screen(CONFIG['screen_seed'],prior)
    name='final' if final else 'screen';assert not (OUT/f'{name}_cases.json.gz').exists();writez(OUT/f'{name}_cases.json.gz',data)
    shared.evaluate_task=evaluate_task;shared.resource_reason=guard
    with writer_lock(directory):
        j=Journal(directory);j.initialize(config,dict(items_hash=hashed(packed(items))),prior);n=j.prepare(data,tasks(items,data['queries']['all']))
        with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:reason=shared.run_stage(j,n,data,ex,config,started,[False])
        if not reason:j.commit(n,j.state(),dict(no_evolution=True,no_adaptive_cases=True))
        writej(OUT/f'{name}_session.json',dict(status='complete' if reason is None else 'stopped',reason=reason,usage=j.get('usage'),wall_seconds=time.monotonic()-started,rss_peak_bytes=shared._peak_rss));j.close();assert reason is None,reason

def load(final=False):
    name='final' if final else 'screen';directory=RUN/name;c=sqlite3.connect(f'file:{directory}/campaign.sqlite?mode=ro',uri=True);rows={};models=[]
    assert c.execute('select count(*) from stages where complete=1').fetchone()[0]==1
    for spec,result,h in c.execute('select spec,result,result_hash from tasks order by n'):
        assert hashed(result)==h;ss=unpacked(spec);rr=unpacked(result)['entries'];assert len(ss)==len(rr)
        for e,r in zip(ss,rr):
            assert e['aliases']==r['aliases'] and e['queries']==[v['case'] for v in r['rows']]
            for i in e['aliases']:assert i not in rows;rows[i]=r['rows']
            models.append((e,r['rows']))
    c.close();return readz(OUT/f'{name}_cases.json.gz'),rows,models

def frozen_selection(data,rows):
    aa=json.loads((OUT/'anchors.json').read_text());items=readz(OUT/'pool.json.gz')['items']+readz(OUT/'references.json.gz');selected=select(items,rows,data,aa)
    allitems={i['id']:i for i in items};final={i['id']:i for i in readz(OUT/'references.json.gz')}
    for c in selected['choices']:
        i=c['item'];final[i['id']]=i
        if i.get('arm') in ('hold','zero'):
            twin=i['id'].replace('/hold/','/zero/') if i['arm']=='hold' else i['id'].replace('/zero/','/hold/');final[twin]=allitems[twin]
    return canonical(dict(items=[final[i] for i in sorted(final)],nominations=selected['choices'],features=selected['features']))

def freeze():
    check();assert not (OUT/'choices.json.gz').exists();data,rows,_=load();choices=frozen_selection(data,rows);writez(OUT/'choices.json.gz',choices)
    print('frozen',len(choices['items']),'final aliases',flush=True)

def final_summary(data,rows):
    choices=readz(OUT/'choices.json.gz');meta=data['metadata'];caps={i:capabilities(rs,meta) for i,rs in rows.items()};report=[]
    for c in choices['nominations']:
        i=c['item'];k=c['anchor'];v=feature(rows[i['id']],meta,caps[f'anchor/{k}']) if k is not None else dict(metrics=caps[i['id']]['summary'])
        changed=k is not None and i['model']!=next(e['model'] for e in choices['items'] if e['id']==f'anchor/{k}')
        if k is not None:v['acquisition_gate'] &= changed
        report.append(dict(label=c['label'],id=i['id'],anchor=k,arm=c['arm'],changed=changed,**v))
    return canonical(dict(label='M5 untouched confirmation after fixed nomination; related descendants, not independent runs',nominees=report,
        all_metrics={i:cap['summary'] for i,cap in caps.items()},upstream_pairs={i:len(upstream(cap,meta)) for i,cap in caps.items()},
        passing=[r['label'] for r in report if r.get('acquisition_gate')],
        limitations=['Shared ancestor and overlapping mutant neighborhoods; no long-run evolutionary or general-solver claim.','Fresh layouts in familiar grammar with correlated poses.','Equal logical allocations; physical work differs after exact-genotype deduplication.']))

def analyze():
    check();assert not (OUT/'summary.json').exists();data,rows,models=load(True)
    writej(OUT/'summary.json',final_summary(data,rows));writez(OUT/'final_responses.json.gz',dict(models=[dict(aliases=e['aliases'],rows=rs) for e,rs in models]))

def audit(final=False):
    check();name='final' if final else 'screen';assert not (OUT/f'{name}_audit.json').exists();started=time.monotonic();data,rows,models=load(final)
    previous=set(readz(PRIOR/'whole_layout_exclusions.json.gz')['hashes'])
    pp=readz(OUT/'pool.json.gz');assert pp==pool(CONFIG['pool_seed'],CONFIG['draws'],json.loads((OUT/'anchors.json').read_text()))
    if final:previous.update(readz(OUT/'screen_cases.json.gz')['new_layouts'])
    assert canonical((confirmation if final else screen)(CONFIG['final_seed'] if final else CONFIG['screen_seed'],previous))==data
    items=readz(OUT/'choices.json.gz')['items'] if final else pp['items']+readz(OUT/'references.json.gz')
    directory=RUN/name;c=sqlite3.connect(f'file:{directory}/campaign.sqlite?mode=ro',uri=True)
    assert [unpacked(r[0]) for r in c.execute('select spec from tasks order by n')]==tasks(items,data['queries']['all']);c.close()
    cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in data['queries']['all']]);checker=Checker(cases);grades=replays=0
    for e,rs in models:
        assert guard(directory,dict(CONFIG,session_wall_seconds=1800),started) is None
        org=organism(e['model']);key=hashed(packed(e['model']))
        for row in rs:
            checker.row(row);grades+=1
            if final or any(i.startswith(('anchor/','legacy/','control/')) for i in e['aliases']) or int(hashed(packed([key,row['case']])),16)%32==0:
                o=cases[row['case']];m=o.maze;assert record(org.react(m.cells,m.w,m.h,m.start,m.goal),o)==row;replays+=1
    for k in range(2):
        for a,b in zip(rows[f'legacy/{k}'],rows[f'anchor/{k}']):assert dict(a,array_bytes=a['array_bytes']+64)==b
    for ctrl in engineering():assert all(r['optimal'] or r['no_path'] for r in rows[ctrl['id']])
    if final:assert final_summary(data,rows)==json.loads((OUT/'summary.json').read_text())
    else:assert frozen_selection(data,rows)==readz(OUT/'choices.json.gz')
    with writer_lock(directory):
        j=Journal(directory);chain=j.verify_chain();assert not j.pending();assert grades==j.get('usage')['calls'];j.close()
    writej(OUT/f'{name}_audit.json',dict(status='PASS',independent_grades=grades,native_replays=replays,chain=chain,wall_seconds=time.monotonic()-started,
        pool_rng_corpus_tasks_regenerated=True,selection_replayed=not final,summary_replayed=final,embedding_verified=True,controls_all_correct=True,
        limitation='Shared native VM; independent raster grader. Screen fixed1/32 native samples plus complete references; final ALL-native.'))
    print(name,'AUDIT PASS',grades,replays,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','pool','screen','freeze','screen-audit','final','analyze','final-audit']);a=p.parse_args()
    {'prepare':prepare,'register':register,'pool':make_pool,'screen':run_phase,'freeze':freeze,'screen-audit':audit,'final':lambda:run_phase(True),'analyze':analyze,'final-audit':lambda:audit(True)}[a.action]()
