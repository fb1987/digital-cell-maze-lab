"""Read-only M18 interpretation from frozen results; no inference or selection."""
import sys,json,sqlite3,collections,statistics
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.connected_copy_assay import ROOT,OUT,RUN,check,readz,writej,load
from maze_evolution.deep_campaign_store import unpacked,packed,hashed
from maze_evolution.connected_genome import Genome


def main():
    check();assert not (OUT/'interpretation.json').exists()
    assert json.loads((RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
    s=json.loads((OUT/'summary.json').read_text());panel=readz(OUT/'pool.json.gz')['items'];items={i['id']:i for i in panel}
    traces=readz(OUT/'traces.json.gz');data,rows,physical=load(True)
    coupled=collections.defaultdict(set);alltr=collections.defaultdict(list)
    for r in traces['comparisons']:
        alltr[r['identity']].append(r)
        if r.get('zero_changes_legacy_common_tick'):coupled[r['identity']].add(r['case'])
    groups={}
    for arm,g in s['copy_groups'].items():
        ids=[i['id'] for i in panel if i['kind']=='copy' and i['arm']==arm]
        zero_ids=[i+'/zero_writer' for i in ids]
        work=[s['models'][i]['work']/s['models'][i]['anchor_work'] for i in ids]
        groups[arm]=dict(aliases=len(ids),distinct_genomes=len({hashed(packed(items[i]['model'])) for i in ids}),
            bounded_neutral=len(g['bounded_neutral']),retain_all_correct=len(g['preserve_all_correct']),
            any_correct_loss=len(g['any_correct_loss']),any_correct_gain=sum(s['models'][i]['correct_gains']>0 for i in ids),
            any_mask_difference=sum(s['models'][i]['differences']['mask']>0 for i in ids),
            any_status_difference=sum(s['models'][i]['differences']['status']>0 for i in ids),
            any_step_difference=sum(s['models'][i]['differences']['steps']>0 for i in ids),
            trace_aliases_with_zero_coupling=sum(bool(coupled[i]) for i in zero_ids),
            final_aliases_with_zero_mask_effect=sum(s['models'][i]['versus_pure']['mask']>0 for i in zero_ids),
            bounded_neutral_AND_trace_coupling=sum(s['models'][i]['bounded_response_neutral'] and bool(coupled[i+'/zero_writer']) for i in ids),
            work_ratio_min=min(work),work_ratio_median=statistics.median(work),work_ratio_max=max(work),
            correct_loss_range=[min(s['models'][i]['correct_losses'] for i in ids),max(s['models'][i]['correct_losses'] for i in ids)],
            correct_gain_range=[min(s['models'][i]['correct_gains'] for i in ids),max(s['models'][i]['correct_gains'] for i in ids)])
    contrasts=[]
    for i in panel:
        if i['kind']!='copy' or not i['seeded']:continue
        z=i['id'].replace('/seeded_','/zero_');assert z in items
        a=rows[i['id']];b=rows[z]
        contrasts.append(dict(seeded=i['id'],zero=z,donor_initially_nonzero=i['donor'] in (0,1),
            differences={k:sum(x[k]!=y[k] for x,y in zip(a,b)) for k in ('mask','status','steps')},
            seeded_correct_zero_incorrect=sum((x['optimal'] or x['no_path']) and not(y['optimal'] or y['no_path']) for x,y in zip(a,b)),
            zero_correct_seeded_incorrect=sum((y['optimal'] or y['no_path']) and not(x['optimal'] or x['no_path']) for x,y in zip(a,b))))
    detail={};paired_connection=[]
    for i in panel:
        if i['kind']!='copy' or not i['seeded']:continue
        a=rows['anchor/'+i['anchor']];b=rows[i['id']]
        changes=collections.Counter((x['status'],y['status']) for x,y in zip(a,b) if any(x[k]!=y[k] for k in ('mask','status','steps')))
        losses=collections.Counter((x['status'],y['status']) for x,y in zip(a,b) if (x['optimal'] or x['no_path']) and not(y['optimal'] or y['no_path']))
        detail[i['id']]=dict(changed_status_pairs=[dict(anchor=k[0],copy=k[1],inputs=v) for k,v in sorted(changes.items())],
            lost_correct_status_pairs=[dict(anchor=k[0],copy=k[1],inputs=v) for k,v in sorted(losses.items())],
            min_memory_delta=min(y['array_bytes']-x['array_bytes'] for x,y in zip(a,b)),
            max_memory_delta=max(y['array_bytes']-x['array_bytes'] for x,y in zip(a,b)))
        if i['connected']:
            other=i['id'].replace('/seeded_connected/','/seeded_disconnected/')
            paired_connection.append(dict(connected=i['id'],disconnected=other,all_reaction_fields_equal=rows[i['id']]==rows[other]))
    costs={}
    for phase in ('screen','final'):
        con=sqlite3.connect(f'file:{RUN/phase}/campaign.sqlite?mode=ro',uri=True);buckets={}
        lookup={i['id']:i for i in readz(OUT/'choices.json.gz')['items']}
        for result, in con.execute('select result from tasks order by n'):
            for e in unpacked(result)['entries']:
                # Group by ALL alias labels, so these buckets partition physical work.
                labels=sorted({lookup[i].get('arm',lookup[i]['kind'])+'/'+lookup[i]['kind'] for i in e['aliases']})
                key='|'.join(labels);b=buckets.setdefault(key,dict(physical_models=0,calls=0,work=0,candidate_seconds=0.))
                b['physical_models']+=1
                for k in ('calls','work','candidate_seconds'):b[k]+=e[k]
        con.close();session=json.loads((OUT/f'{phase}_session.json').read_text())
        assert sum(v['calls'] for v in buckets.values())==session['usage']['calls']
        assert sum(v['work'] for v in buckets.values())==session['usage']['work']
        costs[phase]=buckets
    writej(OUT/'physical_cost_buckets.json',costs)
    for i in panel:
        if i['kind']=='copy' and i['seeded']:
            assert all(r['legacy_state_matches'] and r['copy_equals_donor_all_recorded_states'] for r in alltr[i['id']])
    result=dict(groups=groups,initialization_contrasts=contrasts,initialized_response_details=detail,paired_initialized_connection=paired_connection,
        trace_cases=len(traces['selected_cases']),physical_trace_models=len(traces['traces'])//len(traces['selected_cases']),
        pure_initialized_trace_comparisons=sum(len(alltr[i['id']]) for i in panel if i['kind']=='copy' and i['seeded']),
        all_initialized_pure_common_tick_and_copy_equal=True,
        coupled_interventions={i:sorted(c) for i,c in sorted(coupled.items())},
        coupled_by_donor={str(d):sum(bool(coupled[i['id']]) for i in panel if i['kind']=='intervention' and i['seeded'] and i['connected'] and i['donor']==d) for d in range(8)},
        instruction_range=[min(Genome.from_dict(i['model']['genome']).instructions for i in panel),max(Genome.from_dict(i['model']['genome']).instructions for i in panel)],
        designed_intervention_strict_joint_passes=[i for i,v in s['models'].items() if v['skill_metrics']['joint_restoration_pass']],
        limitations=['Post hoc summaries of prespecified saved results; no inference or new cases.',
            'Aliases and two anchors are related; counts are not independent replicates.',
            'No mutation search, no acquired evolutionary skill, no speed benchmark.',
            'Trace non-effect is conditional on sampled cases/stopping, not proof of inertness.'])
    writej(OUT/'interpretation.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('coupled_interventions','initialization_contrasts','initialized_response_details','paired_initialized_connection')},indent=2))

if __name__=='__main__':main()
