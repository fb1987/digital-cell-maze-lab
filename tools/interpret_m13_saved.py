"""M13 post-audit comparison of saved outputs; no new inference or selection."""
import sys,json,subprocess,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.mutation_scope import ROOT,OUT,check,readz,writej
from maze_evolution.mutation_scope_metrics import capabilities_plus,FIELDS
check();target=OUT/'interpretation_evidence.json';assert not target.exists()
assert all(json.loads((OUT/(n+'_audit.json')).read_text())['status']=='PASS' for n in ('search','final'))
s=json.loads((OUT/'summary.json').read_text());d=readz(OUT/'confirmation.json.gz');rows=readz(OUT/'final_responses.json.gz')['rows'];meta=d['metadata']
caps={i:capabilities_plus(rs,meta) for i,rs in rows.items()};protected=s['protected_identities'];parent='m13/reference/quota_parent'
union={f:set().union(*(caps[i][f] for i in protected)) for f in (*FIELDS,'success')}
parent_rows={r['case']:r for r in rows[parent]};details={}
for c in s['conditions']:
 i=c['child']
 if i in details:continue
 a=caps[i];b=caps[parent];rs=rows[i]
 newinputs=sorted(a['success']-union['success'])
 details[i]=dict(parent_same_success_sets=all(a[f]==b[f] for f in FIELDS),
  parent_mask_status_steps_match=sum(all(r[k]==parent_rows[r['case']][k] for k in ('mask','status','steps')) for r in rs),inputs=len(rs),
  parent_ordinary_kept=len(a['ordinary_bases']&b['ordinary_bases']),parent_ordinary_lost=len(b['ordinary_bases']-a['ordinary_bases']),
  ordinary_gained_over_parent=len(a['ordinary_bases']-b['ordinary_bases']),
  new_individual_inputs_beyond_protected=[dict(case=x,family=meta[x]['family'],base=meta[x]['base'],pose=meta[x]['pose'],edges=len(meta[x]['path'])-1,
   base_correct_both_poses=meta[x]['base'] in a['ordinary_bases'],size=meta[x].get('size'),graph=meta[x].get('graph'),prefix=meta[x].get('prefix')) for x in newinputs])
writej(target,dict(scope='Post-audit saved responses only; descriptive, no new cases/inference/reselection',nominees=details))
reg=json.loads((OUT/'registration.json').read_text())
def sysctl(name):return subprocess.check_output(['sysctl','-n',name],text=True).strip()
writej(OUT/'environment_observation.json',dict(observed_epoch=time.time(),scope='Local host read after completed run',cpu=sysctl('machdep.cpu.brand_string'),
 memory_bytes=int(sysctl('hw.memsize')),logical_cpus=int(sysctl('hw.ncpu')),workers=10,gpu_used=False,
 registered_python=reg['python'],registered_dependencies=reg['dependencies'],registered_platform=reg['platform']))
for i,v in details.items():
 print(i,'same-parent-sets',v['parent_same_success_sets'],'outputmatch',v['parent_mask_status_steps_match'],'new',v['new_individual_inputs_beyond_protected'])
