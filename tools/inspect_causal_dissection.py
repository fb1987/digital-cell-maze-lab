"""Post-hoc scope checks on saved V12V outcomes; no candidate inference."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.causal_dissection_data import OUT,load,read_compressed
from maze_evolution.routing_transfer import lines
from maze_evolution.routing_mechanism_audit import component

def main():
    panel=read_compressed(OUT/'panel.json.gz');metrics=read_compressed(OUT/'metrics.json.gz');analysis=read_compressed(OUT/'analysis.json.gz');cases,_,meta=load(OUT/'confirmation');aliases=panel['aliases'];reverse={p:n for n,p in aliases.items()}
    findings={};nonintact={p for n,p in aliases.items() if n!='intact'}
    for e in lines(OUT/'confirmation/responses.jsonl.gz'):
        if e['scope']!='normal' or e['model'] not in nonintact or not e['row']['no_path']:continue
        cid=e['row']['case'];m=cases[cid].maze
        findings.setdefault(reverse[e['model']],[]).append(dict(case=cid,base=meta[cid]['base'],family=meta[cid]['family'],source_component=len(component(m,m.start)),goal_component=len(component(m,m.goal))))
    a=metrics[aliases['d07_no_store']+'|normal']['details'];b=metrics[aliases['d12_no_store']+'|normal']['details'];assert a.keys()==b.keys()
    mismatches=[k for k in a if a[k]['complete']!=b[k]['complete']]
    early=analysis['comparisons']['d07->d07_no_store']['positive_by_context'];late=analysis['comparisons']['d12_no_store->d12_restore_store']['positive_by_context'];effects={}
    for key in early:
        before=early[key]['before']-early[key]['after'];after=late[key]['after']-late[key]['before']
        effects[key]=dict(store_effect_early=before,store_effect_late=after,interaction=after-before)
    (OUT/'scope_checks.json').write_text(json.dumps(dict(candidate_calls=0,post_hoc=True,
        explicit_no_path_successes=findings,no_store_background_pair_mismatches=mismatches,
        store_by_background_interaction=effects,
        later_historical_events={n:panel['historical_events'][n] for n in ('d09','d10','d11','d12')},
        interpretation='A summary of already registered comparisons and saved observations. Does not identify which later mutation causes the reversal; no new edited genome evaluated.'),indent=2)+'\n')

if __name__=='__main__':main()
