"""Post-hoc static data-flow checks and descriptive saved-result extraction.
No reaction calls. These checks motivate later interventions; not a new assay.
"""
from pathlib import Path
import sys,json
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.lineage_mapping_data import OUT,read_compressed
from maze_evolution.exposure_genome import Individual

def reads(g):
    vals=[] if g.op==1 else [g.a]
    if g.op in (2,3,8,9,10,12,16):vals.append(g.b)
    if g.op==12:vals.append(g.c)
    if g.gate!=64:vals.append(g.gate)
    return vals

def main():
    p=read_compressed(OUT/'panel.json.gz');metrics=read_compressed(OUT/'metrics.json.gz')
    gs=Individual.load(p['items']['d02']).genome.program.genes
    assert gs[103].row()==[15,32,3,0,0,3,64]
    assert not any(g.op!=13 and g.dst==44 for g in gs[:108])
    assert [(i,g.row()) for i,g in enumerate(gs) if g.op==13 and g.dst==4]==[(20,[13,4,33,0,0,0,52]),(108,[13,4,44,0,0,0,64])]
    assert [(i,g.row()) for i,g in enumerate(gs) if i>103 and 32 in reads(g)]==[(246,[13,3,32,0,0,0,64])]
    assert gs[249].row()==[13,3,2,0,0,0,64] and not any(g.op==13 and g.dst==3 for g in gs[250:])
    assert [(i,g.row()) for i,g in enumerate(gs) if 103<i<140 and 44 in reads(g)]==[(108,[13,4,44,0,0,0,64])]
    summaries={}
    for name,pid in p['aliases'].items():
        s=metrics[pid+'|normal'];good=[d for d in s['details'].values() if d['complete'] and d['prefix']>0]
        groups=Counter((d['template'],d['prefix'],d['source_shape'],d['graph'],d['second']) for d in good)
        summaries[name]=dict(positive_pairs=len(good),positive_by_graph=dict(Counter(d['graph'] for d in good)),positive_by_prefix=dict(Counter(str(d['prefix'])+'/'+d['source_shape'] for d in good)),positive_by_context=dict(Counter(d['template'] for d in good)),positive_full_eight_pose_groups=sum(v==8 for v in groups.values()),max_paired_route_edges=max((max(d['route_lengths']) for d in good),default=0),legal_nonshortest=sum(f['valid']-f['optimal'] for f in s['families'].values()),false_reachable_no_path=sum(f['false_no_path'] for f in s['families'].values()))
    (OUT/'static_interpretation.json').write_text(json.dumps(dict(candidate_calls=0,post_hoc=True,
        program='d02',static_checks_passed=True,
        facts=['Scratch registers reset to zero per site/tick in the frozen runtime.',
               'No write to scratch44 precedes unconditional STORE channel4 from scratch44 at index108 after edit2.',
               'Index108 is the final channel4 store. Channel4 therefore stays zero after complete d02 ticks.',
               'The new scratch32 value has only one later reader: STORE channel3 at246, overwritten unconditionally from old output channel2 at249.',
               'Between103 and the next write to44 at140, the only reader of44 is STORE channel4 at108.'],
        prediction='Edit2 removes the old channel3-neighbor signal from channel4. A future intervention restoring that channel4 signal can test the behavioral explanation. This is static inspection, not a new causal ablation or complete algorithm derivation.',summaries=summaries),indent=2)+'\n')

if __name__=='__main__':main()
