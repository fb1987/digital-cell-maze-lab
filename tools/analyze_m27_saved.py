"""M27 postprocessing: fixed cohorts, reference/parent novelty and inheritance.
No fresh cases, candidate executions, nomination or endpoint substitutions.
"""
import sys,json,time
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.transfer_retention import ROOT,OUT,check,readz,writej,load
from maze_evolution.breeding_allocation_metrics import capabilities_plus


def main():
    check();assert not (OUT/'saved_diagnostics.json').exists()
    assert json.loads((OUT/'audit.json').read_text())['status']=='PASS';start=time.monotonic()
    pool=readz(OUT/'pool.json.gz');panels,rows,models,usage,chain=load();data=panels['fresh'];wanted=set(data['queries']['all']);meta={c:m for c,m in data['metadata'].items() if c in wanted}
    caps={i:capabilities_plus(rs,meta) for i,rs in rows['fresh'].items()};ordinary={m['base']:m for m in meta.values() if m['family'] in ('ordinary_perfect','ordinary_random')}
    target={b for b,m in ordinary.items() if len(m['path'])-1>=8};long16={b for b,m in ordinary.items() if len(m['path'])-1>=16}
    target_cases={c for c,m in meta.items() if m.get('base') in target};protected=[i['id'] for i in pool['items'] if 'protected' in i['roles']]
    unions={label:{k:set().union(*(caps[i][k] for i in ids)) for k in ('ordinary_bases','success')} for label,ids in [('protected',protected),('historical',pool['historical_references'])]}
    diagnostics={}
    for c in pool['conditions']:
        i=c['id'];a=caps[i];p=caps[c['parent']] if c['parent'] else None
        new=(a['ordinary_bases']&target)-unions['historical']['ordinary_bases']
        diagnostics[i]=dict(cohort=c['cohort'],ordinary8=len(a['ordinary_bases']&target),ordinary16=len(a['ordinary_bases']&long16),
             new_ordinary8_beyond_protected=len((a['ordinary_bases']&target)-unions['protected']['ordinary_bases']),
             new_ordinary8_beyond_historical=len(new),new_ordinary8_keys=sorted(new),
             new_individual8_beyond_protected=len((a['success']&target_cases)-unions['protected']['success']),
             new_individual8_beyond_historical=len((a['success']&target_cases)-unions['historical']['success']),
             new_individual8_keys=sorted((a['success']&target_cases)-unions['historical']['success']),
             versus_actual_parent8=None if p is None else dict(gained=len((a['ordinary_bases']-p['ordinary_bases'])&target),lost=len((p['ordinary_bases']-a['ordinary_bases'])&target),retained=len(a['ordinary_bases']&p['ordinary_bases']&target)),
             correct_no_path=len(a['correct_no_path']),false_no_path=len(a['false']),
             correct_bases_by_family_and_group=dict(Counter(ordinary[b]['family']+'/'+ordinary[b]['panel_group'] for b in a['ordinary_bases'])))
    all_noncontrol_new={i:sorted((c['ordinary_bases']&target)-unions['historical']['ordinary_bases']) for i,c in caps.items() if i not in pool['control_ids']}
    offspring=[]
    for relation in pool['offspring_relations']:
        i=relation['child'];p=relation['parent'];a=caps[i];b=caps[p]
        offspring.append(dict(**relation,novel8_beyond_historical=all_noncontrol_new[i],
           novel8_beyond_parent_and_historical=sorted(set(all_noncontrol_new[i])-b['ordinary_bases']),
           ordinary8_gained_vs_parent=len((a['ordinary_bases']-b['ordinary_bases'])&target),ordinary8_lost_vs_parent=len((b['ordinary_bases']-a['ordinary_bases'])&target),
           no_path_gained=len(a['correct_no_path']-b['correct_no_path']),no_path_lost=len(b['correct_no_path']-a['correct_no_path']),false_no_path=len(a['false'])))
    writej(OUT/'saved_diagnostics.json',dict(scope='Saved audited responses only. Supplementary comparisons do not replace the frozen28-identity primary.',
        ordinary_base_denominators=dict(total=len(ordinary),target8plus=len(target),target16plus=len(long16),targeted=224,standard=256),
        conditions=diagnostics,offspring=offspring,
        all_noncontrol_novel8={i:bs for i,bs in all_noncontrol_new.items() if bs},
        reference_portfolio_coverage={label:dict(ordinary8=len(c['ordinary_bases']&target),ordinary16=len(c['ordinary_bases']&long16)) for label,c in unions.items()},
        physical_models=len(models['fresh']),queries=len(wanted),postprocessing_wall_seconds=time.monotonic()-start,new_inference_calls=0,new_cases=0))
    print(json.dumps(dict(denominators=dict(total=len(ordinary),eight=len(target),sixteen=len(long16)),noncontrol_novel8=len([v for v in all_noncontrol_new.values() if v]),physical_models=len(models['fresh'])),indent=2))


if __name__=='__main__':
    try:main()
    except BaseException:
        import traceback
        with (OUT/f'saved_diagnostics_failure_{time.time_ns()}.json').open('x') as f:json.dump(dict(traceback=traceback.format_exc()),f,indent=2)
        raise
