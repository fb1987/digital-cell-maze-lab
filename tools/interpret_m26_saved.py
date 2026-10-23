"""Posthoc witness supplement for verified M26; saved receipts/decisions only.

Examines ALL novel complete8 hit stages, not a chosen winner. Same-panel parent
unit attribution and population-level preservation prevent overstating mutation
acquisition or loss when another solver survives. Never evaluates a candidate.
"""
import gzip
import hashlib
import json
from collections import Counter,defaultdict
from pathlib import Path
import sqlite3
import time
import zlib
import resource
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/evolvability_audit_m26'
OLD=ROOT/'results/skill_integration'
RUN=ROOT/'runs/skill_integration_m25'


def load_lines(p):
    with gzip.open(p,'rt') as f:return [json.loads(l) for l in f]


def un(b):return json.loads(zlib.decompress(b))


def main():
    start,cpu=time.monotonic(),time.process_time()
    target=OUT/'interpretation.json'
    assert not target.exists() and json.loads((OUT/'verification.json').read_text())['status']=='PASS'
    cohort={r['id']:r for r in load_lines(OUT/'cohorts.jsonl.gz')}
    hits=load_lines(OUT/'novel_hits.jsonl.gz')
    units=json.loads((OUT/'ordinary_units.json').read_text())
    complete=[h for h in hits if h['novel_complete8']]
    needed={h['stage'] for h in complete}
    complete_ids={h['id'] for h in complete}
    con=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True)
    con.execute('PRAGMA query_only=ON');con.execute('BEGIN')
    with gzip.open(OLD/'founders.json.gz','rt') as f:initial=json.load(f)
    with gzip.open(OLD/'inherited_registry.json.gz','rt') as f:inherited=json.load(f)
    models={i:e['item'] for i,e in inherited.items()}
    offspring=defaultdict(list)
    candidate_witnesses={}
    unit_witnesses=[]
    extra_mutation_events={}
    for n,kind,g,inp,dec in con.execute('SELECT n,kind,generation,input,decision FROM stages ORDER BY n'):
        decisions=un(dec)
        if n in needed:
            data=un(inp);rows=[{} for _ in initial];receipts={}
            for task,blob,rhash in con.execute('SELECT n,result,result_hash FROM tasks WHERE stage=? ORDER BY n',(n,)):
                assert hashlib.sha256(blob).hexdigest()==rhash
                for e in un(blob)['entries']:
                    for k,i in e['aliases']:
                        rows[k][i]=e['rows'];receipts[k,i]=dict(stage=n,task=task,result_hash=rhash)
            for h in complete:
                if h['stage']!=n:continue
                k=next(k for k,s in enumerate(initial) if s['name']==h['population'])
                r=cohort[h['id']];rs=rows[k];decision=decisions[k]
                perbase=[]
                for base in h['novel_complete8']:
                    cs=sorted(c for c in data['queries'][initial[k]['curriculum']] if data['metadata'][c].get('base')==base)
                    assert len(cs)==2
                    def solved(i):return i in rs and all(next(row for row in rs[i] if row['case']==cid)['optimal'] for cid in cs)
                    solvers=[i for i in rs if solved(i)]
                    retained=sorted(set(solvers)&set(decision['survivors']))
                    assert h['id'] in solvers
                    parent=r['parent'];root=r['root']
                    parent_solved=solved(parent) if parent in rs else None
                    root_solved=solved(root) if root in rs else None
                    entry=h['id']
                    while entry in cohort and cohort[entry]['parent']:
                        entry=cohort[entry]['parent']
                    selected_after=(h['id'] in decision['survivors'])
                    comparison_ids=set(solvers)|{i['id'] for i in initial[k]['protected']}|{h['id']}
                    comparison_ids.update(i for i in (parent,root,entry) if i in rs)
                    witness=dict(id=h['id'],population=h['population'],stage=n,generation=g,base=base,
                                 unit=units[base],case_ids=cs,child_retained=selected_after,
                                 solvers=sorted(solvers),retained_solvers=retained,
                                 parent_queried=parent in rs,parent_solved=parent_solved,
                                 root_queried=root in rs,root_solved=root_solved,
                                 initial_live_ancestor=entry,entry_queried=entry in rs,
                                 entry_solved=solved(entry) if entry in rs else None,
                                 newly_correct_vs_same_panel_parent=parent_solved is False,
                                 all_parent_correct_inputs_retained=(None if h['parent'] is None else h['parent']['all_old_correct_inputs_retained']),
                                 root90=(None if h['root'] is None else h['root']['domain90_and_disconnection90_zero_false']),
                                 no_path_correct=h['counts']['no_path'],false_no_path=h['counts']['false'],
                                 metadata={c:data['metadata'][c] for c in cs},
                                 saved_mazes=[m for m in data['mazes'] if m['case_id'] in cs],
                                 saved_rows={i:[row for row in rs[i] if row['case'] in cs] for i in sorted(comparison_ids)},
                                 receipts={i:receipts[k,i] for i in sorted(comparison_ids)})
                    assert len(witness['saved_mazes'])==2
                    unit_witnesses.append(witness);perbase.append(witness)
                candidate_witnesses.setdefault(h['id'],[]).append(dict(stage=n,generation=g,
                   newly_correct_vs_parent_bases=[w['base'] for w in perbase if w['newly_correct_vs_same_panel_parent']],
                   inherited_from_same_panel_parent_bases=[w['base'] for w in perbase if w['parent_solved'] is True]))
        for d in decisions:
            for b in d['births']:
                i=b['item']['id']
                if i in complete_ids or b['item']['parent'] in complete_ids:
                    models[i]=b['item'];extra_mutation_events[i]=b['events']
                if b['item']['parent']:offspring[b['item']['parent']].append(i)
    con.close()
    details={}
    for i in sorted(complete_ids):
        r=cohort[i];hs=[h for h in complete if h['id']==i];firsthit=min(h['generation'] for h in hs)
        after=[j for j in offspring[i] if cohort[j]['birth']>firsthit]
        details[i]=dict(population=r['population'],noop=r['noop'],operator=r['operator'],parent_policy=r['parent_policy'],
           instructions=r['instructions'],first_training_generation=r['first']['generation'],
           first_novel_complete_generation=firsthit,first_hit_after_initial_exposure=firsthit>r['first']['generation'],
           survived_first_novel_hit=hs[0]['survived'],after_hit_direct_offspring=len(after),
           changed_after_hit_direct_offspring=sum(not cohort[j]['noop'] for j in after),
           offspring_ids=after,final_live=r['final_live'],final_archive=r['final_archive'],
           final_live_descendants=r['live_descendants'],all_novel_units=r['novel_complete_bases'],
           max_novel_edges=max(units[b]['edges'] for b in r['novel_complete_bases']),
           lifetime_training_exposures=r['train_exposures'],observations=candidate_witnesses[i],
           model=models[i],events=extra_mutation_events[i])
    episodes={}
    for w in unit_witnesses:
        key=(w['population'],w['stage'],w['base'])
        if key in episodes:assert episodes[key]['solvers']==w['solvers']
        episodes[key]=w
    first_changed=[r for r in cohort.values() if r['mutant'] and not r['noop'] and r['first']]
    record_stats={}
    for name in sorted({r['population'] for r in first_changed}):
        rs=[r for r in first_changed if r['population']==name]
        flagsets=dict(all=rs,ordinary8=[r for r in rs if r['first']['counts']['ordinary8']],
          novel_complete8=[r for r in rs if r['first']['novel_complete8']],
          novel_single8=[r for r in rs if r['first']['novel_single8']],
          parent_ordinary8_gainer=[r for r in rs if r['first']['parent'] and r['first']['parent']['ordinary8']['gained']],
          parent_ordinary8_gainer_full_retention=[r for r in rs if r['first']['parent'] and r['first']['parent']['ordinary8']['gained'] and r['first']['parent']['all_old_correct_inputs_retained'] and not r['first']['counts']['false']])
        record_stats[name]={flag:dict(identities=len(items),survived=sum(r['survived_first'] for r in items),
             bred=sum(bool(r['children_after_first']) for r in items),final_live=sum(r['final_live'] for r in items),
             final_live_descendants=sum(bool(r['live_descendants']) for r in items)) for flag,items in flagsets.items()}
    stats=dict(complete_hit_presentations=len(complete),complete_identities=len(complete_ids),
       changed_complete_identities=sum(not v['noop'] for v in details.values()),
       first_exposure_complete_identities=sum(not v['first_hit_after_initial_exposure'] for v in details.values()),
       later_first_complete_identities=sum(v['first_hit_after_initial_exposure'] for v in details.values()),
       survived_first_hit=sum(v['survived_first_novel_hit'] for v in details.values()),
       bred_after_first_hit=sum(bool(v['after_hit_direct_offspring']) for v in details.values()),
       after_hit_direct_offspring=sum(v['after_hit_direct_offspring'] for v in details.values()),
       final_live=sum(v['final_live'] for v in details.values()),final_archive=sum(v['final_archive'] for v in details.values()),
       with_final_live_descendants=sum(bool(v['final_live_descendants']) for v in details.values()),
       distinct_novel_bases=len({w['base'] for w in unit_witnesses}),
       unique_population_stage_base_episodes=len(episodes),
       episodes_retaining_any_solver=sum(bool(w['retained_solvers']) for w in episodes.values()),
       episodes_retaining_no_solver=sum(not w['retained_solvers'] for w in episodes.values()),
       newly_correct_vs_parent_identities=len({w['id'] for w in unit_witnesses if w['newly_correct_vs_same_panel_parent']}),
       newly_correct_vs_parent_full_retention_identities=len({w['id'] for w in unit_witnesses if w['newly_correct_vs_same_panel_parent'] and w['all_parent_correct_inputs_retained']}),
       parent_not_queried_identities=len({w['id'] for w in unit_witnesses if not w['parent_queried']}),
       matched_parent_already_solved_identities=len({w['id'] for w in unit_witnesses if w['parent_solved'] is True}),
       lengths=dict(Counter(str(w['unit']['edges']) for w in episodes.values())),
       families=dict(Counter(w['unit']['family'] for w in episodes.values())),
       sources=dict(Counter(w['unit']['source'] for w in episodes.values())))
    # Admission headroom of these observed variants, not an intervention.
    stats['target_variants_total_append_eligible']=sum(v['instructions']+3<=128 for v in details.values())
    stats['target_variant_instruction_range']=[min(v['instructions'] for v in details.values()),max(v['instructions'] for v in details.values())]
    # Fixed bank repeats are countable units, never independent discoveries.
    exposure=json.loads((OUT/'summary.json').read_text())['population_exposures']
    summary=dict(scope='Posthoc witness/lifecycle interpretation of verified M26 outputs. All novel complete8 hits included; no new inference/cases/reselection.',
         complete8=stats,first_changed_mutants=record_stats,candidates=details,
         episodes=[{k:v for k,v in w.items() if k not in ('saved_mazes','saved_rows','metadata','receipts')} for w in episodes.values()],
         costs=dict(wall_seconds=time.monotonic()-start,cpu_seconds=time.process_time()-cpu,
                    peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
                    inference_calls=0,generated_layouts=0),
         verification_limit='Witness grouping uses audited grade flags, not a second VM; no unseen-case confirmation. This supplement was written after viewing M26 primary counts.')
    with gzip.open(OUT/'novel_complete_witnesses.json.gz','xt') as f:json.dump(unit_witnesses,f,sort_keys=True)
    with target.open('x') as f:json.dump(summary,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(stats,sort_keys=True,indent=2))


if __name__=='__main__':
    try:main()
    except BaseException:
        import traceback
        with (OUT/('interpretation_failure_'+time.strftime('%Y%m%d_%H%M%S')+'.json')).open('x') as f:json.dump(dict(traceback=traceback.format_exc()),f,indent=2)
        raise
