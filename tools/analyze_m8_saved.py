"""Post-audit M8 summary of fixed saved interventions, no inference or selection."""
import sys,json
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.repair_mechanism import ROOT,OUT,check,readz,writej
from maze_evolution.modular_genome import Genome
check();assert json.loads((OUT/'audit.json').read_text())['status']=='PASS'
assert not (OUT/'saved_diagnostics.json').exists()
s=json.loads((OUT/'summary.json').read_text());panel=readz(OUT/'panel.json.gz');results={}
rows=readz(OUT/'responses.json.gz')['rows']
transfers={}
for k in (0,1):
 a=rows[f'a{k}/child'];b=rows[f'a{k}/parent_child_writer'];assert [x['case'] for x in a]==[x['case'] for x in b]
 transfers[f'a{k}']=dict(different_fields={f:sum(x[f]!=y[f] for x,y in zip(a,b)) for f in ('mask','status','steps')},
  differences=[dict(case=x['case'],child={f:x[f] for f in ('status','steps')},transfer={f:y[f] for f in ('status','steps')}) for x,y in zip(a,b) if any(x[f]!=y[f] for f in ('mask','status','steps'))])
for k in (0,1):
 prefix=f'a{k}/';child=s['models'][prefix+'child'];parent=s['models'][prefix+'parent'];root=s['models'][prefix+'root']
 models={i:r for i,r in s['models'].items() if i.startswith(prefix)}
 equal_child=[i for i,r in models.items() if r['terminal_behavior_sha256']==child['terminal_behavior_sha256']]
 equal_parent=[i for i,r in models.items() if r['terminal_behavior_sha256']==parent['terminal_behavior_sha256']]
 masks=[int(i.rsplit('/',1)[1]) for i in equal_child if '/restore/' in i]
 def compact(i):
  r=s['models'][i];m=r['metrics'];return dict(id=i,instructions=Genome.from_dict(panel['items'][i]['genome']).instructions,
    work=m['work'],pairs=m['paired'],corridors=m['by_domain']['corridor']['optimal'],ordinary=m['ordinary_bases_both_poses'],correct_no_path=m['correct_no_path'],false_no_path=m['false_no_path'],target_pairs=r['target_pairs'],
    beyond_protected=r['beyond_protected'],root_retention=r['diagnostic_screen']['root_retention'],
    new_corridors_vs_child=r['new_corridors_vs_child'],lost_corridors_vs_child=r['lost_corridors_vs_child'],
    versus_child=r['versus_child'],versus_root=r['versus_root'],equal_child=i in equal_child,equal_parent=i in equal_parent)
 ids=[prefix+x for x in ('child','root','parent','parent_child_writer')]
 ids += [prefix+f'{base}/{ch}' for base in ('zero','parent_zero') for ch in range(8)]
 if k==0:ids+=['a0/c6_only_channel3','a0/c6_only_channel4']
 results[prefix]=dict(compact=[compact(i) for i in ids],terminal_equal_child=equal_child,terminal_equal_parent=equal_parent,
  child_equal_restoration_masks=masks,child_blocks_required_among_exact_behavior_restorations=[b for b in range(8) if masks and all(not mask>>b&1 for mask in masks)],
  max_target_pairs_any_fixed_variant=max(r['target_pairs'] for r in models.values()),
  qualifying_upstream_variants=[i for i in s['diagnostic_upstream_hits'] if i.startswith(prefix)])
writej(OUT/'saved_diagnostics.json',dict(scope='Saved fixed-panel descriptive comparisons only; no post-hoc variant selection, evaluation or tracing.',lineages=results,
 aliases=len(panel['items']),kind_counts=dict(Counter(v['kind'] for v in panel['items'].values())),primary_repair_replication=s['primary_repair_replication'],writer_transfer_comparisons=transfers))
print('Saved M8 diagnostics; primary:',s['primary_repair_replication'],'diagnostic upstream hits:',len(s['diagnostic_upstream_hits']))
