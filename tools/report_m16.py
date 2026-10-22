"""Saved-record report tables and passive trace interpretation, no new evaluations."""
import json,sys
from pathlib import Path
from collections import Counter
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.restoration_assay import OUT,RUN,check,readz,writej


def main():
    check();assert not (OUT/'report.md').exists() and not (OUT/'interpretation.json').exists()
    assert json.loads((RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
    audits={k:json.loads((OUT/f'{k}_audit.json').read_text()) for k in ('screen','final','trace')}
    assert all(v['status']=='PASS' for v in audits.values())
    s=json.loads((OUT/'summary.json').read_text());trace=readz(OUT/'traces.json.gz');traces=[]
    indexed={(x['anchor'],x['case']):x for x in trace['traces']}
    for x in trace['traces']:
        h=np.asarray(x['history'],dtype=np.uint16);r=x['response'];other=indexed[('parent' if x['anchor']=='child' else 'child',x['case'])]
        oh=np.asarray(other['history'],dtype=np.uint16);upto=min(len(h),len(oh));first=next((t for t in range(upto) if not np.array_equal(h[t],oh[t])),None)
        traces.append(dict(anchor=x['anchor'],group=x['group'],case=x['case'],status=r['status'],steps=r['steps'],reachable=r['reachable'],
            optimal=r['optimal'],correct_no_path=r['no_path'],first_state_divergence=first,
            emitted_cells=int((h[-1,2]>0).sum()),channel_nonzero_final=[int((v>0).sum()) for v in h[-1]],
            channel_max_final=[int(v.max()) for v in h[-1]],
            changing_cells_last_tick=[int((h[-1,k]!=h[-2,k]).sum()) for k in range(8)] if len(h)>1 else [],
            c0_formula_verified=x['c0_formula_matches']))
    choices=readz(OUT/'choices.json.gz');pool=readz(OUT/'pool.json.gz')
    mutations=[i for i in pool['items'] if i['kind']=='mutation'];noops=sum(all(e['before']==e['after'] for e in i['events']) for i in mutations)
    diagnostics={i:v for i,v in s['models'].items() if v['kind']=='diagnostic'}
    evidence=dict(scope='Saved M16 confirmation and registered development histories only; no new inference or reselection',traces=traces,
        mutation_proposals=len(mutations),mutation_opportunities=sum(len(i['events']) for i in mutations),
        all_events_noop_proposals=noops,diagnostic_passes=[i for i,v in diagnostics.items() if v['joint_restoration_pass']],
        screen_reference_eligible=choices['screen_features']['anchor/child']['reference_eligible'],
        final_reference_eligible=s['reference_eligible'])
    writej(OUT/'interpretation.json',evidence)
    lines=['# M16 restoration assay — audited evidence','',
        f"Primary joint-mutation passes: **{len(s['primary_passes'])}/4**. Eligible reference endpoint on fresh confirmation: **{s['reference_eligible']}**. These are fixed one-/two-edit neighborhoods of two related random-origin anchors, not independent evolutionary replicates.",'',
        '## Same-case anchors','',
        '| Anchor | Pairs /400 | Corridors /200 | Ordinary both poses /256 | Correct no-path /168 | False reachable no-path |','|---|---:|---:|---:|---:|---:|']
    for i in ('anchor/parent','anchor/child'):
        m=s['models'][i]['metrics'];lines.append(f"| {i} | {m['paired']} | {m['by_domain']['corridor']['optimal']} | {m['ordinary_bases_both_poses']} | {m['correct_no_path']} | {m['false_no_path']} |")
    lines+=['','## Prospectively frozen nominees','',
      'Joint restoration requires the exact union of both anchors’ pair, corridor, ordinary and correct-disconnection successes, all child target pairs beyond protected references, zero false no-path, and nonempty denominators. A diagnostic pass is an intervention result, not an evolved discovery. Aggregate ranking uses the same mutation pool and development inputs. No final-data role substitution.','',
      '| Role | Identity | Targets kept | Required ordinary lost | Required disconnections lost | False | Pass |','|---|---|---:|---:|---:|---:|---|']
    for n in s['nominations']:
        v=n['result'];lines.append(f"| {n['label']} | {n['identity']} | {v['retained_targets']}/{v['target_pairs']} | {v['lost_required']['ordinary_bases']} | {v['lost_required']['correct_no_path']} | {v['metrics']['false_no_path']} | {v['joint_restoration_pass']} |")
    lines+=['',f"All fixed diagnostics were carried forward before confirmation: {len(diagnostics)} aliases; {len(evidence['diagnostic_passes'])} pass the full gate. Diagnostic pass identities: `{evidence['diagnostic_passes']}`.",
      'Every nominee and fixed diagnostic has full exact-parent/child gains/losses, protected-union comparisons and ordinary length strata in summary.json. Nomination roles can alias the same genome and must not be counted as independent successes.','',
      '## Passive regulation traces (development data)','',
      'The parent C0 update is min(65535, C0 + max(0, C5 − source flag)); the child substitutes C7 for C5. The recurrence passed at every site of every recorded complete tick. The trace adapter makes no candidate change and stops at the original runtime limits. Terminal fields match production M1 and the saved screen responses; all histories replay in the trace audit. This verifies that recurrence and the recorded behavior, not a universal algorithmic explanation.','',
      '| Group | Anchor | Status | Ticks | Path pixels | First state divergence |','|---|---|---|---:|---:|---:|']
    for x in traces:lines.append(f"| {x['group']} | {x['anchor']} | {x['status']} | {x['steps']} | {x['emitted_cells']} | {x['first_state_divergence']} |")
    lines+=['','## Protocol, ancestry and costs','',
      f"Mutation proposals: {len(mutations):,}, comprising 1,024 per exact anchor and {evidence['mutation_opportunities']:,} mutation opportunities; {noops} proposals have only genotype-no-op events. Each anchor has 512 one-edit and 512 sequential two-edit variants, plus 1,024 common random references and 72 fixed diagnostic probes. Parent-derived variants have 1–2 M16 edits from the inherited parent; child-derived variants have 1–2 M16 edits after the single M15 edit. No ancestral chain or known solver was silently substituted.",'',
      'Pool seed 2026102202, development seed 2026102203, confirmation seed 2026102204. All pool variants were published before the common 712-input development panel; all choices were published before the 1,680-input independent panel. Related grammar contexts and poses limit transfer claims. Equal logical evaluations do not imply equal CPU. Separate intact controls are never parents.','',
      '| Phase | Calls | Candidate seconds | Worker CPU seconds | Wall seconds | Work | Peak tree RSS GiB |','|---|---:|---:|---:|---:|---:|---:|']
    for name in ('screen','final'):
        v=json.loads((OUT/f'{name}_session.json').read_text());u=v['usage']
        lines.append(f"| {name} | {u['calls']:,} | {u['candidate_seconds']:.2f} | {u['cpu_seconds']:.2f} | {v['wall_seconds']:.2f} | {u['work']:,} | {v['rss_peak_bytes']/2**30:.3f} |")
    lines+=['',f"Passive traces add {trace['calls']} executions (instrumented plus native), {trace['work']:,} work, {trace['trace_seconds']:.2f} instrumented seconds, {trace['native_seconds']:.2f} native seconds, and {trace['wall_seconds']:.2f} wall seconds. Trace audit separately adds {audits['trace']['calls']} executions/{audits['trace']['work']:,} work/{audits['trace']['wall_seconds']:.2f} wall seconds. Instrumentation allocation is recorded per trace and excluded from production candidate memory.",'',
       f"Screen audit: {audits['screen']['independent_grades']:,} independent grades; {audits['screen']['native_replays']:,} native replays; {audits['screen']['wall_seconds']:.2f}s. Final audit: ALL {audits['final']['native_replays']:,} native responses/grades and summary, plus {audits['final']['conventional_calls']:,} BFS/A*/bitwave calls; {audits['final']['wall_seconds']:.2f}s. Both intact controls solve every queried input. Shared VM/mutation code, independent raster grader; not a second full interpreter.",'',
       'Five focused tests passed, not the full suite. Two successful pre-registration artificial-founder rehearsals are preserved, including the initial rehearsal before an exclusion observer was added. The observer records early rejected layouts without changing accepted cases, query order, metadata or RNG; fixture equivalence was checked. Preparation costs in both preflight.json packets are additional, not scientific discoveries. Unit tests additionally execute 15 native/15 instrumented cases per invocation, with two invocations; timing was not separately instrumented. All fixture and test layouts are excluded.','',
       'No post-registration scientific repair, new runtime, recombination, solver injection or final-data reselection. Preserve all M15 and M16 records. Any further experiment needs a new protocol; none is launched by this report.','']
    (OUT/'report.md').write_text('\n'.join(lines));print('M16 evidence tables written; review and add actual interpretation before sealing.')


if __name__=='__main__':main()
