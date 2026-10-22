"""Posthoc M23 interpretation of audited saved data only; ZERO new inference/cases."""
import json,sqlite3,time
from collections import Counter,defaultdict
from maze_evolution import dormant_evolution as m
from maze_evolution.deep_campaign_store import unpacked

def main():
 m.check();assert not (m.OUT/'interpretation.json').exists()
 assert json.loads((m.RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
 s=json.loads((m.OUT/'summary.json').read_text());d=json.loads((m.OUT/'saved_diagnostics.json').read_text());a=json.loads((m.OUT/'allocation_persistence.json').read_text());audit=json.loads((m.OUT/'search_audit.json').read_text())
 panel=m.readz(m.OUT/'confirmation.json.gz');rows=m.readz(m.OUT/'final_responses.json.gz')['rows'];cases=[]
 for identity,n in d['nominees'].items():
  for cid in n['new_individual_inputs_beyond_archive']:
   meta=panel['metadata'][cid];members=[r for r in rows[identity] if panel['metadata'][r['case']]['base']==meta['base']]
   cases.append(dict(identity=identity,case=cid,family=meta['family'],size=meta['size'],edges=len(meta['path'])-1,pose=meta['pose'],M23_mutation_births=n['M23_mutation_births'],scope='Only individual success beyond the fixed103alias/73genotype comparison archive. Not all historical mutants, and not a new complete two-pose maze success.',two_pose_responses=[dict(case=r['case'],pose=panel['metadata'][r['case']]['pose'],optimal=r['optimal'],status=r['status'],failure=r['failure'],steps=r['steps']) for r in members]))
 group=defaultdict(Counter);survival=defaultdict(Counter)
 for name,v in a['variation_counts'].items():
  arm=name.rsplit('/',1)[1]
  for k,n in v.items():group[arm][k]+=n
  for k,n in a['immediate_birth_survival'].get(name,{}).items():survival[arm][k]+=n
 # Count exact admission-limited no-ops from stored event schemas; never mutate.
 con=sqlite3.connect(f'file:{m.RUN}/campaign.sqlite?mode=ro',uri=True);con.execute('BEGIN');admission=defaultdict(Counter)
 for blob, in con.execute("select decision from stages where kind='train' and complete=1 order by n"):
  for event in unpacked(blob):
   arm=event['name'].rsplit('/',1)[1]
   for birth in event['births']:
    for e in birth['events']:
     if 'activation_index' in e and e['opportunity']==0 and arm!='ordinary':
      admission[arm]['attempts']+=1;admission[arm]['admitted']+=e['kind'] in ('disabled_extension','enabled_extension');admission[arm]['bounded_noop']+=e['kind']=='bounded_noop'
 con.close()
 sessions={k:json.loads((m.OUT/n).read_text()) for k,n in [('search','session.json'),('final','final_session.json')]};wf=json.loads((m.RUN/'workflow_status.json').read_text());launch=json.loads((m.OUT/'launch.json').read_text())
 costs={k:sum(v['usage'][k] for v in sessions.values()) for k in sessions['search']['usage']}
 persistence={arm:dict(extension_descendants=sum(v['extension_descendants'] for name,v in a['final_persistence'].items() if name.endswith('/'+arm)),max_M23_depth=max(v['max_M23_mutation_depth'] for name,v in a['final_persistence'].items() if name.endswith('/'+arm)),max_extension_births_on_chain=max(v['max_extension_births_on_chain'] for name,v in a['final_persistence'].items() if name.endswith('/'+arm)),max_current_wrappers=max(x['recognized_wrappers'] for name,v in a['final_persistence'].items() if name.endswith('/'+arm) for x in v['current_structures'].values())) for arm in ('ordinary','enabled','disabled')}
 result=dict(scope='POSTHOC interpretation of audited saved records; no new inference, mutation, cases, reselection or protocol change.',primary=s['policy_comparison'],acquisition_passes={k:sum(bool(c[k]) for c in s['conditions']) for k in ('upstream_acquisition','long_ordinary_acquisition','combined_transfer')},all27_raw_novel_target_counts_zero=all(c['beyond_root_and_protected_union']['new_upstream_pairs']==0 for c in s['conditions']),all_nominees16plus_zero=all(d['model_details'][i]['length16plus_successes']==0 for i in d['nominees']),ordinary16plus_opportunities=79,novel_individual_cases=cases,mutation_and_operator_counts={k:dict(v) for k,v in group.items()},next_train_survival={k:dict(v) for k,v in survival.items()},extension_admission={k:dict(v) for k,v in admission.items()},final_persistence=persistence,scientific_usage=costs,nominal_queries_per_population=next(iter(audit['logical_query_counts'].values())),nominal_queries_all_populations=sum(sum(v.values()) for v in audit['logical_query_counts'].values()),final_physical_models=sessions['final']['usage']['calls']//1680,confirmation_queries=1680,measured_scientific_session_seconds=sum(v['wall_seconds'] for v in sessions.values()),workflow_calendar_elapsed_seconds=wf['ended_epoch']-launch['started_epoch'],search_timing=json.loads((m.OUT/'search_timing.json').read_text()),conclusion='Disabled birth is operationally safe at admitted capacity; thousands of insertions and subsequent expression edits were generated and some survived/reproduced. This campaign confirms no novel target-pair/long-route/general capability or disabled-arm advantage. A single one-pose6-edge response emerged in an enabled16-birth lineage with losses. It is not a robust new solver; zero raw target novelty means the negative primary is not solely a90%retention-threshold artifact. Larger capacity/depth remains untested here.',recommendation='Proposal ONLY: a small separately registered causal audit of the frozen16-step lineage, comparing branch bypass while keeping material versus the final output-writer port swap and earlier ancestors on already-used cases as development. Establish whether extension/tuning contributed or were neutral passengers. Preserve exact ending populations/RNG for any later sustained continuation. No M24, new inference, evolution, recombination, solver injection or cloud compute launched.')
 m.writej(m.OUT/'interpretation.json',result);print(json.dumps(dict(admission=result['extension_admission'],persistence=persistence,novel_individual_cases=cases,scientific_usage=costs),indent=2))
if __name__=='__main__':main()
