"""M32 bounded sequential repair: paired finite-panel diversity allocation.

Candidate inference and variation are unchanged M18/M19. Oracle rows only reach
selection/grading; no route or generated instruction enters a genome.
"""
import argparse, json, multiprocessing, os, random, shutil, sqlite3, subprocess, time, traceback
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from copy import deepcopy
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz, compressed_json as writez
from .deep_confirmation import writej
from .routing_transfer import canonical, sha
from .deep_campaign_store import packed, unpacked, hashed, writer_lock
from .referenced_campaign_store import Journal, load_layouts, write_reference
from . import deep_campaign as shared
from .connected_evaluation import evaluate_task
from .connected_genome import Genome
from .connected_evolution_genome import ordinary, random_genome
from .connected_evolution import pushed
from .copy_specialization import tasks
from .modular_pilot_search import tupled
from .breeding_allocation_metrics import capabilities_plus
from .transfer_retention_metrics import FIELDS, endpoint, compare, gate
from .transfer_retention import clock, elapsed, validate_panel
from .transfer_retention_data import fresh, observed_hashes
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .information_flow_m30 import geometry
from .foundation_data import transform_maze, layout_hash
from .datasets import manifest
from .evaluator import Oracle

OUT=ROOT/'results/repair_evolution_m32'
RUN=ROOT/'runs/repair_evolution_m32'
PREP=ROOT/'results/repair_evolution_m32_preparation'
PRIOR=ROOT/'results/output_access_m31'
RARE='m31/regulated/C6/draw0246'
FRESH_LEAD='m31/donor/C6/draw0297'
A0='m14/reference/anchor/0'
ARMS=('shared','niche')
CONFIG=dict(phase='M32',seed=2026102332,fresh_seed=20261023320,workers=10,
    population=96,populations=6,assessment_every=16,max_rounds=256,
    soft_wall_seconds=1500,session_wall_seconds=1800,final_wall_seconds=900,
    source_wall_seconds=900,audit_wall_seconds=3600,call_cap=30000000,work_cap=10**15,
    memory_bytes=8*2**30,storage_bytes=8*2**30,disk_free_floor_bytes=16*2**30,
    layout_base_manifest='results/repair_evolution_m32/exclusions.json')


def prior_check():
    seal=json.loads((PRIOR/'completion.json').read_text())
    for p,h in seal['files'].items(): assert sha(ROOT/p)==h,p
    for p,r in seal['local_records'].items(): assert sha(ROOT/p)==r['sha256'] and (ROOT/p).stat().st_size==r['bytes'],p
    return dict(files=len(seal['files']),local_records=len(seal['local_records']),sha256=sha(PRIOR/'completion.json'))


def storage(): return sum(p.stat().st_size for b in (OUT,RUN,PREP) for p in b.rglob('*') if p.is_file())
def guard(directory,config,started):
    if elapsed(started)>=config['session_wall_seconds']: return 'wall'
    if shared.process_resources()>=config['memory_bytes']: return 'memory'
    if storage()>=config['storage_bytes']: return 'storage'
    if shutil.disk_usage(RUN).free<config['disk_free_floor_bytes']: return 'disk_free'
def ensure(config,started): assert guard(RUN,config,started) is None,'M32 resource guard'
def generation_guard(config,started):
    last=[0.]
    def check_guard():
        assert elapsed(started)<config['session_wall_seconds'],'M32 generation wall'
        if time.monotonic()-last[0]>.5: ensure(config,started);last[0]=time.monotonic()
    return check_guard
def check():
    reg=json.loads((OUT/'registration.json').read_text())
    for p,h in reg['files'].items(): assert sha(ROOT/p)==h,p
    now=shared.source_manifest();assert all(reg[k]==now[k] for k in ('python','dependencies'))
    prior_check();return json.loads((OUT/'config.json').read_text())


def sources():
    pool=readz(PRIOR/'pool.json.gz');old=readz(PRIOR/'choices.json.gz')
    wanted=set(pool['historical_references'])|set(pool['control_ids'])|{c['id'] for c in old['choices']}|{RARE}
    items=[deepcopy(i) for i in pool['items'] if i['id'] in wanted]
    ids={i['id'] for i in items};assert ids==wanted
    anchors=[A0,'m14/reference/a1/standard/0191','m14/reference/a0/standard/0434','historical/M10/threshold']
    focal=[p['id'] for p in pool['parents'].values()]
    entries=anchors+focal+[RARE,FRESH_LEAD];assert len(set(entries))==9
    registry={i['id']:i for i in items};parents=pool['parents'];conditions={c['id']:c for c in pool['conditions']}
    roots={i:[i] for i in anchors}
    for p in parents.values(): roots[p['id']]=p['comparators']
    for i in (RARE,FRESH_LEAD):
        c=conditions[i];roots[i]=list(dict.fromkeys([i]+c['comparators']))
    assert set(x for rs in roots.values() for x in rs)<=ids
    for i in entries: assert registry[i]['model']['representation']=='connected'
    return canonical(dict(items=items,entries=entries,strict_roots=roots,
        historical_references=sorted(ids-set(pool['control_ids'])),control_ids=pool['control_ids'],
        M31_rare_event=conditions[RARE],M31_fresh_lead_event=conditions[FRESH_LEAD],
        inherited_M31_sources_sha256=sha(PRIOR/'sources.json.gz'),
        provenance='Four exact preserved random-origin anchors, three exact M30 parents, rare M31 development specialist and fixed fresh-pose lead. New matched forks; no whole old population resumed.'))


def founders(s=None):
    s=sources() if s is None else s;models={i['id']:i['model'] for i in s['items']};states=[]
    for rep in range(3):
        initial=[]
        for k in range(96):
            entry=s['entries'][k%9];identity=entry if k<9 else f'm32/initial/{rep}/{k}'
            initial.append(dict(id=identity,model=models[entry],entry=entry,parent=None if k<9 else entry,
                entry_model=models[entry],parent_model=None if k<9 else models[entry],protected=k<9,
                birth=0,depth=0,changed_depth=0,origin='preserved_random_origin'))
        for arm in ARMS:
            states.append(dict(name=f'{rep}/{arm}',replicate=rep,arm=arm,generation=0,assessment_generation=-1,
                population=deepcopy(initial),archive=[],nominees=[],rng=random.Random(CONFIG['seed']+rep).getstate()))
    return canonical(states)


def old_panel():
    d=deepcopy(readz(PRIOR/'development_panel.json.gz'));d.pop('expected_source_rows',None)
    d.update(generation=0,new_layouts=[],kind='assessment',used_development=True);return canonical(d)


def pick_group(groups,count,rng):
    keys=sorted(groups);rng.shuffle(keys);chosen=keys[:count]
    assert len(chosen)==count
    return [c for k in chosen for c in sorted(groups[k])]


def training(g,panel=None):
    d=old_panel() if panel is None else deepcopy(panel);meta=d['metadata'];ids=d['queries']['all']
    rng=random.Random(CONFIG['seed']*10000+g);groups=defaultdict(list)
    # Complete controlled swaps: sixteen contrasts, two inputs each. Repeated
    # geometry/symmetry aliases remain visible, never treated as independent N.
    swaps=[c for c in d['contrasts'] if c['kind']=='route_swap'];rng.shuffle(swaps)
    selected=[x for c in swaps[:16] for x in (c['a'],c['b'])]
    ordinary_groups=defaultdict(list);pair_groups=defaultdict(list)
    for c in ids:
        m=meta[c];f=m['family']
        if f in ('ordinary_perfect','ordinary_random'): ordinary_groups[m['base']].append(c)
        elif f=='paired':pair_groups[(m['base'],m['pose'])].append(c)
    # The panel has two fixed poses per ordinary base and two alternatives per
    # paired base/pose. Keep complete units for whole-solution fitness.
    ordinary_groups={b:cs for b,cs in ordinary_groups.items() if len(cs)==2}
    pair_groups={b:cs for b,cs in pair_groups.items() if len(cs)==2}
    selected+=pick_group(ordinary_groups,16,rng)+pick_group(pair_groups,4,rng)
    for family,count in [('corridor',16),('no_path',8)]:
        options=[c for c in ids if (meta[c]['family']=='corridor' if family=='corridor' else not meta[c]['path'])]
        rng.shuffle(options);selected+=options[:count]
    assert len(selected)==len(set(selected))==96
    return subset(d,selected,kind='train',generation=g)


def subset(d,ids,**changes):
    result=deepcopy(d);wanted=set(ids);result['queries']={'all':list(ids)}
    result['mazes']=[m for m in result['mazes'] if m['case_id'] in wanted]
    result['metadata']={i:result['metadata'][i] for i in ids}
    result['contrasts']=[c for c in result.get('contrasts',[]) if {c['a'],c['b']}<=wanted]
    result.update(changes);return canonical(result)


def caps_rows(rows,data):
    meta={c:data['metadata'][c] for c in data['queries']['all']}
    return {i:capabilities_plus(rs,meta) for i,rs in rows.items()}


def controlled(c,data):
    swaps=[x for x in data.get('contrasts',[]) if x['kind']=='route_swap']
    success={x for x in data['queries']['all'] if data['metadata'][x]['family'].startswith('controlled_') and data['metadata'][x]['path'] and x in c['success']}
    return sum(x['a'] in c['success'] and x['b'] in c['success'] for x in swaps),success


def merit(i,caps,data):
    c=caps[i['id']];entry=caps[i['entry']];pairs,success=controlled(c,data)
    fractions=[len(c[k]&entry[k])/len(entry[k]) for k in FIELDS if entry[k]]
    ordinary_meta={m['base']:m for m in data['metadata'].values() if m['family'] in ('ordinary_perfect','ordinary_random')}
    long=sum(len(ordinary_meta[b]['path'])-1>=8 for b in c['ordinary_bases'])
    return (not c['false'],pairs,long,min(fractions,default=1.),
        len(c['ordinary_bases']),len(c['pairs']),len(c['corridors']),len(success),len(c['correct_no_path']))


def choose(items,key): return sorted(items,key=lambda i:(tuple(-x for x in key(i)),i['id']))[0]
def nomination(items,rows,data,s):
    caps=caps_rows(rows,data);reference=s['historical_references'];a0=caps[A0]
    portfolio={k:set().union(*(caps[i][k] for i in reference)) for k in (*FIELDS,'success','false')}
    def detail(i):
        c=caps[i['id']];comparators=s['strict_roots'].get(i['entry'],[i['entry']])
        if i['parent'] and i['parent'] in caps:comparators=list(dict.fromkeys(comparators+[i['parent']]))
        e=endpoint(c,[caps[p] for p in comparators],portfolio,a0,data['metadata'],i['changed_depth']>0)
        pairs,success=controlled(c,data)
        return dict(id=i['id'],entry=i['entry'],parent=i['parent'],depth=i['depth'],changed_depth=i['changed_depth'],
            endpoint=e,controlled_pairs=pairs,controlled_individuals=len(success),metrics=c['summary'],
            comparisons={p:compare(c,caps[p]) for p in comparators},
            correct_inputs=len(c['success']),false_no_path=len(c['false']),no_path=len(c['correct_no_path']))
    details={i['id']:detail(i) for i in items}
    keys={
        'INTEGRATED':lambda i:(details[i['id']]['endpoint']['gate']['passes'],details[i['id']]['endpoint']['raw_novel_complete8'],*merit(i,caps,data)),
        'REPAIR':lambda i:(*controlled(caps[i['id']],data)[:1],len(controlled(caps[i['id']],data)[1]),*merit(i,caps,data)),
        'ORDINARY':lambda i:(len(caps[i['id']]['ordinary_bases']),*merit(i,caps,data))}
    return [dict(role=role,item=choose(items,key),development=details[choose(items,key)['id']]) for role,key in keys.items()]


def row_values(rows):
    # Complete solutions only. No partial-pixel or empty-output reward.
    return [int(r['optimal'] or r['no_path'])-int(r['reachable'] and r['status']=='no_path') for r in rows]
def lexicase(rng,items,rows):
    pool=list(items);vals={i['id']:row_values(rows[i['id']]) for i in pool};columns=list(range(len(rows[pool[0]['id']])));rng.shuffle(columns)
    for c in columns:
        best=max(vals[i['id']][c] for i in pool)
        pool=[i for i in pool if vals[i['id']][c]==best]
        if len(pool)==1:return pool[0]
    return rng.choice(pool)


def retain(items,rows,data,rng,arm):
    caps=caps_rows(rows,data);ordered=sorted(items,key=lambda i:(tuple(-v for v in merit(i,caps,data)),i['id']))
    protected=[i for i in items if i['protected']]
    assert len(protected)==9
    chosen=protected.copy();left=[i for i in ordered if i not in chosen];chosen+=left[:8];left=left[8:]
    niche=[];profiles={}
    if arm=='niche':
        for i in left:
            c=caps[i['id']];_,success=controlled(c,data)
            # Full correct reachable responses only, including one-sided ones.
            # False no-path excludes a profile; loss of true no-path is disclosed
            # but allowed in this bounded intermediate niche.
            if not success or c['false']:continue
            profile=tuple(sorted(success))
            profiles.setdefault(profile,[]).append(i)
        cells=[rng.choice(profiles[k]) for k in sorted(profiles)];rng.shuffle(cells);niche=cells[:8]
        chosen+=niche;left=[i for i in left if i not in niche]
    covered=set().union(*(caps[i['id']]['success'] for i in chosen))
    for _ in range(12):
        if len(chosen)>=44 or not left:break
        best=choose(left,lambda i:(len(caps[i['id']]['success']-covered),*merit(i,caps,data)))
        if not caps[best['id']]['success']-covered:break
        chosen.append(best);left.remove(best);covered|=caps[best['id']]['success']
    while len(chosen)<44:
        best=lexicase(rng,left,rows);chosen.append(best);left.remove(best)
    return chosen,niche,dict(distinct_niche_profiles=len(profiles),niche=[i['id'] for i in niche],survivors=[i['id'] for i in chosen])


def candidate_items(state,assessment=False):
    groups=[state['population']]
    if assessment:groups.append(state['archive'])
    unique={i['id']:i for group in groups for i in group};return [unique[i] for i in sorted(unique)]


def task_specs(states,data,assessment=False,s=None):
    s=readz(OUT/'sources.json.gz') if s is None else s
    # References/entries are present every panel for same-case comparisons, but
    # external controls and archive aliases can never breed.
    items={i['id']:dict(id=i['id'],model=i['model']) for i in s['items']}
    for st in states:
        for i in candidate_items(st,assessment):
            if i['id'] in items:assert items[i['id']]['model']==i['model']
            items[i['id']]=dict(id=i['id'],model=i['model'])
            items[i['entry']]=dict(id=i['entry'],model=i['entry_model'])
            if assessment and i['parent']:items[i['parent']]=dict(id=i['parent'],model=i['parent_model'])
    return tasks([items[i] for i in sorted(items)],data['queries']['all'])


def decoded_rows(results):
    rows={}
    for r in results:
        for e in r['entries']:
            for i in e['aliases']:assert i not in rows;rows[i]=e['rows']
    return rows


def transition(states,data,results,s=None):
    s=readz(OUT/'sources.json.gz') if s is None else s;rows=decoded_rows(results);new=deepcopy(states);decisions=[]
    for st in new:
        rng=random.Random();rng.setstate(tupled(st['rng']));items=candidate_items(st,data['kind']=='assessment')
        if data['kind']=='assessment':
            nominees=nomination(items,rows,data,s);st['nominees']=nominees
            caps=caps_rows(rows,data);ranked=sorted(items,key=lambda i:(tuple(-v for v in merit(i,caps,data)),i['id']))
            keep={x['item']['id']:x['item'] for x in nominees}
            # Up to eight exact complete-solution profiles, bounded archive.
            profiles=set()
            for i in ranked:
                profile=tuple(sorted(caps[i['id']]['success']))
                if profile not in profiles and len(keep)<8:keep[i['id']]=i;profiles.add(profile)
            st['archive']=[keep[k] for k in sorted(keep)];st['assessment_generation']=st['generation']
            decisions.append(dict(name=st['name'],nominees=nominees,archive=[i['id'] for i in st['archive']],births=[]))
        else:
            survivors,niche,log=retain(st['population'],rows,data,rng,st['arm']);births=[]
            for b in range(52):
                identity=f'm32/{st["name"]}/g{st["generation"]+1}/b{b}'
                if b<7:
                    g=random_genome(rng);entry=identity;parent=None;depth=changed=0;event=None;policy='random_immigrant'
                    entry_model=dict(representation='connected',genome=g.to_dict());parent_model=None
                    # Immigrants serve as their own phase entry from first exposure.
                else:
                    p=niche[(b-7)%len(niche)] if niche and b<15 else lexicase(rng,survivors,rows)
                    old=Genome.from_dict(p['model']['genome']);g,event=ordinary(old,rng)
                    entry=p['entry'];parent=p['id'];depth=p['depth']+1;changed=p['changed_depth']+int(g.to_dict()!=old.to_dict())
                    entry_model=p['entry_model'];parent_model=p['model']
                    policy='niche_cycle' if niche and b<15 else 'shared_lexicase'
                item=dict(id=identity,model=dict(representation='connected',genome=g.to_dict()),entry=entry,parent=parent,
                    entry_model=entry_model,parent_model=parent_model,protected=False,
                    depth=depth,changed_depth=changed,birth=st['generation']+1,origin='M32_random_origin' if parent is None else p['origin'])
                births.append(dict(item=item,event=event,parent_policy=policy))
            st['population']=survivors+[b['item'] for b in births];st['generation']+=1
            decisions.append(dict(name=st['name'],**log,births=births))
        st['rng']=rng.getstate();assert len(st['population'])==len({i['id'] for i in st['population']})==96
    return canonical(new),canonical(decisions)


def readonly(name):
    con=sqlite3.connect(f'file:{RUN}/{name}/campaign.sqlite?mode=ro',uri=True);con.execute('PRAGMA query_only=ON');con.execute('BEGIN')
    j=Journal.__new__(Journal);j.db=con;j.directory=RUN/name
    return j


def execute(items,data,name,config,previous,start):
    shared.evaluate_task=evaluate_task;shared.resource_reason=guard;directory=RUN/name
    assert not (directory/'campaign.sqlite').exists()
    with writer_lock(directory):
        j=Journal(directory);j.initialize(config,dict(no_evolution=True,name=name),previous)
        try:
            n=j.prepare(data,tasks(items,data['queries']['all']))
            with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
                reason=shared.run_stage(j,n,data,ex,config,start,[False]);assert reason is None,reason
            ensure(config,start);j.commit(n,j.state(),dict(name=name))
            return dict(status='complete',usage=j.get('usage'),wall_seconds=elapsed(start),rss_peak_bytes=shared._peak_rss,chain=j.verify_chain(),
                aliases=len(items),queries=len(data['queries']['all']),physical_models=sum(map(len,tasks(items,[]))))
        finally:j.close()


def collect_registry(j,s):
    reg={}
    for st in founders(s):
        for i in st['population']:reg[i['id']]=dict(item=i,event=None,phase='M32_entry')
    for blob, in j.db.execute('select decision from stages where complete=1 order by n'):
        for d in unpacked(blob):
            for b in d['births']:
                i=b['item'];assert i['id'] not in reg;reg[i['id']]=dict(b,phase='M32_birth')
    return reg


def freeze(j,s):
    states=j.state();registry=collect_registry(j,s);items={i['id']:dict(id=i['id'],model=i['model']) for i in s['items']};choices=[];needed=set()
    for st in states:
        for c in st['nominees']:
            i=c['item'];choices.append(dict(population=st['name'],replicate=st['replicate'],arm=st['arm'],role=c['role'],**c))
            for identity in (i['id'],i['entry'],i['parent']):
                if identity:items[identity]=dict(id=identity,model=registry[identity]['item']['model'])
            cursor=i['id']
            while cursor and cursor not in needed:
                needed.add(cursor);cursor=registry[cursor]['item']['parent']
    writez(OUT/'choices.json.gz',dict(choices=choices,items=[items[i] for i in sorted(items)],historical_references=s['historical_references'],control_ids=s['control_ids'],chain=j.verify_chain()))
    writez(OUT/'ancestry.json.gz',{i:registry[i] for i in sorted(needed)})
    writez(OUT/'final_states.json.gz',states)


def search():
    config=check();pushed(OUT/'registration.json');start=clock();s=readz(OUT/'sources.json.gz');previous=load_layouts(OUT/'exclusions.json');directory=RUN/'search'
    assert not (directory/'campaign.sqlite').exists();shared.evaluate_task=evaluate_task;shared.resource_reason=guard
    with writer_lock(directory):
        j=Journal(directory);j.initialize(config,readz(OUT/'founders.json.gz'),previous)
        try:
            panel=readz(OUT/'development_panel.json.gz')
            with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
                stop=None
                while True:
                    states=j.state();g=states[0]['generation'];assert all(st['generation']==g for st in states)
                    if stop is None:
                        if elapsed(start)>=config['soft_wall_seconds']:stop='soft_wall'
                        elif g>=config['max_rounds']:stop='round_ceiling'
                        elif j.get('usage')['calls']+2000000>config['call_cap']:stop='call_reserve'
                    assessment=(g%config['assessment_every']==0 or stop is not None) and states[0]['assessment_generation']!=g
                    if stop is not None and not assessment:break
                    data=dict(deepcopy(panel),generation=g) if assessment else training(g,panel)
                    specs=task_specs(states,data,assessment,s);n=j.prepare(data,specs)
                    reason=shared.run_stage(j,n,data,ex,config,start,[False]);assert reason is None,reason
                    state,decision=transition(states,data,j.results(n),s);j.commit(n,state,decision)
                    print(json.dumps(dict(stage=n,kind=data['kind'],generation=g,usage=j.get('usage'),elapsed_seconds=elapsed(start),rss_peak_bytes=shared._peak_rss)),flush=True)
            ensure(config,start);freeze(j,s);j.put('finished',True);j.db.commit()
            writej(OUT/'search_session.json',dict(status='complete',reason=stop,generation=j.state()[0]['generation'],usage=j.get('usage'),wall_seconds=elapsed(start),rss_peak_bytes=shared._peak_rss,chain=j.verify_chain()))
        finally:j.close()


def independent_source_panel():
    # Reused generator family, fresh source-measurement cases; neither search nor
    # final selection can see responses. Source measurement is not final proof.
    config=check();start=clock();config=dict(config,session_wall_seconds=config['source_wall_seconds'])
    previous=load_layouts(OUT/'exclusions.json');pushed(OUT/'registration.json')
    data=new_panel('source',previous,config,start)
    writez(OUT/'source_panel.json.gz',data)
    result=execute(readz(OUT/'sources.json.gz')['items'],data,'source',config,previous,start)
    writej(OUT/'source_session.json',result)


def final():
    config=check();config=dict(config,session_wall_seconds=config['final_wall_seconds']);start=clock();pushed(OUT/'choices.json.gz')
    assert json.loads((OUT/'search_audit.json').read_text())['status']=='PASS'
    previous=load_layouts(OUT/'exclusions.json')|set(readz(OUT/'source_panel.json.gz')['new_layouts'])
    # Journal begins at an explicit immutable base including source measurement.
    write_reference(OUT/'final_exclusions.json',OUT/'exclusions.json',previous)
    config['layout_base_manifest']=str((OUT/'final_exclusions.json').relative_to(ROOT))
    data=new_panel('final',previous,config,start);writez(OUT/'fresh_panel.json.gz',data)
    result=execute(readz(OUT/'choices.json.gz')['items'],data,'final',config,previous,start);writej(OUT/'final_session.json',result)


def phase_observations(name,audit=False):
    prefix=name+('_audit' if audit else '')
    return observed_hashes(RUN/(prefix+'_generation_layouts.jsonl'))|observed_hashes(RUN/(prefix+'_controlled_layouts.jsonl'))


def new_panel(name,previous,config,start,audit=False):
    prefix=name+('_audit' if audit else '');seed=config['seed']*10+1 if name=='source' else config['fresh_seed']
    data=fresh(seed,previous,RUN/(prefix+'_generation_layouts.jsonl'),generation_guard(config,start));validate_panel(data,previous)
    generated=set();contrasts=[];sizes=(15,19,23) if name=='source' else (25,29,33)
    # Fixed full family, no successful-genome filtering or favorable retry.
    with (RUN/(prefix+'_controlled_layouts.jsonl')).open('x') as log:
        for n in sizes:
            for gy in (6,n-7):
                bypose=defaultdict(dict)
                for variant in ('A','B','both','neither','clutter0','clutter1'):
                    base,_=geometry(n,gy,variant)
                    for pose in range(8):
                        ensure(config,start);m=transform_maze(base,pose)
                        cid=f'M32/{name}/n{n}/gate{gy}/{variant}/pose{pose}'
                        from dataclasses import replace
                        m=replace(m,case_id=cid,seed=seed,split='confirmation');o=Oracle.build(m);h=layout_hash(m)
                        assert h not in previous and h not in set(data['new_layouts']),'Fixed controlled family overlaps excluded history; no silent retry'
                        if h not in generated:
                            log.write(json.dumps([h])+'\n');log.flush();os.fsync(log.fileno());generated.add(h)
                        data['mazes']+=manifest([o]);data['queries']['all'].append(cid)
                        data['metadata'][cid]=dict(family='controlled_'+variant,path=o.path,size=n,pose=pose,variant=variant,gate_y=gy,panel_group='controlled',length_bin='none' if not o.path else 'long')
                        bypose[pose][variant]=cid
                for pose,cs in sorted(bypose.items()):contrasts.append(dict(id=f'{name}/{n}/{gy}/{pose}',kind='route_swap',a=cs['A'],b=cs['B']))
    data.update(contrasts=contrasts,new_layouts=sorted(set(data['new_layouts'])|generated),controlled_queries=288)
    assert phase_observations(name,audit)==set(data['new_layouts'])
    return canonical(data)


def summarize(data,rows,choices,s):
    caps=caps_rows(rows,data);portfolio={k:set().union(*(caps[i][k] for i in s['historical_references'])) for k in (*FIELDS,'success','false')};a0=caps[A0];conditions=[]
    for c in choices['choices']:
        item=c['item'];i=item['id'];comparators=list(dict.fromkeys(s['strict_roots'].get(item['entry'],[item['entry']])+[x for x in (item['entry'],item['parent']) if x]))
        e=endpoint(caps[i],[caps[p] for p in comparators],portfolio,a0,data['metadata'],item['changed_depth']>0)
        parent_gate=gate(caps[i],[caps[item['parent']]] if item['parent'] else [caps[item['entry']]],a0,item['changed_depth']>0)
        cs,ss=controlled(caps[i],data);conditions.append(dict(population=c['population'],replicate=c['replicate'],arm=c['arm'],role=c['role'],id=i,entry=item['entry'],parent=item['parent'],depth=item['depth'],changed_depth=item['changed_depth'],
            **e,actual_parent_only_gate=parent_gate,comparisons={p:compare(caps[i],caps[p]) for p in comparators},metrics=caps[i]['summary'],controlled_pairs=cs,controlled_individuals=len(ss),
            new_individual_inputs=sorted(caps[i]['success']-portfolio['success']),status_counts=dict(Counter(r['status'] for r in rows[i]))))
    pairs=[]
    for rep in range(3):
        scores={a:next(c['primary_score'] for c in conditions if c['replicate']==rep and c['arm']==a and c['role']=='INTEGRATED') for a in ARMS}
        pairs.append(dict(replicate=rep,**scores,difference=scores['niche']-scores['shared']))
    ordinary={m['base']:m for m in data['metadata'].values() if m['family'] in ('ordinary_perfect','ordinary_random')};strata={}
    for i,cap in caps.items():
        bins=defaultdict(lambda:dict(bases=0,complete=0))
        for b,m in ordinary.items():
            edges=len(m['path'])-1;k=f'{m["family"]}/{m.get("size")}/'+('0-7' if edges<8 else '8-15' if edges<16 else '16plus')
            bins[k]['bases']+=1;bins[k]['complete']+=int(b in cap['ordinary_bases'])
        strata[i]=dict(bins)
    return canonical(dict(conditions=conditions,policy_comparison=dict(pairs=pairs,positive_pairs=sum(p['difference']>0 for p in pairs),sum_difference=sum(p['difference'] for p in pairs),descriptive_support=sum(p['difference']>0 for p in pairs)>=2 and sum(p['difference'] for p in pairs)>0),
        ordinary_length_strata=strata,ordinary_bases=len(ordinary),ordinary8_bases=sum(len(m['path'])-1>=8 for m in ordinary.values()),ordinary16_bases=sum(len(m['path'])-1>=16 for m in ordinary.values()),
        all_model_metrics={i:c['summary'] for i,c in caps.items()},queries=len(data['queries']['all']),independent_confirmation=True,
        limitation='Related matched forks and fixed used development curriculum; equal nominal rounds/slots not equal CPU. No significance, general-solver or speed claim. No secondary role substitution.'))


def load_finite(name):
    j=readonly(name);assert not j.pending() and j.get('latest')==0
    data=unpacked(j.db.execute('select input from stages where n=0').fetchone()[0]);results=j.results(0);rows=decoded_rows(results);usage=j.get('usage');chain=j.verify_chain();j.close()
    return data,rows,results,usage,chain


def analyze():
    check();assert not (OUT/'summary.json').exists();data,rows,_,usage,chain=load_finite('final')
    result=summarize(data,rows,readz(OUT/'choices.json.gz'),readz(OUT/'sources.json.gz'));result.update(usage=usage,chain=chain)
    writej(OUT/'summary.json',result);writez(OUT/'final_responses.json.gz',rows)


def audit(name):
    config=check();config=dict(config,session_wall_seconds=config['audit_wall_seconds']);start=clock();path=OUT/(name+'_audit.json');assert not path.exists()
    assert sources()==readz(OUT/'sources.json.gz') and founders()==readz(OUT/'founders.json.gz') and old_panel()==readz(OUT/'development_panel.json.gz')
    s=readz(OUT/'sources.json.gz');j=readonly(name);chain=j.verify_chain();assert not j.pending();states=readz(OUT/'founders.json.gz');calls=work=grades=baseline_calls=0;cpu=0.
    source_manifest=OUT/'final_exclusions.json' if name=='final' else OUT/'exclusions.json';previous=load_layouts(source_manifest)
    if name in ('source','final'):
        expected=new_panel(name,previous,config,start,True)
    reserves=RUN/(name+'_audit_reservations.jsonl');receipts=RUN/(name+'_audit_receipts.jsonl')
    with reserves.open('x') as rf,receipts.open('x') as of,ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
        for n,blob in j.db.execute('select n,input from stages where complete=1 order by n'):
            data=unpacked(blob)
            if name=='search':
                expected=dict(deepcopy(readz(OUT/'development_panel.json.gz')),generation=states[0]['generation']) if data['kind']=='assessment' else training(states[0]['generation'])
                specs=task_specs(states,data,data['kind']=='assessment',s)
            else:specs=tasks((s if name=='source' else readz(OUT/'choices.json.gz'))['items'],data['queries']['all'])
            assert canonical(expected)==data
            assert [sp for _,sp,_ in j.tasks(n)]==specs
            cases=cases_from_manifest(data['mazes']);checker=Checker(cases);sizes={c:len(o.maze.cells) for c,o in cases.items()}
            todo=list(enumerate(specs));pending={};rc=rw=0;old_results=j.results(n)
            while todo or pending:
                ensure(config,start)
                while todo and len(pending)<config['workers']:
                    k,spec=todo.pop(0);cc,ww=shared.reservation(spec,sizes);assert calls+rc+cc<=config['call_cap'] and work+rw+ww<=config['work_cap']
                    rf.write(json.dumps(dict(stage=n,task=k,calls=cc,reserved_work=ww,spec_sha256=hashed(packed(spec))))+'\n');rf.flush();os.fsync(rf.fileno())
                    pending[ex.submit(evaluate_task,spec,data['mazes'],hashed(packed(data['mazes'])))]=(k,cc,ww);rc+=cc;rw+=ww
                done,_=wait(pending,timeout=.5,return_when=FIRST_COMPLETED)
                for f in done:
                    k,cc,ww=pending.pop(f);actual=f.result();old=old_results[k]
                    assert actual['calls']==old['calls']==cc and actual['work']==old['work']<=ww
                    for a,b in zip(actual['entries'],old['entries']):
                        assert a['aliases']==b['aliases'] and a['rows']==b['rows'] and a['work']==b['work']
                        for row in b['rows']:
                            checker.row(row);grades+=1
                            if set(b['aliases'])&set(s['control_ids']):assert row['optimal'] or row['no_path']
                    calls+=cc;work+=actual['work'];cpu+=actual['cpu_seconds'];rc-=cc;rw-=ww
                    of.write(json.dumps(dict(stage=n,task=k,calls=cc,work=actual['work'],all_native_exact=True))+'\n');of.flush();os.fsync(of.fileno())
            if name=='search':
                states,decisions=transition(states,data,old_results,s)
                rec=j.db.execute('select decision,state_hash from stages where n=?',(n,)).fetchone()
                assert decisions==unpacked(rec[0]) and hashed(packed(states))==rec[1]
            # Conventional checks on unique assessment/source/final cases only.
            if n==0:
                from .baselines import baseline
                from .foundation_pair_confirm import normal_row
                for method in ('compiled_bfs','compiled_astar','wave_bit'):
                    for o in cases.values():
                        r=canonical(normal_row(baseline(method,o.maze.cells,o.maze.w,o.maze.h,o.maze.start,o.maze.goal),o));checker.row(r);assert r['optimal'] or r['no_path'];baseline_calls+=1
    assert calls==grades==j.get('usage')['calls'] and work==j.get('usage')['work']
    if name=='search':
        assert states==j.state()==readz(OUT/'final_states.json.gz')
        # Freeze is reconstructed without writing/renominating final choices.
        choices=readz(OUT/'choices.json.gz')['choices']
        assert [(c['population'],c['role'],c['item'],c['development']) for c in choices]==[(st['name'],c['role'],c['item'],c['development']) for st in states for c in st['nominees']]
    if name=='final':
        dd,rr,_,uu,ch=load_finite('final');summary=summarize(dd,rr,readz(OUT/'choices.json.gz'),s);summary.update(usage=uu,chain=ch)
        assert summary==json.loads((OUT/'summary.json').read_text())
    j.close();ensure(config,start);writej(path,dict(status='PASS',all_native_replays=calls,independent_grades=grades,counted_work=work,worker_cpu_seconds=cpu,wall_seconds=elapsed(start),rss_peak_bytes=shared._peak_rss,chain=chain,
        all_sources_rng_tasks_selection_replayed=True,all_controls_correct=True,conventional_calls=baseline_calls,prior_hashes=prior_check(),limitation='Shared unchanged VM/operator, independent raster grader; not a second independent full VM or latency benchmark.'))


def prepare():
    assert not OUT.exists();prior=prior_check();OUT.mkdir();RUN.mkdir(parents=True,exist_ok=True)
    assert shutil.disk_usage(RUN).free>=CONFIG['disk_free_floor_bytes']+CONFIG['storage_bytes']
    s=sources();writez(OUT/'sources.json.gz',s);writez(OUT/'founders.json.gz',founders(s));writez(OUT/'development_panel.json.gz',old_panel());writej(OUT/'config.json',CONFIG)
    write_reference(OUT/'exclusions.json',PRIOR/'whole_layout_exclusions.json',load_layouts(PRIOR/'whole_layout_exclusions.json'))
    writej(OUT/'preparation.json',dict(prior=prior,scientific_calls=0,new_scientific_cases=0,old_histories_unchanged=True,founders_per_population=96,protected_entries=9,reference_aliases=len(s['items'])))


def preflight():
    assert not (OUT/'registration.json').exists() and not (OUT/'preflight.json').exists();start=clock();s=readz(OUT/'sources.json.gz');states=founders(s)
    fixture=readz(ROOT/'results/transfer_retention_m27/discarded_fixture.json.gz');ids=fixture['queries']['all'][:4]
    data=subset(fixture,ids,kind='train',generation=0,new_layouts=[]);previous=load_layouts(OUT/'exclusions.json');config=dict(CONFIG,workers=2,session_wall_seconds=600)
    specs=task_specs(states,data,True,s);items=[dict(id=i,model=e['model']) for spec in specs for e in spec for i in e['aliases']]
    result=execute(items,data,'fixture',config,previous,start)
    _,rows,results,_,_=load_finite('fixture')
    assessed=deepcopy(data);assessed['kind']='assessment'
    aa,ad=transition(states,assessed,results,s);assert (aa,ad)==transition(states,assessed,results,s)
    bb,bd=transition(aa,data,results,s);assert (bb,bd)==transition(aa,data,results,s)
    assert all(st['generation']==1 and len(st['population'])==96 for st in bb)
    specs2=task_specs(bb,assessed,True,s);items2=[dict(id=i,model=e['model']) for spec in specs2 for e in spec for i in e['aliases']]
    second=execute(items2,assessed,'fixture_second',config,previous,start)
    _,rows2,results2,_,_=load_finite('fixture_second');cc,cd=transition(bb,assessed,results2,s)
    assert (cc,cd)==transition(bb,assessed,results2,s) and all(len(st['nominees'])==3 for st in cc)
    # Genuine two sequential ordinary births and exact RNG reproduction on the
    # unchanged VM; does not consume any scientific source/final case.
    st=states[0];rng=random.Random();rng.setstate(tupled(st['rng']));g=Genome.from_dict(st['population'][0]['model']['genome']);events=[]
    for _ in range(2):g,e=ordinary(g,rng);events.append(e)
    original=Genome.from_dict(st['population'][0]['model']['genome']);rr=random.Random();rr.setstate(tupled(st['rng']));gg=original
    for e in events:gg,ee=ordinary(gg,rr);assert e==ee
    assert gg==g and rr.getstate()==rng.getstate()
    assert all(all(r['optimal'] or r['no_path'] for r in rows[i]) for i in s['control_ids'])
    writej(OUT/'preflight.json',dict(status='PASS',native=result,second_native=second,old_discarded_inputs=ids,sequential_variation_rng_replayed=True,assessment_train_assessment_replayed=True,all_intact_controls_correct=True,scientific_calls=0,wall_seconds=elapsed(start)))
    writej(OUT/'preparation_local_records.json',{str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in RUN.rglob('*.sqlite')})


def register():
    assert not (OUT/'registration.json').exists();assert json.loads((OUT/'preflight.json').read_text())['status']=='PASS'
    reg=shared.source_manifest();paths=[p for b in (OUT,PREP) for p in b.rglob('*') if p.is_file()]
    paths += [ROOT/'docs/REPAIR_EVOLUTION_M32.md',ROOT/'tests/test_repair_evolution_m32.py',ROOT/'tools/run_m32_workflow.py',PRIOR/'completion.json']
    reg['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths});reg.update(phase='M32',scientific_calls=0,new_scientific_cases=0);writej(OUT/'registration.json',reg)


def status():
    for name in ('source','search','final'):
        if (RUN/name/'campaign.sqlite').exists():
            j=readonly(name);print(name,json.dumps(dict(latest=j.get('latest'),usage=j.get('usage'),pending=None if not j.pending() else j.pending()[0],generation=j.state()[0]['generation'] if name=='search' else None)));j.close()


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','preflight','register','source','search','audit_source','audit_search','final','analyze','audit_final','status']);a=p.parse_args()
    try:
        if a.action=='source':independent_source_panel()
        elif a.action.startswith('audit_'):audit(a.action[6:])
        else:globals()[a.action]()
    except BaseException:
        d=OUT if OUT.exists() else PREP;d.mkdir(parents=True,exist_ok=True);writej(d/(a.action+'_failure_'+str(time.time_ns())+'.json'),dict(traceback=traceback.format_exc()));raise


if __name__=='__main__':main()
