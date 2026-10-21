"""M8 fixed ancestral-block interventions; no evolution, mating or new VM."""
import argparse,json,itertools,random,time,sqlite3,shutil,multiprocessing
from copy import deepcopy
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from .breeding_allocation import ROOT,readz,writez,writej,sha,organism,evaluate_task,controls,pushed
from .modular_genome import Genome,random_genome
from .regulatory import Gene
from . import deep_campaign as shared
from .deep_campaign_store import Journal,writer_lock,packed,unpacked,hashed
from .breeding_allocation_data import confirmation
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import record
from .deep_confirmation_analysis import capabilities
from .routing_transfer import canonical

OUT=ROOT/'results/repair_mechanism';RUN=ROOT/'runs/repair_mechanism_m8'
CONFIG=dict(phase='M8',seed=2026102119,random_seed=2026102120,workers=10,call_cap=1500000,work_cap=2*10**12,
 session_wall_seconds=900,memory_bytes=8*2**30,storage_bytes=6*2**30,disk_free_floor_bytes=16*2**30)
TARGETS=['m7/modular/0/shared/g500/b47','m7/modular/0/quota/g900/b16']

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
    # Generic local writer probes and matched parent ablations. No routing oracle.
    for k,identity in enumerate(TARGETS):
        child=sources['items'][identity];parent=sources['items'][child['parent']]
        for channel in range(8):add(f'a{k}/parent_zero/{channel}',silenced(parent['genome'],channel),'parent_writer_zero',identity)
        for role,item in [('child',child),('parent',parent)]:
            # Re-expose every existing block6 node as its writer, without pruning
            # or renumbering earlier scratch nodes. Fixed exhaustive local scan.
            g=item['genome']
            for node in range(len(g['blocks'][6])):
                x=deepcopy(g);last=x['blocks'][6][-1][1]
                x['blocks'][6][-1]=Gene(0,last,12+node,0,0,0,64).row() if node<len(g['blocks'][6])-1 else x['blocks'][6][-1]
                add(f'a{k}/{role}_readout/{node:02d}',Genome.from_dict(x).to_dict(),'existing_node_readout',identity)
        # Exactly transfer the recorded final writer (and its input port map)
        # into the parent prefix; both recorded edits append copies of old nodes.
        event=sources['last_births'][identity]['events'];assert len(event)==1 and event[0]['kind']=='duplicate_node' and event[0]['block']==6
        x=deepcopy(parent['genome']);gene=deepcopy(child['genome']['blocks'][6][-1]);gene[1]=x['blocks'][6][-1][1]
        x['blocks'][6][-1]=gene;x['ports'][6]=deepcopy(child['genome']['ports'][6])
        add(f'a{k}/parent_child_writer',Genome.from_dict(x).to_dict(),'last_writer_transfer',identity)
    # Candidate-shared0 feedback isolation: replace ONLY the final C6 writer by
    # a direct read of each of its two observed OR inputs. Raw channel references
    # go through the existing C6 port map; no new operator or solver is supplied.
    child=sources['items'][TARGETS[0]]['genome'];assert child['blocks'][6][-1][0]==10
    for channel in (3,4):
        x=deepcopy(child);dst=x['blocks'][6][-1][1];port=x['ports'][6].index(channel)
        x['blocks'][6][-1]=Gene(0,dst,port,0,0,0,64).row()
        add(f'a0/c6_only_channel{channel}',Genome.from_dict(x).to_dict(),'feedback_input_isolation',TARGETS[0])
    for identity in sources['protected']:
        add('protected/'+identity,sources['items'][identity]['genome'],'protected_reference',identity)
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
    prior=json.loads((ROOT/'results/breeding_allocation/completion.json').read_text())
    for p,h in prior['files'].items():assert sha(ROOT/p)==h,p
    return json.loads((OUT/'config.json').read_text())

def prepare():
    from tools.inspect_modular_dependencies import describe
    assert not OUT.exists();OUT.mkdir()
    old=ROOT/'results/breeding_allocation';seal=json.loads((old/'completion.json').read_text())
    for p,h in seal['files'].items():assert sha(ROOT/p)==h,p
    choices=readz(old/'choices.json.gz');anc=readz(old/'ancestry.json.gz');ids=set(TARGETS)
    for i in TARGETS:ids.update([choices['items'][i]['root'],choices['items'][i]['parent']])
    protected=sorted(i for i,roles in choices['roles'].items() if any(r[1]=='protected' for r in roles));ids.update(protected)
    sources=dict(items={i:choices['items'][i] for i in sorted(ids)},last_births={i:anc[i] for i in TARGETS},protected=protected)
    writez(OUT/'sources.json.gz',sources);writej(OUT/'config.json',CONFIG)
    static={i:dict(dependencies=describe(v['genome']),genome=v['genome']) for i,v in sources['items'].items()}
    writej(OUT/'static_analysis.json',dict(label='M7-informed static analysis; zero inference or edits',items=static))

def register():
    assert not (OUT/'registration.json').exists();r=shared.source_manifest()
    paths=[*OUT.glob('*.json'),*OUT.glob('*.json.gz'),ROOT/'docs/REPAIR_MECHANISM.md',ROOT/'tests/test_repair_mechanism.py',ROOT/'tools/inspect_modular_dependencies.py',ROOT/'tools/run_m8_workflow.py',ROOT/'results/breeding_allocation/completion.json',ROOT/'results/breeding_allocation/whole_layout_exclusions.json.gz']
    r['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths});r.update(phase='M8',scientific_calls=0,scientific_variants_generated=False)
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
    previous=set(readz(ROOT/'results/breeding_allocation/whole_layout_exclusions.json.gz')['hashes'])
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
    from .breeding_allocation_metrics import capabilities_plus,comparison,criterion,upstream_pairs
    meta=data['metadata'];queried=set(data['queries']['all'])
    caps={i:capabilities_plus(rs,meta) for i,rs in rows.items()}
    protected=[i for i,v in p['items'].items() if v['kind']=='protected_reference']
    union={k:set().union(*(caps[i][k] for i in protected)) for k in ('pairs','corridors','ordinary_bases','correct_no_path','false','success')}
    a0=caps['protected/m7/reference/anchor/0'];results={}
    om={m['base']:m for cid,m in meta.items() if cid in queried and m['family'] in ('ordinary_perfect','ordinary_random')}
    pm={(m['base'],m['pose']):m for cid,m in meta.items() if cid in queried and m['family']=='paired'}
    behavior=lambda i:hashed(packed([(r['case'],r['mask'],r['status'],r['steps']) for r in rows[i]]))
    for i,cap in caps.items():
        lineage=int(i[1]) if i.startswith(('a0/','a1/')) else None
        child=caps[f'a{lineage}/child'] if lineage is not None else None
        root=caps[f'a{lineage}/root'] if lineage is not None else None
        gate=criterion(cap,root,union,a0,meta,1) if root is not None else None
        # criterion(1) is a DIAGNOSTIC screen, never an evolved-acquisition claim.
        strata={}
        for domain in sorted({m['family']+'/'+str(m['size']) for m in om.values()}):
            for label in ('short','medium','long'):
                bs={b for b,m in om.items() if m['family']+'/'+str(m['size'])==domain and m['length_bin']==label}
                strata[domain+'/'+label]=dict(bases=len(bs),correct_both_poses=len(bs&cap['ordinary_bases']))
        results[i]=dict(kind=p['items'][i]['kind'],metrics=cap['summary'],target_pairs=len(upstream_pairs(cap,meta)),
            target_opportunities=sum(m['graph']!='fork' and m['prefix']>=2 for m in pm.values()),ordinary_length_strata=strata,
            ordinary_success_lengths=[dict(base=b,family=om[b]['family'],size=om[b]['size'],edges=len(om[b]['path'])-1) for b in sorted(cap['ordinary_bases'])],
            versus_child=comparison(cap,child,meta) if child else None,versus_root=comparison(cap,root,meta) if root else None,
            new_corridors_vs_child=len(cap['corridors']-child['corridors']) if child else None,lost_corridors_vs_child=len(child['corridors']-cap['corridors']) if child else None,
            beyond_protected={k:len(cap[k]-union[k]) for k in ('pairs','corridors','ordinary_bases','correct_no_path','success')},
            diagnostic_screen=gate,terminal_behavior_sha256=behavior(i))
    comparisons={}
    for k in (0,1):
        a=caps[f'a{k}/child'];b=caps[f'a{k}/parent'];r=caps[f'a{k}/root']
        comparisons[f'a{k}']=dict(versus_parent=comparison(a,b,meta),versus_root=comparison(a,r,meta),
            new_corridors_vs_parent=len(a['corridors']-b['corridors']),lost_corridors_vs_parent=len(b['corridors']-a['corridors']),
            parent_child_writer_matches_child=behavior(f'a{k}/parent_child_writer')==behavior(f'a{k}/child'),
            zero_writer_matches_child={str(ch):behavior(f'a{k}/zero/{ch}')==behavior(f'a{k}/child') for ch in range(8)},
            zero_writer_matches_parent={str(ch):behavior(f'a{k}/zero/{ch}')==behavior(f'a{k}/parent') for ch in range(8)})
    a=caps['a0/child'];b=caps['a0/parent']
    eligible=bool(comparisons['a0']['new_corridors_vs_parent']>0 and not a['false'] and
        all(b[k]<=a[k] for k in ('pairs','corridors','ordinary_bases','correct_no_path')) and
        comparisons['a0']['parent_child_writer_matches_child'])
    diagnostic_kinds={'ancestral_restoration','writer_zero','parent_writer_zero','existing_node_readout','last_writer_transfer','feedback_input_isolation'}
    hits=[i for i,r in results.items() if r['kind'] in diagnostic_kinds and r['diagnostic_screen'] and r['diagnostic_screen']['upstream_acquisition']]
    return canonical(dict(label='M8 fixed mechanism assay; diagnostic edits are not evolved offspring',models=results,comparisons=comparisons,
        primary_repair_replication=eligible,diagnostic_upstream_hits=hits,queries=len(queried),ordinary_bases=len(om),
        limits=['One prospectively frozen fresh panel; no adaptive selection or evolutionary reproduction.',
        'Positive diagnostic variants require separate untouched confirmation before promotion.',
        'Static recurrence plus ablations does not prove general routing or unique mechanistic explanation.',
        'Behavior equality covers saved terminal masks/status/steps, not whole trajectories or universal equivalence.']))

def analyze():
    check();assert not (OUT/'summary.json').exists();data,rows,_=load()
    writej(OUT/'summary.json',summarize(data,rows,readz(OUT/'panel.json.gz')))
    writez(OUT/'responses.json.gz',dict(rows=rows))

def audit():
    config=check();assert not (OUT/'audit.json').exists();started=time.monotonic();data,rows,models=load();p=readz(OUT/'panel.json.gz')
    assert p==make_panel(readz(OUT/'sources.json.gz'))
    assert canonical(confirmation(config['seed'],set(readz(ROOT/'results/breeding_allocation/whole_layout_exclusions.json.gz')['hashes'])))==data
    c=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True)
    assert [unpacked(r[0]) for r in c.execute('select spec from tasks order by n')]==specs(p,data['queries']['all']);c.close()
    cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in data['queries']['all']]);checker=Checker(cases);replays=grades=0
    for e,rs in models:
        reason=guard(RUN,dict(config,session_wall_seconds=1800),started);assert reason is None,reason
        org=organism(e['model'])
        for row in rs:
            checker.row(row);grades+=1
            o=cases[row['case']];m=o.maze;assert record(org.react(m.cells,m.w,m.h,m.start,m.goal),o)==row;replays+=1
    assert summarize(data,rows,p)==json.loads((OUT/'summary.json').read_text())
    from .baselines import baseline
    from .foundation_pair_confirm import normal_row
    baseline_rows={}
    for name in ('compiled_bfs','compiled_astar','wave_bit'):
        rs=[]
        for o in cases.values():
            m=o.maze;r=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));checker.row(r);assert r['optimal'] or r['no_path'];rs.append(r)
        baseline_rows[name]=rs
    assert not (OUT/'baselines.json.gz').exists();writez(OUT/'baselines.json.gz',baseline_rows)
    for i in ('control/intact_flat','control/intact_modular'):assert all(r['optimal'] or r['no_path'] for r in rows[i])
    with writer_lock(RUN):
        j=Journal(RUN);chain=j.verify_chain();assert not j.pending();assert grades==j.get('usage')['calls'];j.close()
    writej(OUT/'audit.json',dict(status='PASS',independent_grades=grades,native_replays=replays,chain=chain,wall_seconds=time.monotonic()-started,
        conventional_calls=3*len(cases),panel_corpus_summary_regenerated=True,engineering_controls_all_correct=True,limitation='All native outputs replayed; shared native VM, independent grader, not a second interpreter.'))
    print('AUDIT PASS',grades,replays,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','panel','run','analyze','audit']);a=p.parse_args();globals()[a.action]()
