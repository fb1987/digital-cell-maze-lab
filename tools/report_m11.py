"""M11 report tables from sealed predictions and audited saved results only."""
import sys,json,sqlite3
from pathlib import Path
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.retention_bank import ROOT,OUT,RUN,check,readz,writej,capabilities_plus,PARENT,GATED,STRATA
from maze_evolution.deep_campaign_store import unpacked
check();assert not (OUT/'report.md').exists();assert not (OUT/'diagnostics.json').exists()
s=json.loads((OUT/'summary.json').read_text());freeze=readz(OUT/'calibration_freeze.json.gz');models=readz(OUT/'pool.json.gz')
p=json.loads((OUT/'preservation.json').read_text());audits={k:json.loads((OUT/f'{k}_audit.json').read_text()) for k in ('calibration','final')}
assert all(a['status']=='PASS' for a in audits.values())
con=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True);coverage=[];stage_costs=[]
for n,blob in con.execute('select n,input from stages where complete=1 order by n'):
 d=unpacked(blob);receipts=[unpacked(b) for b, in con.execute('select result from tasks where stage=? order by n',(n,))]
 stage_costs.append(dict(stage=n,kind=d['kind'],rep=d['generation'],calls=sum(r['calls'] for r in receipts),candidate_seconds=sum(r['candidate_seconds'] for r in receipts),cpu_seconds=sum(r['cpu_seconds'] for r in receipts),work=sum(r['work'] for r in receipts)))
 if d['kind']=='draw':
  choice=freeze['banks'][d['generation']]
  for x,y in zip(d['strata'],choice['strata']):coverage.append(dict(rep=d['generation'],family=x['family'],size=x['size'],lo=x['lo'],hi=x['hi'],raw_draws=x['raw_draws'],length_eligible=len(x['eligible_bases']),reference_successes=y['successful_bases'],selected=len(y['selected_bases'])))
con.close()
data=readz(OUT/'confirmation.json.gz');rows=readz(OUT/'final_responses.json.gz');caps={i:capabilities_plus(rs,data['metadata']) for i,rs in rows.items()};strata={}
for i in [PARENT,*GATED,'m10/reference/shared_child']:
 groups=defaultdict(set)
 for r in rows[i]:
  m=data['metadata'][r['case']]
  if m['family'] in ('ordinary_perfect','ordinary_random'):groups[f"{m['family']}/{m['size']}/{m['length_bin']}"].add(m['base'])
 strata[i]={k:dict(bases=len(bs),correct_both_poses=len(bs&caps[i]['ordinary_bases'])) for k,bs in groups.items()}
for i,ss in strata.items():assert sum(x['bases'] for x in ss.values())==256
writej(OUT/'diagnostics.json',dict(scope='Saved records only; no additional inference or cases',bank_construction_coverage=coverage,stage_costs=stage_costs,reference_ordinary_length_strata=strata,
 physical_models=len(models),aliases=sum(len(m['aliases']) for m in models),no_evolution=True))
lines=['# M11 retention-bank calibration: audited results','',
f"Descriptive bank support: **{s['descriptive_bank_support']}**. Readiness for a separately registered evolutionary protocol: **{s['ready_for_new_protocol']}**. No evolution or new solver discovery occurred in M11.",'',
'This tests whether a fixed scoring panel rejects severe ordinary-skill losses in the preserved M10 diagnostic pool. The exact pool was frozen before new cases:30physical models, including two intact controls; aliases are preserved and counted once per genotype. The parent used to construct every bank is the unchanged M10 quota_parent. Neither gated reference nor any diagnostic candidate chose bank cases.','',
'Each of three current panels and its matched bank scores392inputs/model. The344nonordinary inputs are identical; only24ordinary bases/two poses change. The current distribution follows M10. Bank quotas are4parent-successful bases each for P11/P15/R9/R15short andP11/P15medium. This is explicitly biased reference-conditioned fitness design. It is not an unbiased maze performance benchmark. Shared scoring inputs are physically deduplicated, and all reference-construction calls are additional.','',
'Every bank uses exactly1024raw draws per stratum, selects the first4optimal-both-pose reference successes, and retains all generated/rejected/unqueried layouts. No quota, score, pool or bound was changed after registration. Banks/predictions were published before the independent1680-input corpus; all models were tested, with no nominee reselection.','',
'## Independent classification','',
f"The fixed parent solves {s['truth_parent_ordinary_denominator']}/256 ordinary bases in both poses on fresh confirmation. Of {s['diagnostic_genotypes']} diagnostic genotypes, {s['severe_loss_genotypes']} retain less than90% of those successes. This sample-based severe-loss definition is the registered truth criterion; it is not universal semantic equivalence.",'',
'| Panel | Current parent successes | Bank parent successes | Current severe false accepts | Bank severe false accepts | Current false rejects | Bank false rejects | Nonvacuous | Bank ready |',
'|---|---:|---:|---:|---:|---:|---:|---|---|']
for c,panel in zip(s['comparisons'],freeze['panels']):
 a=c['methods']['current'];b=c['methods']['bank']
 lines.append(f"| {c['rep']} | {panel['current']['parent_ordinary_total']} | {panel['bank']['parent_ordinary_total']} | {a['false_accepts']} | {b['false_accepts']} | {a['false_rejections']} | {b['false_rejections']} | {c['nonvacuous']} | {c['bank_ready']} |")
lines+=['',
'False accept: a genotype with severe loss on confirmation passes complete ordinary retention on the scoring panel. False reject: a genotype retaining all parental ordinary successes on confirmation fails the panel. Counts exclude the two intact controls, deduplicate genotypes, and refer to sampled behavior. Positive checks separately require the fixed parent and both intact controls to pass in both methods.','',
'All three comparisons must meet declared nonvacuity: >=16parental confirmation successes, >=2severe genotypes including shared_child, nonempty current-panel parent denominator,24bank parent successes, and >=8bank ordinary successes for each gated reference. Descriptive support additionally needs strict improvement in2/3panels and positive total reduction. Readiness requires ZEROsevere false accepts in ALLthree banks plus positive checks. This is a descriptive calibration on related genomes, not a significance test or proof about future mutations.','',
'## Gated-reference coverage and ranking','',
'| Panel | Gated partial bank successes | Gated specialist bank successes | Current top-ranked genotype retention on confirmation | Bank top-ranked genotype retention on confirmation |','|---|---:|---:|---:|---:|']
for c,panel in zip(s['comparisons'],freeze['panels']):
 den=panel['bank']['gated_ordinary_denominators'];a=c['methods']['current']['top_rank_confirmation'];b=c['methods']['bank']['top_rank_confirmation']
 lines.append(f"| {c['rep']} | {den[GATED[0]]} | {den[GATED[1]]} | {a['ordinary_retention']:.3f} | {b['ordinary_retention']:.3f} |")
lines+=['','The ranking uses the unchanged M10 integration rank on each panel. All rankings were frozen before confirmation and never selected a different tested pool. Full genotype/alias prediction matrices and integration capability diagnostics are in calibration_freeze.json.gz and summary.json. Existing M10 mutation depth does not imply M11 acquisition; M11 has zero births.','',
'## Construction coverage','',
'| Bank | Family | Size | Edges | Raw bases | Length-eligible | Parent solved both poses | Selected |','|---|---|---:|---|---:|---:|---:|---:|']
for x in coverage:lines.append(f"| {x['rep']} | {x['family']} | {x['size']} | {x['lo']}–{x['hi']} | {x['raw_draws']} | {x['length_eligible']} | {x['reference_successes']} | {x['selected']} |")
lines+=['','There was no16+quota. Long-route capabilities remain sparse; diagnostics.json reports queried-only confirmation length strata for the parent, both gated references and shared_child. Complete ordinary coverage means both sampled poses, not arbitrary transformations or maze families.','',
'## Costs, audit and preservation','',
'| Stage | Kind | Replicate | Physical calls | Candidate seconds | Worker CPU seconds | Work |','|---|---|---:|---:|---:|---:|---:|']
for x in stage_costs:lines.append(f"| {x['stage']} | {x['kind']} | {x['rep']} | {x['calls']:,} | {x['candidate_seconds']:.3f} | {x['cpu_seconds']:.3f} | {x['work']:,} |")
for name in ('calibration','final'):
 x=json.loads((OUT/f'{name}_session.json').read_text());a=audits[name]
 lines+=['',f"{name}: {x['wall_seconds']:.2f}s wall, {x['rss_peak_bytes']/2**30:.3f}GiB sampled process-tree RSS. First audit PASS in {a['wall_seconds']:.2f}s ({a['cpu_seconds']:.2f}CPU seconds): ALL {a['all_native_replays']:,}native outputs and independent grades; corpus/task/selection/metric/hash/chain replay. Audit work is additional."]
lines+=['',
'Both intact controls solve every panel and final input; BFS/A*/bitwave solve all1680final queries (5040calls). The audit uses the production native VM and selection implementation with independent raster grading, not a second interpreter. No uncertain attempts, automatic resumes, budget extensions or scientific source repairs occurred.','',
'Six focused software tests pass, not a full-suite claim. The first attempt had4passes/1failure because the test redirected output but not its temporaryROOT; the test-only fix and failed log are preserved. The discarded success-branch fixture intentionally substitutes an intact control for the parent alias, only in that labeled fixture. It does not alter the scientific pool or create a solver lineage. Its13012calls/5.90candidate seconds and4124generated layouts are excluded from scientific results.','',
f"Registration13d94e2 was pushed before scientific generation. Banks/predictions were pushed at {json.loads((OUT/'bank_freeze.json').read_text())['commit'][:7]} before independent generation. All312registration and356priorM10completion hashes verify. The original SQLite journal and verified API backup match every table and pass integrity checks. Preservation uses {p['storage_bytes']/2**30:.3f}GiB, with {p['disk_free_bytes']/2**30:.2f}GiBfree, inside4GiBtotal/16GiBfree bounds. All {p['whole_layouts']:,}layouts are preserved ({p['initial_layouts']:,}initial, {p['calibration_new_layouts']:,}calibration, {p['final_new_layouts']:,}final). Checksummed gzip chunks and whole_layout_exclusions.json retain the full ledger without exceeding per-file upload limits. Future phases must load every part via retention_bank.load_layouts.",'',
'No new search, model promotion, case generation, temporal inference or phase beyond M11 was performed for this report. The diagnostic pool is informed by past failures and shares ancestry; passing this assay would justify a better-specified experiment, not establish general maze solving.','']
(OUT/'report.md').write_text('\n'.join(lines));print('Wrote M11 diagnostics and report tables; interpretation must be reviewed before seal.')
