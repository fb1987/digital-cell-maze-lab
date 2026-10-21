"""Conservative static dependency cones for M1; no new inference or causal claim."""
import sys,json
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.modular_genome import Genome,REFS
from maze_evolution.regulatory import NAMES
from maze_evolution.modular_pilot import OUT,readz,writej


def describe(value):
 g=Genome.from_dict(value);modules=[]
 for m,block in enumerate(g.blocks):
  seen=set();channels=set();flags=set();pending=[len(block)-1]
  while pending:
   i=pending.pop()
   if i in seen:continue
   seen.add(i);gene=block[i];row=gene.row()
   refs=[row[k] for k in REFS[gene.op]]+([gene.gate] if gene.gate!=64 else [])
   for r in refs:
    if r>=12:pending.append(r-12)
    elif r<8:channels.add(g.ports[m][r])
    else:flags.add(r)
   if gene.op in (4,5,6,7,14,15,17):channels.add(g.ports[m][gene.a])
  modules.append(dict(channel=m,total_nodes=len(block),potential_output_nodes=len(seen),node_indices=sorted(seen),reads_channels=sorted(channels),reads_flags=sorted(flags),ops=dict(Counter(NAMES[block[i].op] for i in seen))))
 channels={2,7};old=set()
 while channels!=old:
  old=channels.copy();channels.update(c for m in old for c in modules[m]['reads_channels'])
 return dict(total_instructions=g.instructions,blocks=modules,output_and_halt_recurrent_channels=sorted(channels),potential_nodes_in_output_and_halt=sum(modules[m]['potential_output_nodes'] for m in channels),limitation='Static backward dependence includes gates and all alternatives. It can overestimate causal activity; no branch feasibility or intervention is inferred.')


if __name__=='__main__':
 c=readz(OUT/'choices.json.gz');result={}
 for i,v in c['items'].items():
  if c['representations'][i]=='modular':result[i]=describe(v['genome'])
 writej(OUT/'modular_dependencies.json',dict(label='Post-hoc static analysis; zero candidate calls',items=result))
