"""M21 fixed copy/readout interventions. Reused mechanism data; no evolution."""
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
from .copy_specialization import tasks, references
from .connected_evolution import pushed
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import record
from .breeding_allocation_metrics import capabilities_plus

OUT = ROOT/'results/readout_causality'
RUN = ROOT/'runs/readout_causality_m21'
PRIOR = ROOT/'results/copy_specialization'
SPECIALISTS = ('generic/parent/d3/0246', 'generic/parent/d5/0259',
               'local/parent/d3/0108', 'local/parent/d5/0059')
COPY_MODES = ('intact', 'bypass_keep', 'remove_only', 'bypass_remove')
TERMINALS = ('saved', 'restore_old')
CONFIG = dict(phase='M21', workers=10, call_cap=250000, work_cap=10**14,
              session_wall_seconds=900, audit_wall_seconds=900, trace_wall_seconds=900,
              trace_call_cap=2500, trace_work_cap=10**13, memory_bytes=8*2**30,
              storage_bytes=2*2**30, disk_free_floor_bytes=16*2**30,
              layout_base_manifest='results/readout_causality/exclusions.json')


def replace_parts(g, blocks=None, ports=None, tags=None):
    return Genome(Body(tuple(tuple(b) for b in (blocks if blocks is not None else g.body.blocks)),
                       tuple(tuple(p) for p in (ports if ports is not None else g.body.ports))),
                  tuple(tags if tags is not None else g.initialization))


def terminal(g, reader, gene, append=False):
    blocks=[list(b) for b in g.body.blocks]
    row=gene.row(); row[1]=12+len(blocks[reader])-(not append)
    if append: blocks[reader].append(Gene(*row))
    else: blocks[reader][-1]=Gene(*row)
    return replace_parts(g, blocks=blocks)


def intervene(g, reader, donor, target, copy_mode, old_terminal=None):
    """No maze/oracle access. Removal zeroes only target's seed/writer.

    Bypass exchanges dormant donor and active target positions in this reader;
    asserts prevent silently redirecting another live input slot.
    """
    assert copy_mode in COPY_MODES and target>=8
    ports=[list(p) for p in g.body.ports]; blocks=[list(b) for b in g.body.blocks]
    tags=list(g.initialization)
    if copy_mode.startswith('bypass'):
        a=ports[reader].index(target); b=ports[reader].index(donor)
        assert a<8<=b, (reader, donor, target, a, b)
        ports[reader][a], ports[reader][b]=ports[reader][b], ports[reader][a]
    if copy_mode in ('remove_only','bypass_remove'):
        blocks[target]=[]; tags[target]=0
    result=replace_parts(g, blocks, ports, tags)
    if old_terminal is not None: result=terminal(result, reader, old_terminal)
    return result


def make_variants(sources, pool):
    lookup={x['id']:x for x in pool['items']}; items=[]
    parent=Genome.from_dict(sources['anchors']['parent']['genome'])
    for identity in SPECIALISTS:
        source=lookup[identity]; g=Genome.from_dict(source['model']['genome'])
        reader, donor, target=(source[k] for k in ('reader','donor','target'))
        assert reader==6 and source['anchor']=='parent'
        old=parent.body.blocks[reader][-1]; observed=g.body.blocks[reader][-1]
        assert observed.op==3 and (observed.a,observed.b,observed.gate)==(15,13,64)
        for mode in COPY_MODES:
            for expression in TERMINALS:
                v=intervene(g,reader,donor,target,mode,old if expression=='restore_old' else None)
                items.append(dict(id=identity+'/'+mode+'/'+expression, kind='factorial', specialist=identity,
                    copy_mode=mode, terminal=expression, reader=reader, donor=donor, target=target,
                    model=dict(representation='connected',genome=v.to_dict())))
        # Broader restoration control: full original reader body AND ports.
        for remove in (False,True):
            blocks=list(g.body.blocks); ports=list(g.body.ports); tags=list(g.initialization)
            blocks[reader]=parent.body.blocks[reader]; ports[reader]=parent.body.ports[reader]
            if remove: blocks[target]=(); tags[target]=0
            v=replace_parts(g,blocks,ports,tags)
            items.append(dict(id=identity+'/full_reader_restore/'+str(remove), kind='whole_reader',
                specialist=identity, copy_removed=remove, model=dict(representation='connected',genome=v.to_dict())))
        # Fixed sufficiency tests on original source and exact initialized copy.
        base=lookup[source['copy_base']]
        for background,back in [('source',parent),('copy',Genome.from_dict(base['model']['genome']))]:
            for append in (True,False):
                v=terminal(back,reader,observed,append)
                items.append(dict(id=identity+'/terminal_only/'+background+'/'+('append' if append else 'replace'),
                    kind='sufficiency',specialist=identity,background=background,append=append,
                    model=dict(representation='connected',genome=v.to_dict())))
        items.append(deepcopy(base))
    items+=references(sources)
    unique={}
    for item in items:
        if item['id'] in unique: assert unique[item['id']]==item
        unique[item['id']]=item
    return canonical(dict(items=[unique[i] for i in sorted(unique)], specialists=list(SPECIALISTS),
                          inference_used=False, selection=False, transformations='Fixed factorial plus sufficiency and full-reader controls'))


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
    old=readz(PRIOR/'final_cases.json.gz'); data=deepcopy(old)
    ids=data['queries']['all']; assert len(ids)==1680
    data.update(kind='mechanism',generation=0,new_layouts=[],
        reused_from='results/copy_specialization/final_cases.json.gz',independent_confirmation=False)
    saved=readz(PRIOR/'final_responses.json.gz')
    rows={i:rs['rows'] for rs in saved['models'] for i in rs['aliases']}
    caps={i:capabilities_plus(rs,old['metadata']) for i,rs in rows.items()}
    details=json.loads((PRIOR/'specialist_details.json').read_text())['nominees']
    gained=sorted({r['case'] for i in SPECIALISTS for r in details[i]['new_ordinary_case_responses']})
    assert len(gained)==2
    selected={c:['shared_gain'] for c in gained}; losses={}
    for identity in SPECIALISTS:
        lost=caps['anchor/parent']['success']-caps[identity]['success']; groups={}
        for cid in lost:
            m=old['metadata'][cid]; family=m['family']
            label='disconnected' if not next(r for r in rows['anchor/parent'] if r['case']==cid)['reachable'] else family
            groups.setdefault(label,[]).append(cid)
        losses[identity]={}
        for family,cases in sorted(groups.items()):
            c=min(cases,key=lambda c:hashlib.sha256(c.encode()).hexdigest())
            selected.setdefault(c,[]).append(identity+'/'+family); losses[identity][family]=c
    assert len(selected)<=24
    return canonical(data),dict(gained_inputs=gained,selected_cases=sorted(selected),reasons=selected,
        representative_losses=losses,rule='All two gain poses plus lowest SHA256(case ID) lost input per specialist/family, disconnection separate',
        scope='Fixed reused mechanism/development cases, not confirmation')


def prepare():
    assert not OUT.exists(); prior=prior_check();OUT.mkdir();RUN.mkdir(parents=True,exist_ok=True)
    assert shutil.disk_usage(RUN).free>=CONFIG['disk_free_floor_bytes']+CONFIG['storage_bytes']
    sources=readz(PRIOR/'sources.json.gz'); pool=readz(PRIOR/'pool.json.gz')
    writej(OUT/'config.json',CONFIG);writez(OUT/'variants.json.gz',make_variants(sources,pool))
    data,traces=panel_and_traces();writez(OUT/'panel.json.gz',data);writej(OUT/'trace_panel.json',traces)
    write_reference(OUT/'exclusions.json',PRIOR/'whole_layout_exclusions.json',load_layouts(PRIOR/'whole_layout_exclusions.json'))
    items=readz(OUT/'variants.json.gz')['items'];count=sum(map(len,tasks(items,[])))
    assert count*1680<CONFIG['call_cap']
    writej(OUT/'preparation.json',dict(prior=prior,aliases=len(items),physical_models=count,planned_calls=count*1680,
        planned_trace_calls=sum(len(t) for t in tasks([i for i in items if i['model']['representation']=='connected'],[]))*len(traces['selected_cases']),
        new_cases=0,evolution=False,independent_confirmation=False))


def preflight():
    assert not (OUT/'preflight.json').exists() and not (OUT/'registration.json').exists()
    from .copy_specialization import fixture_sources
    from .specialization_genome import eligible,copy
    from .connected_trace import respond
    sources=fixture_sources();g=Genome.from_dict(sources['anchors']['parent']['genome']);r,d,t=eligible(g)[0]
    c,_=copy(g,r,d,t,True)
    # Three existing excluded fixture inputs; synthetic genomes only.
    fixture=readz(ROOT/'results/restoration_assay/discarded_corpus_fixture.json.gz')
    ids=fixture['queries']['all'][:3];mazes=[m for m in fixture['mazes'] if m['case_id'] in ids]
    cases=cases_from_manifest(mazes);checker=Checker(cases)
    models=[dict(id='fixture/'+mode,model=dict(representation='connected',genome=intervene(c,r,d,t,mode).to_dict())) for mode in COPY_MODES]
    models+=references(sources);started=time.monotonic();receipts=[];native=0
    for task in tasks(models,ids):
        receipt=evaluate_task(task,mazes,'m21fixture');receipts.append(receipt)
        for e,result in zip(task,receipt['entries']):
            org=organism(e['model'])
            for row in result['rows']:
                checker.row(row);o=cases[row['case']];m=o.maze
                assert record(org.react(m.cells,m.w,m.h,m.start,m.goal),o)==row;native+=1
                if e['model']['representation']=='connected':
                    reaction,history,_=respond(e['model'],m);assert record(reaction,o)==row
                    assert len(history)==reaction.steps+1;native+=1
    writez(OUT/'preflight_receipts.json.gz',receipts)
    writej(OUT/'preflight.json',dict(status='PASS',fixture_calls=sum(r['calls'] for r in receipts),
        candidate_seconds=sum(r['candidate_seconds'] for r in receipts),extra_native_and_trace_checks=native,
        wall_seconds=time.monotonic()-started,new_cases=0,scientific_variant_calls=0))


def register():
    assert not (OUT/'registration.json').exists() and (OUT/'preflight.json').exists()
    reg=shared.source_manifest();paths=[p for p in OUT.rglob('*') if p.is_file()]
    paths += [ROOT/'docs/READOUT_CAUSALITY.md',ROOT/'tests/test_readout_causality.py',ROOT/'tools/run_m21_workflow.py',PRIOR/'completion.json']
    reg['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    reg.update(phase='M21',scientific_variant_calls=0,new_case_generation=False,selection=False)
    writej(OUT/'registration.json',reg)


def guard(directory,config,started):
    if time.monotonic()-started>=config['session_wall_seconds']:return 'wall'
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
            wall_seconds=time.monotonic()-started,rss_peak_bytes=shared._peak_rss));j.close();assert not reason,reason


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
    caps={i:capabilities_plus(rs,data['metadata']) for i,rs in rows.items()}
    gained=json.loads((OUT/'trace_panel.json').read_text())['gained_inputs'];items=readz(OUT/'variants.json.gz')['items']
    source=caps['anchor/parent'];case_rows={i:{r['case']:r for r in rs} for i,rs in rows.items()}
    protected=list(readz(PRIOR/'sources.json.gz')['protected']);union=set().union(*(caps[i]['success'] for i in protected))
    ordinary={m['base']:m for cid,m in data['metadata'].items() if cid in data['queries']['all'] and m['family'].startswith('ordinary_')}
    metrics={}
    for item in items:
        i=item['id'];c=caps[i]
        strata={}
        for base,m in ordinary.items():
            length=len(m['path'])-1;label=m['family']+'/'+('16plus' if length>=16 else '8to15' if length>=8 else '0to7')
            cell=strata.setdefault(label,dict(bases=0,correct_both_poses=0));cell['bases']+=1;cell['correct_both_poses']+=base in c['ordinary_bases']
        comparisons={}
        if item.get('specialist'):
            other=caps[item['specialist']+'/intact/saved']
            comparisons=dict(specialist_correct_lost=len(other['success']-c['success']),specialist_correct_gained=len(c['success']-other['success']),
                source_losses_recovered=len((source['success']-other['success'])&c['success']),
                same_mask_status_steps=sum(all(a[k]==b[k] for k in ('mask','status','steps')) for a,b in zip(rows[i],rows[item['specialist']+'/intact/saved'])))
        metrics[i]=dict(metrics=c['summary'],correct_inputs=len(c['success']),correct_no_path=len(c['correct_no_path']),
            source_correct_lost=len(source['success']-c['success']),source_correct_gained=len(c['success']-source['success']),
            lost_source_inputs=sorted(source['success']-c['success']),new_inputs_beyond_protected=sorted(c['success']-union),
            ordinary_length_strata=strata,versus_saved_specialist=comparisons,
            gained_both_poses=all(x in c['success'] for x in gained),gained_input_responses=[case_rows[i][x] for x in gained])
    tests={}
    for i in SPECIALISTS:
        observed=i+'/intact/saved';old=i+'/intact/restore_old'
        tests[i]=dict(observed_both_poses=metrics[observed]['gained_both_poses'],
            old_terminal_both_poses=metrics[old]['gained_both_poses'],
            terminal_required_in_saved_background=metrics[observed]['gained_both_poses'] and not metrics[old]['gained_both_poses'],
            copy_modes={mode:metrics[i+'/'+mode+'/saved']['gained_both_poses'] for mode in COPY_MODES},
            terminal_only={bg+'/'+op:metrics[i+'/terminal_only/'+bg+'/'+op]['gained_both_poses'] for bg in ('source','copy') for op in ('append','replace')})
    return canonical(dict(status='mechanism_evaluated',independent_confirmation=False,selection=False,new_cases=0,
        inputs=len(data['queries']['all']),aliases=len(items),models=metrics,causal_tests=tests,
        limits='Conditional interventions on four selected related specialists and reused M20 data; not new confirmation, evolutionary accessibility, generalization, speed or isolated arithmetic-op causality.'))


def analyze():
    check();assert not (OUT/'summary.json').exists();data,rows,models=load()
    writej(OUT/'summary.json',summary(data,rows));writez(OUT/'responses.json.gz',dict(models=[dict(aliases=e['aliases'],rows=rs) for e,rs in models]))


def audit():
    config=check();assert not (OUT/'audit.json').exists();started=time.monotonic();data,rows,models=load()
    assert make_variants(readz(PRIOR/'sources.json.gz'),readz(PRIOR/'pool.json.gz'))==readz(OUT/'variants.json.gz')
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
    saved=readz(PRIOR/'final_responses.json.gz');oldrows={i:e['rows'] for e in saved['models'] for i in e['aliases']}
    comparisons=0
    for identity in SPECIALISTS:
        assert rows[identity+'/intact/saved']==oldrows[identity];comparisons+=1680
    for item in items:
        if item['id'] in oldrows:assert rows[item['id']]==oldrows[item['id']];comparisons+=1680
        if item['kind']=='control':assert all(r['optimal'] or r['no_path'] for r in rows[item['id']])
    assert summary(data,rows)==json.loads((OUT/'summary.json').read_text())
    with writer_lock(RUN/'evaluation'):
        j=Journal(RUN/'evaluation');chain=j.verify_chain();assert not j.pending() and calls==j.get('usage')['calls'];j.close()
    writej(OUT/'audit.json',dict(status='PASS',native_replays=calls,independent_grades=calls,native_counted_work=work,
        chain=chain,all_transformations_panel_tasks_summary_replayed=True,m20_exact_response_comparisons=comparisons,
        wall_seconds=time.monotonic()-started,limitation='Shared frozen production VM; independent raster grader, ALL-native replay.'))


def traces(audit_mode=False):
    from .connected_trace import respond
    import numpy as np
    config=check();name='trace_audit.json' if audit_mode else 'trace_session.json'
    assert not (OUT/name).exists();started=time.monotonic();data,rows,models=load()
    ids=json.loads((OUT/'trace_panel.json').read_text())['selected_cases']
    cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in ids]);records=[];calls=work=0
    saved=readz(OUT/'traces.json.gz') if audit_mode else None;position=0
    for e,rs in models:
        if e['model']['representation']!='connected':continue
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
    writej(OUT/name,dict(status='PASS',calls=calls,counted_work=work,wall_seconds=time.monotonic()-started,
                        complete_history_replay=audit_mode,all_production_rows_equal=True,rss_peak_bytes=shared._peak_rss))


if __name__=='__main__':
    actions=dict(prepare=prepare,preflight=preflight,register=register,run=run,analyze=analyze,audit=audit,
                 traces=traces,trace_audit=lambda:traces(True))
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=actions)
    actions[parser.parse_args().action]()
