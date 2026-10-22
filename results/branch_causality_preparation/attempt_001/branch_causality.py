"""M24 fixed dormant-branch and readout causality. Reused data, no evolution."""
import argparse
import base64
import hashlib
import json
import multiprocessing
import shutil
import sqlite3
import time
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz, compressed_json as writez
from .deep_confirmation import writej
from .routing_transfer import canonical, sha
from .deep_campaign_store import writer_lock, packed, unpacked, hashed
from .referenced_campaign_store import Journal, load_layouts, write_reference
from . import deep_campaign as shared
from .connected_genome import Genome
from .spare_genome import Genome as Body
from .regulatory import Gene
from .connected_evaluation import organism, evaluate_task
from .copy_specialization import tasks
from .connected_evolution import pushed
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import record
from .breeding_allocation_metrics import capabilities_plus

OUT = ROOT/'results/branch_causality'
RUN = ROOT/'runs/branch_causality_m24'
PRIOR = ROOT/'results/dormant_evolution'
FOCAL='m23/connected/0/enabled/g190/b50'
ROOT_ID='m14/reference/gated_partial'
BRANCHES=((0,10),(7,13))
GAIN='confirmation/ordinary/perfect/15/112000/perfect/15x15/d4-4'
COUNTERPOSE=GAIN[:-1]+'0'
ACTION_EPOCH=time.time()
CONFIG=dict(phase='M24',workers=10,call_cap=150000,work_cap=10**14,
    session_wall_seconds=900,audit_wall_seconds=900,trace_wall_seconds=900,
    trace_call_cap=600,trace_work_cap=10**13,memory_bytes=8*2**30,
    storage_bytes=3*2**30,disk_free_floor_bytes=16*2**30,
    layout_base_manifest='results/branch_causality/exclusions.json')


def replace_parts(g, blocks=None, ports=None, tags=None):
    return Genome(Body(tuple(tuple(b) for b in (blocks if blocks is not None else g.body.blocks)),
                       tuple(tuple(p) for p in (ports if ports is not None else g.body.ports))),
                  tuple(tags if tags is not None else g.initialization))


def lineage(ancestry):
    chain=[];identity=FOCAL
    while True:
        entry=ancestry[identity];chain.append(entry)
        if entry.get('phase')!='M23':break
        identity=entry['item']['parent']
    chain.reverse();assert len(chain)==17 and chain[0]['item']['id']==ROOT_ID
    return chain


def factorial(g, parent, bypass0, bypass7, saved_ports):
    """Retain every instruction/seed; replace SELECT branches with old/old."""
    blocks=[list(b) for b in g.body.blocks];ports=list(g.body.ports)
    for bypass,(m,i) in zip((bypass0,bypass7),BRANCHES):
        if bypass:
            v=blocks[m][i+2];assert v.op==12 and (v.a,v.b,v.c,v.gate)==(12+i,13+i,11+i,64)
            blocks[m][i+2]=Gene(v.op,v.dst,v.a,v.c,v.c,v.radius,v.gate)
    if not saved_ports:ports[2]=parent.body.ports[2]
    return replace_parts(g,blocks,ports)


def make_variants(ancestry, sources):
    chain=lineage(ancestry);g=Genome.from_dict(chain[-1]['item']['genome']);p=Genome.from_dict(chain[-2]['item']['genome'])
    assert g.body.blocks==p.body.blocks and g.initialization==p.initialization
    assert all(g.body.ports[k]==p.body.ports[k] for k in range(10) if k!=2)
    assert chain[-1]['events'][0]['kind']=='ports' and chain[-1]['events'][0]['a']==8 and chain[-1]['events'][0]['b']==3
    ports=list(p.body.ports[2]);ports[8],ports[3]=ports[3],ports[8];assert tuple(ports)==g.body.ports[2]
    items=[]
    for n,entry in enumerate(chain):
        item=entry['item'];items.append(dict(id=item['id'],kind='ancestor',position=n,
            parent=item.get('parent'),events=entry.get('events',[]),model=dict(representation='connected',genome=item['genome'])))
    for a in (False,True):
        for b in (False,True):
            for saved in (False,True):
                v=factorial(g,p,a,b,saved)
                items.append(dict(id=f'factorial/bypass0={int(a)}/bypass7={int(b)}/ports={int(saved)}',kind='factorial',
                    bypass0=a,bypass7=b,saved_ports=saved,model=dict(representation='connected',genome=v.to_dict())))
    root=Genome.from_dict(chain[0]['item']['genome']);ports=list(root.body.ports);port=list(ports[2]);port[8],port[3]=port[3],port[8];ports[2]=tuple(port)
    items.append(dict(id='sufficiency/root_plus_final_port_swap',kind='sufficiency',model=dict(representation='connected',genome=replace_parts(root,ports=ports).to_dict())))
    items += [dict(id=i,kind='protected',model=dict(representation='connected',genome=v['genome'])) for i,v in sources['protected'].items() if i in ancestry and ancestry[i].get('phase')!='M23' and i!=ROOT_ID]
    from .connected_evolution import controls
    items += [dict(id=c['id'],kind='control',model={k:c[k] for k in ('representation','genome')}) for c in controls()]
    assert len({i['id'] for i in items})==len(items)
    return canonical(dict(items=sorted(items,key=lambda i:i['id']),chain=[e['item']['id'] for e in chain],
        inference_used=False,selection=False,transformations='Eight fixed branch-bypass x final-port states plus exact ancestry and root swap sufficiency'))


def prior_check():
    seal=json.loads((PRIOR/'completion.json').read_text())
    for p,h in seal['files'].items(): assert sha(ROOT/p)==h,p
    for p,r in seal['local_records'].items(): assert sha(ROOT/p)==r['sha256'],p
    return dict(completion_sha256=sha(PRIOR/'completion.json'),files=len(seal['files']),local_records=len(seal['local_records']))


def check():
    reg=json.loads((OUT/'registration.json').read_text())
    for p,h in reg['files'].items(): assert sha(ROOT/p)==h,p
    now=shared.source_manifest()
    for k in ('python','dependencies'): assert reg[k]==now[k]
    prior_check(); return json.loads((OUT/'config.json').read_text())


def panel_and_traces():
    old=readz(PRIOR/'confirmation.json.gz');data=deepcopy(old);assert len(data['queries']['all'])==1680
    data.update(kind='mechanism',generation=0,new_layouts=[],reused_from='results/dormant_evolution/confirmation.json.gz',independent_confirmation=False)
    saved=readz(PRIOR/'final_responses.json.gz')['rows'];caps={i:capabilities_plus(saved[i],old['metadata']) for i in (FOCAL,ROOT_ID)}
    gains=caps[FOCAL]['success']-caps[ROOT_ID]['success'];losses=caps[ROOT_ID]['success']-caps[FOCAL]['success']
    selected={GAIN:['known_single_pose_gain'],COUNTERPOSE:['known_counterpose_failure']}
    for label,ids in [('gain',gains),('loss',losses)]:
        groups={}
        for cid in ids:
            row=next(r for r in saved[ROOT_ID] if r['case']==cid)
            family=old['metadata'][cid]['family'] if row['reachable'] else 'disconnected'
            groups.setdefault(family,[]).append(cid)
        for family,cs in groups.items():
            cid=min(cs,key=lambda c:hashlib.sha256(c.encode()).hexdigest());selected.setdefault(cid,[]).append(label+'/'+family)
    # One old no-path input and one long input per ordinary family, metadata-only.
    for label,cs in [('correct_no_path',list(caps[ROOT_ID]['correct_no_path']))]+[(f+'/16plus',[c for c in data['queries']['all'] if old['metadata'][c]['family']==f and len(old['metadata'][c]['path'])-1>=16]) for f in ('ordinary_perfect','ordinary_random')]:
        if cs:
            cid=min(cs,key=lambda c:hashlib.sha256(c.encode()).hexdigest());selected.setdefault(cid,[]).append(label)
    assert len(selected)<=16
    return canonical(data),canonical(dict(gained_inputs=[GAIN],counterpose=COUNTERPOSE,selected_cases=sorted(selected),reasons=selected,
        rule='Known gain/counterpose; lowest SHA256 case per old root gain/loss family; one root no-path and one 16+ case per ordinary family',
        scope='Reused M23 mechanism/development data, no independent confirmation'))


def prepare():
    assert not OUT.exists();prior=prior_check();OUT.mkdir();RUN.mkdir(parents=True,exist_ok=True)
    assert shutil.disk_usage(RUN).free>=CONFIG['disk_free_floor_bytes']+CONFIG['storage_bytes']
    a=readz(PRIOR/'ancestry.json.gz');s=readz(PRIOR/'sources.json.gz')
    writej(OUT/'config.json',CONFIG);writez(OUT/'variants.json.gz',make_variants(a,s))
    writez(OUT/'ancestry_source.json.gz',{e['item']['id']:e for e in lineage(a)})
    data,traces=panel_and_traces();writez(OUT/'panel.json.gz',data);writej(OUT/'trace_panel.json',traces)
    write_reference(OUT/'exclusions.json',PRIOR/'whole_layout_exclusions.json',load_layouts(PRIOR/'whole_layout_exclusions.json'))
    items=readz(OUT/'variants.json.gz')['items'];count=sum(map(len,tasks(items,[])))
    traced=sum(len(t) for t in tasks([i for i in items if i['kind'] in ('factorial','ancestor','sufficiency')],[]))
    assert count*1680<CONFIG['call_cap'] and traced*len(traces['selected_cases'])<=CONFIG['trace_call_cap']
    writej(OUT/'preparation.json',dict(prior=prior,aliases=len(items),physical_models=count,planned_calls=count*1680,
        planned_trace_calls=traced*len(traces['selected_cases']),new_cases=0,evolution=False,independent_confirmation=False))


def preflight():
    assert not (OUT/'preflight.json').exists() and not (OUT/'registration.json').exists()
    from .copy_specialization import fixture_sources
    from .connected_trace import respond
    from .connected_evolution import controls
    source=Genome.from_dict(fixture_sources()['anchors']['parent']['genome']);blocks=[list(b) for b in source.body.blocks]
    for m in (0,7):
        n=len(blocks[m]);blocks[m] += [Gene(1,12+n,1,0,0,0,64),Gene(0,13+n,12,0,0,0,12+n),Gene(12,14+n,12+n,13+n,11+n,0,64)]
    g=replace_parts(source,blocks);p=g;items=[]
    for a in (False,True):
        for b in (False,True):
            bs=[list(v) for v in g.body.blocks]
            for m,flag in ((0,a),(7,b)):
                if flag:
                    v=bs[m][-1];bs[m][-1]=Gene(v.op,v.dst,v.a,v.c,v.c,0,v.gate)
            items.append(dict(id=f'fixture/{a}/{b}',model=dict(representation='connected',genome=replace_parts(g,bs).to_dict())))
    items += [dict(id=c['id'],model={k:c[k] for k in ('representation','genome')}) for c in controls()]
    fixture=readz(ROOT/'results/restoration_assay/discarded_corpus_fixture.json.gz');ids=fixture['queries']['all'][:3]
    mazes=[m for m in fixture['mazes'] if m['case_id'] in ids];cases=cases_from_manifest(mazes);checker=Checker(cases)
    started=time.monotonic();receipts=[];native=trace=0
    for task in tasks(items,ids):
        receipt=evaluate_task(task,mazes,'m24fixture');receipts.append(receipt)
        for e,result in zip(task,receipt['entries']):
            org=organism(e['model'])
            for row in result['rows']:
                checker.row(row);o=cases[row['case']];m=o.maze
                assert record(org.react(m.cells,m.w,m.h,m.start,m.goal),o)==row;native+=1
                if e['model']['representation']=='connected':
                    reaction,history,_=respond(e['model'],m);assert record(reaction,o)==row
                    assert len(history)==reaction.steps+1;trace+=1
    writez(OUT/'preflight_receipts.json.gz',receipts)
    writej(OUT/'preflight.json',dict(status='PASS',fixture_calls=sum(r['calls'] for r in receipts),candidate_seconds=sum(r['candidate_seconds'] for r in receipts),
        extra_native_checks=native,trace_checks=trace,wall_seconds=elapsed(started),new_cases=0,scientific_variant_calls=0))


def register():
    assert not (OUT/'registration.json').exists() and (OUT/'preflight.json').exists()
    reg=shared.source_manifest();paths=[p for p in OUT.rglob('*') if p.is_file()]
    paths += [ROOT/'docs/BRANCH_CAUSALITY.md',ROOT/'tests/test_branch_causality.py',ROOT/'tools/run_m24_workflow.py',PRIOR/'completion.json']
    reg['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    reg.update(phase='M24',scientific_variant_calls=0,new_case_generation=False,selection=False)
    writej(OUT/'registration.json',reg)


def elapsed(started):
    return max(time.monotonic()-started,time.time()-ACTION_EPOCH)


def guard(directory,config,started):
    if elapsed(started)>=config['session_wall_seconds']:return 'wall'
    if shared.process_resources()>=config['memory_bytes']:return 'memory'
    if shutil.disk_usage(RUN).free<config['disk_free_floor_bytes']:return 'disk_free'
    if sum(p.stat().st_size for b in (RUN,OUT) for p in b.rglob('*') if p.is_file())>=config['storage_bytes']:return 'storage'


def run():
    config=check();pushed(OUT/'registration.json');assert not (RUN/'evaluation/campaign.sqlite').exists()
    data=readz(OUT/'panel.json.gz');items=readz(OUT/'variants.json.gz')['items'];started=time.monotonic()
    shared.evaluate_task=evaluate_task;shared.resource_reason=guard
    with writer_lock(RUN/'evaluation'):
        j=Journal(RUN/'evaluation');j.initialize(config,dict(variants_sha256=sha(OUT/'variants.json.gz')),load_layouts(OUT/'exclusions.json'))
        n=j.prepare(data,tasks(items,data['queries']['all']))
        with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as executor:
            reason=shared.run_stage(j,n,data,executor,config,started,[False])
        if not reason:j.commit(n,j.state(),dict(no_selection=True,reused_mechanism_panel=True))
        writej(OUT/'session.json',dict(status='complete' if not reason else 'stopped',reason=reason,usage=j.get('usage'),
            wall_seconds=elapsed(started),rss_peak_bytes=shared._peak_rss));j.close();assert not reason,reason


def load():
    rows={};models=[];con=sqlite3.connect(f'file:{RUN}/evaluation/campaign.sqlite?mode=ro',uri=True)
    assert con.execute('select count(*) from stages where complete=1').fetchone()[0]==1
    for spec,result,h in con.execute('select spec,result,result_hash from tasks order by n'):
        assert hashed(result)==h;ss=unpacked(spec);rr=unpacked(result)['entries'];assert len(ss)==len(rr)
        for e,r in zip(ss,rr):
            assert e['aliases']==r['aliases'] and e['queries']==[v['case'] for v in r['rows']]
            for i in e['aliases']:assert i not in rows;rows[i]=r['rows']
            models.append((e,r['rows']))
    con.close();return readz(OUT/'panel.json.gz'),rows,models


def summary(data,rows):
    variants=readz(OUT/'variants.json.gz');items=variants['items'];meta=data['metadata']
    caps={i:capabilities_plus(rs,meta) for i,rs in rows.items()};source=caps[ROOT_ID];focal=caps[FOCAL]
    old=readz(PRIOR/'final_responses.json.gz')['rows'];archive=[i for i in old if i.startswith('archive/')];assert len(archive)==103
    union=set().union(*(capabilities_plus(old[i],meta)['success'] for i in archive))
    ordinary={m['base']:m for c,m in meta.items() if c in data['queries']['all'] and m['family'].startswith('ordinary_')}
    metrics={}
    for item in items:
        i=item['id'];c=caps[i];strata={};lookup={r['case']:r for r in rows[i]}
        for base,m in ordinary.items():
            length=len(m['path'])-1;label=m['family']+'/'+('16plus' if length>=16 else '8to15' if length>=8 else '0to7')
            cell=strata.setdefault(label,dict(bases=0,correct_both_poses=0));cell['bases']+=1;cell['correct_both_poses']+=base in c['ordinary_bases']
        metrics[i]=dict(kind=item['kind'],metrics=c['summary'],correct_inputs=len(c['success']),correct_no_path=len(c['correct_no_path']),
            versus_root={k:dict(gained=len(c[k]-source[k]),lost=len(source[k]-c[k]),retained=len(c[k]&source[k])) for k in ('pairs','corridors','ordinary_bases','correct_no_path','success')},
            versus_focal={k:dict(gained=len(c[k]-focal[k]),lost=len(focal[k]-c[k])) for k in ('pairs','corridors','ordinary_bases','correct_no_path','success')},
            same_focal_terminal=sum(all(a[k]==b[k] for k in ('mask','status','steps')) for a,b in zip(rows[i],rows[FOCAL])),
            lost_root_inputs=sorted(source['success']-c['success']),new_inputs_beyond_declared_archive=sorted(c['success']-union),
            ordinary_length_strata=strata,gain=lookup[GAIN],counterpose=lookup[COUNTERPOSE],
            counted_work=sum(r['reads']+r['dispatches']+r['exposure_checks'] for r in rows[i]),
            status_counts={s:sum(r['status']==s for r in rows[i]) for s in sorted({r['status'] for r in rows[i]})})
    truth=[dict(identity=i['id'],bypass0=i['bypass0'],bypass7=i['bypass7'],saved_ports=i['saved_ports'],
        gain=metrics[i['id']]['gain']['optimal'],counterpose=metrics[i['id']]['counterpose']['optimal'],
        **{k:metrics[i['id']][k] for k in ('correct_inputs','correct_no_path','same_focal_terminal')}) for i in items if i['kind']=='factorial']
    chain=[dict(identity=i,position=n,events=next(x['events'] for x in items if x['id']==i),gain=metrics[i]['gain']['optimal'],
                pairs=metrics[i]['metrics']['paired'],ordinary=metrics[i]['metrics']['ordinary_bases_both_poses'],correct_no_path=metrics[i]['correct_no_path']) for n,i in enumerate(variants['chain'])]
    return canonical(dict(status='mechanism_evaluated',independent_confirmation=False,new_cases=0,evolution=False,selection=False,
        inputs=len(data['queries']['all']),aliases=len(items),models=metrics,factorial=truth,lineage=chain,
        first_successful_ancestor=next((c['identity'] for c in chain if c['gain']),None),archive_aliases=len(archive),
        limits='Conditional fixed interventions on one selected related lineage and reused M23 data; no new confirmation, isolated policy claim, generalization or speed claim.'))


def analyze():
    check();assert not (OUT/'summary.json').exists();data,rows,models=load()
    writej(OUT/'summary.json',summary(data,rows));writez(OUT/'responses.json.gz',dict(models=[dict(aliases=e['aliases'],rows=rs) for e,rs in models]))


def audit():
    config=check();assert not (OUT/'audit.json').exists();started=time.monotonic();data,rows,models=load()
    assert make_variants(readz(PRIOR/'ancestry.json.gz'),readz(PRIOR/'sources.json.gz'))==readz(OUT/'variants.json.gz')
    expected,tp=panel_and_traces();assert expected==data and tp==json.loads((OUT/'trace_panel.json').read_text())
    items=readz(OUT/'variants.json.gz')['items'];con=sqlite3.connect(f'file:{RUN}/evaluation/campaign.sqlite?mode=ro',uri=True)
    assert [unpacked(r[0]) for r in con.execute('select spec from tasks order by n')]==tasks(items,data['queries']['all']);con.close()
    cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in data['queries']['all']]);checker=Checker(cases);calls=work=0
    for e,rs in models:
        assert not guard(RUN,dict(config,session_wall_seconds=config['audit_wall_seconds']),started)
        org=organism(e['model'])
        for r in rs:
            checker.row(r);o=cases[r['case']];m=o.maze
            assert record(org.react(m.cells,m.w,m.h,m.start,m.goal),o)==r
            calls+=1;work+=r['reads']+r['dispatches']+r['exposure_checks']
    old=readz(PRIOR/'final_responses.json.gz');prior_models={hashed(packed(e['model'])):rs for e,rs in old['models']};comparisons=0
    for e,rs in models:
        key=hashed(packed(e['model']))
        if key in prior_models:assert rs==prior_models[key];comparisons+=len(rs)
    for item in items:
        if item['kind']=='control':assert all(r['optimal'] or r['no_path'] for r in rows[item['id']])
    assert summary(data,rows)==json.loads((OUT/'summary.json').read_text())
    with writer_lock(RUN/'evaluation'):
        j=Journal(RUN/'evaluation');chain=j.verify_chain();assert not j.pending() and calls==j.get('usage')['calls'];j.close()
    writej(OUT/'audit.json',dict(status='PASS',native_replays=calls,independent_grades=calls,native_counted_work=work,
        chain=chain,all_transformations_panel_tasks_summary_replayed=True,m23_exact_response_comparisons=comparisons,
        wall_seconds=elapsed(started),limitation='Shared frozen production VM; independent raster grader, ALL-native replay.'))


def traces(audit_mode=False):
    from .connected_trace import respond
    import numpy as np
    config=check();name='trace_audit.json' if audit_mode else 'trace_session.json'
    assert not (OUT/name).exists();started=time.monotonic();data,rows,models=load()
    ids=json.loads((OUT/'trace_panel.json').read_text())['selected_cases']
    cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in ids]);records=[];calls=work=0
    saved=readz(OUT/'traces.json.gz') if audit_mode else None;position=0
    trace_aliases={i['id'] for i in readz(OUT/'variants.json.gz')['items'] if i['kind'] in ('ancestor','factorial','sufficiency')}
    for e,rs in models:
        if e['model']['representation']!='connected' or not set(e['aliases'])&trace_aliases:continue
        lookup={r['case']:r for r in rs}
        for cid in ids:
            assert not guard(RUN,dict(config,session_wall_seconds=config['trace_wall_seconds']),started)
            assert calls+1<=config['trace_call_cap']
            o=cases[cid];reaction,history,allocated=respond(e['model'],o.maze);row=record(reaction,o)
            assert row==lookup[cid]
            calls+=1;work+=row['reads']+row['dispatches']+row['exposure_checks'];assert work<=config['trace_work_cap']
            result=dict(model_sha256=hashed(packed(e['model'])),aliases=e['aliases'],case=cid,row=row,
                shape=list(history.shape),dtype='uint16',history_base64=base64.b64encode(history.tobytes()).decode(),
                allocated_history_bytes=allocated)
            if audit_mode:assert result==saved['records'][position];position+=1
            else:records.append(result)
    if audit_mode:assert position==len(saved['records'])
    else:writez(OUT/'traces.json.gz',dict(records=records,scope='Passive completed-tick states only, unchanged normal halt/work limits'))
    writej(OUT/name,dict(status='PASS',calls=calls,counted_work=work,wall_seconds=elapsed(started),
                        complete_history_replay=audit_mode,all_production_rows_equal=True,rss_peak_bytes=shared._peak_rss))


if __name__=='__main__':
    actions=dict(prepare=prepare,preflight=preflight,register=register,run=run,analyze=analyze,audit=audit,
                 traces=traces,trace_audit=lambda:traces(True))
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=actions)
    actions[parser.parse_args().action]()
