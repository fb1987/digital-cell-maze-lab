"""M17 retrospective saved-record accounting and static dependencies. No inference."""
import json,sys,sqlite3
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.spare_state_assay import ROOT,OUT,RUN,check,readz,writej,load,references
from maze_evolution.deep_campaign_store import unpacked
from maze_evolution.spare_genome import Genome as Spare
from maze_evolution.modular_genome import Genome as Base,REFS
from maze_evolution.restoration_metrics import reference_sets


def static_description(model):
    g=(Spare if model['representation']=='spare' else Base).from_dict(model['genome'])
    modules=[]
    for k,block in enumerate(g.blocks):
        seen=set();channels=set();pending=[len(block)-1] if block else []
        while pending:
            i=pending.pop()
            if i in seen:continue
            seen.add(i);gene=block[i];row=gene.row()
            refs=[row[j] for j in REFS[gene.op]]+([gene.gate] if gene.gate!=64 else [])
            for r in refs:
                if r>=12:pending.append(r-12)
                elif r<8:channels.add(g.ports[k][r])
            if gene.op in (4,5,6,7,14,15,17):channels.add(g.ports[k][gene.a])
        modules.append(dict(channel=k,nodes=len(block),potential_output_nodes=len(seen),reads_channels=sorted(channels)))
    cone={2,7}
    while True:
        nxt=cone|{c for k in cone for c in modules[k]['reads_channels']}
        if nxt==cone:break
        cone=nxt
    return dict(instructions=g.instructions,active_writers=sum(bool(b) for b in g.blocks),
        active_spare_writers=[k for k in range(8,len(g.blocks)) if g.blocks[k]],blocks=modules,
        output_explicit_halt_cone=sorted(cone),spare_in_output_explicit_halt_cone=sorted(cone&{8,9}),
        limitation='Conservative static expression cone, not branch feasibility or causal intervention. All active channels can affect global quiescence/work even outside this cone.')


def accounting(final=False):
    phase='final' if final else 'screen'
    items=readz(OUT/'choices.json.gz')['items'] if final else readz(OUT/'pool.json.gz')['items']+references(readz(OUT/'sources.json.gz'))
    lookup={i['id']:i for i in items};con=sqlite3.connect(f'file:{RUN/phase}/campaign.sqlite?mode=ro',uri=True)
    buckets={};arms={}
    def add(d,key,e):
        x=d.setdefault(key,dict(physical_models=0,calls=0,work=0,candidate_seconds=0.,max_array_bytes=0))
        x['physical_models']+=1
        for k in ('calls','work','candidate_seconds'):x[k]+=e[k]
        x['max_array_bytes']=max(x['max_array_bytes'],max(r['array_bytes'] for r in e['rows']))
    for result, in con.execute('select result from tasks order by n'):
        for e in unpacked(result)['entries']:
            members=[lookup[i] for i in e['aliases']];tags=set()
            for i in members:tags.add(i['arm'] if i['kind']=='mutation' else 'random_'+i['arm'] if i['kind']=='random' else 'references')
            add(buckets,'+'.join(sorted(tags)),e)
            for arm in {i['arm'] for i in members if i['kind']=='mutation'}:add(arms,arm,e)
    con.close();session=json.loads((OUT/f'{phase}_session.json').read_text())
    for key in ('calls','work','candidate_seconds'):
        assert abs(sum(x[key] for x in buckets.values())-session['usage'][key])<1e-5
    q=1680 if final else 712
    return dict(disjoint_physical_buckets=buckets,inclusive_arm_costs=arms,
        nominal_mutation_queries_per_arm={arm:sum(i.get('arm')==arm and i['kind']=='mutation' for i in items)*q for arm in ('unchanged','overwrite','spare')},
        note='Inclusive arm costs count shared genotypes in each relevant arm; do not sum. Disjoint buckets sum exactly to physical usage. Final nominal identity slots may merge nomination roles; fixed primary role allocation is4*1680 per arm.')


def main():
    check();assert not (OUT/'report.md').exists() and not (OUT/'interpretation.json').exists()
    assert json.loads((RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
    audits={k:json.loads((OUT/f'{k}_audit.json').read_text()) for k in ('screen','final')}
    assert all(x['status']=='PASS' for x in audits.values())
    s=json.loads((OUT/'summary.json').read_text());choices=readz(OUT/'choices.json.gz');lookup={i['id']:i for i in choices['items']}
    pool=readz(OUT/'pool.json.gz')['items'];sources=readz(OUT/'sources.json.gz');data,rows,models=load()
    caps,union,targets,pm=reference_sets(rows,data['metadata'],list(sources['protected']))
    screen={}
    for arm in ('unchanged','overwrite','spare'):
        entries=[i for i in pool if i.get('arm')==arm and i['kind']=='mutation']
        partial=[i['id'] for i in entries if caps[i['id']]['pairs']&targets and caps[i['id']]['correct_no_path'] and not caps[i['id']]['false']]
        screen[arm]=dict(proposals=len(entries),variation_opportunities=sum(len(i['events']) for i in entries),
            any_target_and_any_disconnection_without_false=len(partial),partial_identities=partial,
            full_gate_passes=[i['id'] for i in entries if choices['screen_features'][i['id']]['joint_restoration_pass']],
            event_kinds=dict(Counter(e['kind'] for i in entries for e in i['events'])),
            initial_copy_noops=sum(i['events'][0]['before']==i['events'][0]['after'] for i in entries))
    spare_items=[i for i in pool if i.get('arm')=='spare' and i['kind']=='mutation']
    static_pool={i['id']:static_description(i['model']) for i in spare_items}
    spare_access=dict(proposals=len(spare_items),
        has_spare_in_output_explicit_halt_cone=sum(bool(x['spare_in_output_explicit_halt_cone']) for x in static_pool.values()),
        active_writer_counts=dict(Counter(x['active_writers'] for x in static_pool.values())),
        max_instructions=max(x['instructions'] for x in static_pool.values()),
        note='Saved-genome conservative static count; ignores path feasibility, does not establish actual active computation. Spare channels outside the cone can still affect quiescence and work.')
    finaldata,finalrows,_=load(True);descriptions={};equivalences={}
    for n in s['nominations']:
        i=lookup[n['identity']];descriptions[i['id']]=static_description(i['model'])
        signature=lambda rs:[(r['case'],r['mask'],r['status'],r['steps']) for r in rs]
        equivalences[i['id']]=[r for r in ('anchor/parent','anchor/child',*sources['protected']) if signature(finalrows[i['id']])==signature(finalrows[r])]
    evidence=dict(scope='Saved records only; zero new candidate evaluations',screen=screen,spare_access=spare_access,
        costs={k:accounting(k=='final') for k in ('screen','final')},static_nominees=descriptions,
        final_mask_status_steps_reference_matches=equivalences,reference_eligible=s['reference_eligible'],
        inherited_ancestry='Exact preserved M15 child has one inherited M15 port-swap beyond actual parent. M17 adds3/5opportunities, no sustained lineage or independent origins.',
        final_partial=[n['label'] for n in s['nominations'] if n['result']['retained_targets'] and n['result']['metrics']['correct_no_path'] and not n['result']['metrics']['false_no_path']])
    writej(OUT/'interpretation.json',evidence)
    lines=['# M17 spare-state duplication assay — audited results','',
        'Joint primary passes: **'+', '.join(f"{arm} {len(ids)}/4" for arm,ids in s['arm_primary_passes'].items())+f"**. Fresh reference endpoint eligible: **{s['reference_eligible']}**.",'',
        '## Same-case anchors','',
        '| Anchor | Pairs /400 | Corridors /200 | Ordinary both poses /256 | Correct disconnected /168 | False no-path |','|---|---:|---:|---:|---:|---:|']
    for i in ('anchor/parent','anchor/child'):
        m=s['models'][i]['metrics'];lines.append(f"| {i} | {m['paired']} | {m['by_domain']['corridor']['optimal']} | {m['ordinary_bases_both_poses']} | {m['correct_no_path']} | {m['false_no_path']} |")
    lines+=['','## Frozen confirmation roles','',
        'Pass requires ALL parent/child union skills and ALL child upstream targets beyond protected references, >=8targets in>=2contexts, nonempty denominators and zero false reachable no-path. Four fixed roles per arm; no replacement from random or secondary data. Ordinary counts across different experiments are not acquisition.','',
        '| Role | Identity | Targets | Lost pairs | Lost corridors | Lost ordinary | Lost disconnections | False | Pass |','|---|---|---:|---:|---:|---:|---:|---:|---|']
    for n in s['nominations']:
        v=n['result'];l=v['lost_required'];lines.append(f"| {n['label']} | {n['identity']} | {v['retained_targets']}/{v['target_pairs']} | {l['pairs']} | {l['corridors']} | {l['ordinary_bases']} | {l['correct_no_path']} | {v['metrics']['false_no_path']} | {v['joint_restoration_pass']} |")
    lines+=['','## Development pool — not confirmation','',
        '| Arm | Proposals | Opportunities | Full gate passes | Any target + any disconnection, zero false |','|---|---:|---:|---:|---:|']
    for arm,v in screen.items():lines.append(f"| {arm} | {v['proposals']} | {v['variation_opportunities']} | {len(v['full_gate_passes'])} | {v['any_target_and_any_disconnection_without_false']} |")
    lines+=['','The fixed paired draws use a common random donor and post-initial seed, then diverge in state/operator domains. Each arm has1024proposals and4096variation opportunities; depth3/5includes the initial copy or mutation.256randomM1bodies and their256neutralembeddings are separate references. Two related anchors are not independent origins. Generic copying is enriched prospectively; this does not estimate its spontaneous discovery frequency.','',
        '## Representation and observed costs','',
        'Two initially inactive channels preserve legacy behavior exactly. Same primitive operations,256totalinstruction cap,256ticks/read/dispatch limits; extra memory8bytes/site+152bytes metadata. Activated extra writers can change global quiescence and consume budget even before their values feed old writers. The treatment combines spare state and accessible port/mutation domains; it does not isolate every mechanism.','',
        '| Phase | Physical calls | Candidate seconds | Worker CPU seconds | Wall seconds | Work | Peak RSS GiB |','|---|---:|---:|---:|---:|---:|---:|']
    for k in ('screen','final'):
        v=json.loads((OUT/f'{k}_session.json').read_text());u=v['usage'];lines.append(f"| {k} | {u['calls']:,} | {u['candidate_seconds']:.2f} | {u['cpu_seconds']:.2f} | {v['wall_seconds']:.2f} | {u['work']:,} | {v['rss_peak_bytes']/2**30:.3f} |")
    lines+=['','| Screen mutation arm | Nominal queries | Inclusive physical queries | Candidate seconds | Work | Maximum array bytes |','|---|---:|---:|---:|---:|---:|']
    c=evidence['costs']['screen']
    for arm,v in c['inclusive_arm_costs'].items():lines.append(f"| {arm} | {c['nominal_mutation_queries_per_arm'][arm]:,} | {v['calls']:,} | {v['candidate_seconds']:.2f} | {v['work']:,} | {v['max_array_bytes']:,} |")
    lines+=['','Inclusive physical costs may overlap for shared genotypes; do not sum them. The disjoint buckets in interpretation.json sum exactly to journal usage. Input decoding/inference/emission are included in react timing, model construction is outside; no speed benchmark claim. Work counts reads+dispatches, not every host loop/allocation. Equal nominal queries are not equal CPU or memory. Cheaper incorrect outputs are not faster solutions.','',
        '## Audit and scope','']
    for k,v in audits.items():lines.append(f"- {k}: PASS; {v['independent_grades']:,} independent grades, {v['native_replays']:,} native replays, {v['embedding_comparisons']:,} paired embedding comparisons, {v['wall_seconds']:.2f}s; conventional evaluations{v['conventional_calls']:,}.")
    lines+=['','Screen replays all events/RNG/corpus/tasks/nomination plus fixed native samples; final replays ALLnative responses/grades/summary. Shared VM/operator implementation, independent raster grader. Intact flat/M1/embedded controls and conventional BFS/A*/bitwave remain separate, never candidate parents.','',
        'Six focused tests, not fullsuite;85native test executions and2000mutation-validity steps. Two artificial-founder pre-registration rehearsals each44856candidatecalls plus7warmups,2848embeddingcomparisons;107.76/110.03candidate seconds. The second adds per-model cost recording; all rows/pool/nominations/summary are unchanged and initial artifacts remain. All old/new discarded layouts excluded. No scientific repair, bound extension, adaptive selection, solver injection or post-final reselection.','',
        'Full exact-parent/child/protected-union gains/losses and length strata are in summary.json. Conservative static nominee dependency cones and exact finite-panel response matches are in interpretation.json; static cones do not prove executed activity or omit quiescence effects. No general solver, significance, isolated-policy causality or speed claim.','']
    (OUT/'report.md').write_text('\n'.join(lines));print('M17 actual tables written; add reviewed scientific interpretation before sealing.')
if __name__=='__main__':main()
