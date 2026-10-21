"""M4 fixed ancestral-block interventions; no evolution, mating or new VM."""
import argparse,json,itertools,random,time,sqlite3,shutil,multiprocessing
from copy import deepcopy
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from .wave_continuation import ROOT,readz,writez,writej,sha,organism,evaluate_task,controls,pushed
from .modular_genome import Genome,random_genome
from .regulatory import Gene
from . import deep_campaign as shared
from .deep_campaign_store import Journal,writer_lock,packed,unpacked,hashed
from .wave_continuation_data import confirmation
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import record
from .deep_confirmation_analysis import capabilities
from .wave_continuation_analysis import complex_sets
from .routing_transfer import canonical

OUT=ROOT/'results/mechanism_retention';RUN=ROOT/'runs/mechanism_retention_m4'
CONFIG=dict(phase='M4',seed=2026102107,random_seed=2026102108,workers=10,call_cap=1000000,work_cap=10**12,
 session_wall_seconds=900,memory_bytes=8*2**30,storage_bytes=4*2**30,disk_free_floor_bytes=16*2**30)
TARGETS=['m3/modular/0/mixed/g669/b31','m3/modular/2/single/g800/b15']

def restored(child,root,bits):
    x=deepcopy(child)
    for k in range(8):
        if bits>>k&1:
            for f in ('blocks','ports'):x[f][k]=deepcopy(root[f][k])
    return Genome.from_dict(x).to_dict()

def silenced(value,k):
    x=deepcopy(value);dst=x['blocks'][k][-1][1];x['blocks'][k][-1]=Gene(1,dst,0,0,0,0,64).row()
    return Genome.from_dict(x).to_dict()

def make_panel(sources):
    items={};excluded=[]
    def add(label,value,kind,origin=None):items[label]=dict(genome=value,representation='modular',kind=kind,origin=origin)
    for k,i in enumerate(TARGETS):
        child=sources['items'][i];root=sources['items'][child['root']];parent=sources['items'][child['parent']]
        for role,item in [('child',child),('root',root),('parent',parent)]:add(f'a{k}/{role}',item['genome'],'unchanged',item['id'])
        for bits in range(256):
            try:g=restored(child['genome'],root['genome'],bits)
            except ValueError:excluded.append([k,bits]);continue
            add(f'a{k}/restore/{bits:03d}',g,'ancestral_restoration',i)
        for channel in range(8):add(f'a{k}/zero/{channel}',silenced(child['genome'],channel),'writer_zero',i)
    # Exact recorded intermediate plus complementary last-birth edit in mixed0.
    e=sources['last_births'][TARGETS[0]];assert [x['block'] for x in e['events']]==[4,6]
    add('a0/last_edit_first',e['intermediate'],'recorded_intermediate',TARGETS[0])
    p=deepcopy(sources['items'][sources['items'][TARGETS[0]]['parent']]['genome'])
    for f in ('blocks','ports'):p[f][6]=deepcopy(sources['items'][TARGETS[0]]['genome'][f][6])
    add('a0/last_edit_second',Genome.from_dict(p).to_dict(),'last_edit_counterfactual',TARGETS[0])
    rng=random.Random(CONFIG['random_seed'])
    for k in range(8):add(f'random/{k}',random_genome(rng).to_dict(),'random_reference')
    for c in controls():items[c['id']]=dict(genome=c['genome'],representation=c['representation'],kind='engineering_control')
    return canonical(dict(items=items,invalid_restorations=excluded,no_reproduction=True))

def specs(panel,ids):
    models={}
    for i,v in panel['items'].items():
        m={k:v[k] for k in ('representation','genome')};h=hashed(packed(m))
        models.setdefault(h,dict(model=m,queries=ids,aliases=[]))['aliases'].append(i)
    return [[models[h]] for h in sorted(models)]

def guard(directory,config,started):
    if time.monotonic()-started>=config['session_wall_seconds']:return 'wall'
    if shared.process_resources()>=config['memory_bytes']:return 'memory'
    if shutil.disk_usage(RUN).free<config['disk_free_floor_bytes']:return 'disk_free'
    if sum(p.stat().st_size for base in (RUN,OUT) for p in base.rglob('*') if p.is_file())>=config['storage_bytes']:return 'storage'

def check():
    r=json.loads((OUT/'registration.json').read_text())
    for p,h in r['files'].items():assert sha(ROOT/p)==h,p
    now=shared.source_manifest();assert all(now[k]==r[k] for k in ('python','dependencies'))
    return json.loads((OUT/'config.json').read_text())

def prepare():
    from tools.inspect_modular_dependencies import describe
    assert not OUT.exists();OUT.mkdir()
    old=ROOT/'results/wave_continuation';seal=json.loads((old/'completion.json').read_text())
    for p,h in seal['files'].items():assert sha(ROOT/p)==h,p
    choices=readz(old/'choices.json.gz');anc=readz(old/'ancestry.json.gz');ids=set(TARGETS)
    for i in TARGETS:ids.update([choices['items'][i]['root'],choices['items'][i]['parent']])
    sources=dict(items={i:choices['items'][i] for i in sorted(ids)},last_births={i:anc[i] for i in TARGETS})
    writez(OUT/'sources.json.gz',sources);writej(OUT/'config.json',CONFIG)
    static={i:dict(dependencies=describe(v['genome']),genome=v['genome']) for i,v in sources['items'].items()}
    writej(OUT/'static_analysis.json',dict(label='M3-informed static analysis; zero inference or edits',items=static))

def register():
    assert not (OUT/'registration.json').exists();r=shared.source_manifest()
    paths=[*OUT.glob('*.json'),*OUT.glob('*.json.gz'),ROOT/'docs/MECHANISM_RETENTION.md',ROOT/'tests/test_mechanism_retention.py',ROOT/'tools/inspect_modular_dependencies.py',ROOT/'results/wave_continuation/completion.json',ROOT/'results/wave_continuation/whole_layout_exclusions.json.gz']
    r['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths});r.update(phase='M4',scientific_calls=0,scientific_variants_generated=False)
    writej(OUT/'registration.json',r)

def panel():
    check();pushed(OUT/'registration.json');assert not (OUT/'panel.json.gz').exists()
    p=make_panel(readz(OUT/'sources.json.gz'));writez(OUT/'panel.json.gz',p)
    count=len(specs(p,[]));assert count*1680<=CONFIG['call_cap']
    writej(OUT/'panel_counts.json',dict(aliases=len(p['items']),physical_models=count,max_calls=count*1680,excluded=len(p['invalid_restorations']),fresh_cases_generated=False));print(count,'models',flush=True)

def run():
    config=check();pushed(OUT/'panel.json.gz');p=readz(OUT/'panel.json.gz');assert p==make_panel(readz(OUT/'sources.json.gz'))
    assert not (RUN/'campaign.sqlite').exists(),'No silent rerun/resume; inspect any existing records.'
    RUN.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    shared.evaluate_task=evaluate_task;shared.resource_reason=guard
    previous=set(readz(ROOT/'results/wave_continuation/whole_layout_exclusions.json.gz')['hashes'])
    with writer_lock(RUN):
        j=Journal(RUN);j.initialize(config,dict(panel_sha256=sha(OUT/'panel.json.gz')),previous)
        data=confirmation(config['seed'],previous);writez(OUT/'cases.json.gz',data);tasks=specs(p,data['queries']['all']);n=j.prepare(data,tasks)
        with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as pool:
            reason=shared.run_stage(j,n,data,pool,config,started,[False])
        if not reason:j.commit(n,j.state(),dict(no_selection=True,no_evolution=True))
        writej(OUT/'session.json',dict(status='checkpoint' if reason else 'complete',reason=reason,usage=j.get('usage'),wall_seconds=time.monotonic()-started,rss_peak_bytes=shared._peak_rss));j.close()
        assert reason is None,reason

def load():
    c=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True);rows={};models=[]
    assert c.execute('select count(*) from stages where complete=1').fetchone()[0]==1
    for spec,result,h in c.execute('select spec,result,result_hash from tasks order by n'):
        assert hashed(result)==h;entries=unpacked(result)['entries'];assert len(entries)==1
        e=unpacked(spec)[0];r=entries[0];assert e['aliases']==r['aliases']
        assert [row['case'] for row in r['rows']]==e['queries']
        for i in e['aliases']:rows[i]=r['rows']
        models.append((e,r['rows']))
    c.close();return readz(OUT/'cases.json.gz'),rows,models

def summarize(data,rows,p):
    meta=data['metadata'];caps={i:capabilities(rs,meta) for i,rs in rows.items()};targets=[caps[f'a{k}/child'] for k in (0,1)]
    results={}
    for i,cap in caps.items():
        sets=complex_sets(cap,meta);retention=[]
        for ref in targets:
            retention.append({k:len(cap[k]&ref[k])/len(ref[k]) if ref[k] else None for k in ('pairs','corridors','ordinary_bases')})
        joint=all(x is None or x>=.9 for d in retention for x in d.values()) and not cap['false']
        results[i]=dict(kind=p['items'][i]['kind'],metrics=cap['summary'],hard_pairs=len(sets['hard_pairs']),long_bases=len(sets['long_bases']),
            retained_against_children=retention,joint_retention_screen=joint,
            child_differences={f'a{k}':dict(new_pairs=len(cap['pairs']-ref['pairs']),lost_pairs=len(ref['pairs']-cap['pairs']),new_ordinary=len(cap['ordinary_bases']-ref['ordinary_bases']),lost_ordinary=len(ref['ordinary_bases']-cap['ordinary_bases'])) for k,ref in enumerate(targets)})
    behavior=lambda i:hashed(packed([(r['case'],r['mask'],r['status'],r['steps']) for r in rows[i]]))
    mixed_new=complex_sets(caps['a0/child'],meta)['long_bases']-complex_sets(caps['a0/root'],meta)['long_bases']
    junction_new=complex_sets(caps['a1/child'],meta)['hard_pairs']-complex_sets(caps['a1/root'],meta)['hard_pairs']
    eligible=len(mixed_new)>=1 and len(junction_new)>=8
    return canonical(dict(label='M4 fixed-panel mechanism experiment; diagnostic edits are not evolved offspring',models=results,
        reference_eligibility=dict(mixed_new_long_bases=len(mixed_new),junction_new_hard_pairs=len(junction_new),eligible=eligible),
        qualified_diagnostic_hits=[i for i,r in results.items() if eligible and r['joint_retention_screen'] and r['kind'] in ('ancestral_restoration','writer_zero','last_edit_counterfactual')],
        last_birth_checks=dict(first_equals_parent=behavior('a0/last_edit_first')==behavior('a0/parent'),second_equals_child=behavior('a0/last_edit_second')==behavior('a0/child'),child_zero6_equals_child=behavior('a0/zero/6')==behavior('a0/child')),
        limitations=['All variants fixed before fresh cases; no adaptive selection or new evolutionary lineage.', 'Edited-variant positive screens are exploratory multiple comparisons and require separate untouched confirmation before promotion.', 'Root block/port restoration changes several loci together; whole-block necessity is conditional on this background.', 'Writer-zero preserves instruction count but may alter read cost and stopping; status and resource failures remain outcomes.']))

def analyze():
    check();assert not (OUT/'summary.json').exists();data,rows,_=load()
    writej(OUT/'summary.json',summarize(data,rows,readz(OUT/'panel.json.gz')))

def audit():
    config=check();assert not (OUT/'audit.json').exists();started=time.monotonic();data,rows,models=load();p=readz(OUT/'panel.json.gz')
    assert p==make_panel(readz(OUT/'sources.json.gz'))
    assert canonical(confirmation(config['seed'],set(readz(ROOT/'results/wave_continuation/whole_layout_exclusions.json.gz')['hashes'])))==data
    c=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True)
    assert [unpacked(r[0]) for r in c.execute('select spec from tasks order by n')]==specs(p,data['queries']['all']);c.close()
    cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in data['queries']['all']]);checker=Checker(cases);replays=grades=0
    for e,rs in models:
        reason=guard(RUN,dict(config,session_wall_seconds=1800),started);assert reason is None,reason
        original=any(p['items'][i]['kind']!='ancestral_restoration' for i in e['aliases']);org=organism(e['model']);key=hashed(packed(e['model']))
        for row in rs:
            checker.row(row);grades+=1
            if original or int(hashed(packed([key,row['case']])),16)%16==0:
                o=cases[row['case']];m=o.maze;assert record(org.react(m.cells,m.w,m.h,m.start,m.goal),o)==row;replays+=1
    assert summarize(data,rows,p)==json.loads((OUT/'summary.json').read_text())
    for i in ('control/intact_flat','control/intact_modular'):assert all(r['optimal'] or r['no_path'] for r in rows[i])
    with writer_lock(RUN):
        j=Journal(RUN);chain=j.verify_chain();assert not j.pending();assert grades==j.get('usage')['calls'];j.close()
    writej(OUT/'audit.json',dict(status='PASS',independent_grades=grades,native_replays=replays,chain=chain,wall_seconds=time.monotonic()-started,
        panel_corpus_summary_regenerated=True,engineering_controls_all_correct=True,limitation='Shared native VM; independent grader; all non-factorial models replayed fully, factorial-only models at fixed1/16.'))
    print('AUDIT PASS',grades,replays,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','panel','run','analyze','audit']);a=p.parse_args();globals()[a.action]()
