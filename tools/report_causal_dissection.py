"""Saved-data V12V tables and scope summaries. Zero candidate calls."""
from pathlib import Path
import sys,json
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.causal_dissection_data import OUT,read_compressed
from maze_evolution.exposure_genome import Individual

def main():
    p=read_compressed(OUT/'panel.json.gz');m=read_compressed(OUT/'metrics.json.gz');a=read_compressed(OUT/'analysis.json.gz');out=[];scopes={}
    out+=['# V12V saved-result tables','','Synthetic variants are diagnostic probes, not evolutionary discoveries. Poses and graph/prefix variants within a context are correlated.','', '| Model | Kind | Genes | All pairs | Positive pairs | Corridors | Ordinary shortest | Explicit no-path |','|---|---|---:|---:|---:|---:|---:|---:|']
    for name,pid in p['aliases'].items():
        s=m[pid+'|normal'];f=s['families'];gs=Individual.load(p['items'][name]).genome.genes
        ordinary=sum(f[k]['optimal'] for k in ('ordinary_perfect','ordinary_random'));np=sum(f[k]['no_path'] for k in ('disconnected','ordinary_disconnected'));npn=sum(f[k]['inputs'] for k in ('disconnected','ordinary_disconnected'))
        positive=sum(d['prefix']>0 for d in s['details'].values())
        out.append(f"| {name} | {p['kinds'][name]} | {len(gs)} | {s['pairs']}/{s['pair_opportunities']} | {s['positive']}/{positive} | {f['corridor']['optimal']}/{f['corridor']['inputs']} | {ordinary}/384 | {np}/{npn} |")
        good=[d for d in s['details'].values() if d['complete'] and d['prefix']>0];groups=Counter((d['template'],d['prefix'],d['source_shape'],d['graph'],d['second']) for d in good)
        scopes[name]=dict(positive_by_graph=dict(Counter(d['graph'] for d in good)),positive_by_prefix=dict(Counter(str(d['prefix'])+'/'+d['source_shape'] for d in good)),positive_by_context=dict(Counter(d['template'] for d in good)),positive_full_pose_groups=sum(v==8 for v in groups.values()),max_paired_route_edges=max((max(d['route_lengths']) for d in good),default=0),legal_nonshortest=sum(f['valid']-f['optimal'] for f in s['families'].values()),false_no_path=sum(f['false_no_path'] for f in s['families'].values()))
    out+=['','| Contrast (before→after) | Positive pairs gained/lost | All pairs gained/lost | Masks changed | Stops changed |','|---|---:|---:|---:|---:|']
    for name,v in a['comparisons'].items():
        g=sum(s['gained'] for s in v['positive_by_context'].values());l=sum(s['lost'] for s in v['positive_by_context'].values())
        out.append(f"| {name} | +{g}/−{l} | +{len(v['gained'])}/−{len(v['lost'])} | {v['changed_responses']['mask']} | {v['changed_responses']['steps']} |")
    out+=['','| Signal intervention | Predicted native reference | Exact full records | Matching masks/status/ticks |','|---|---|---:|---:|']
    for name,v in a['signal_predictions'].items():
        c=v['counts'];out.append(f"| {name.replace('|',' / ')} | {v['reference']} | {c['full_record_equal']}/{c['inputs']} | {c['behavior_equal']}/{c['inputs']} |")
    out+=['','All exceptions, including counter-only differences, are preserved in analysis.json.gz. No normalization removes work or memory differences from the full-record test.','']
    (OUT/'data_tables.md').write_text('\n'.join(out));(OUT/'descriptive_scopes.json').write_text(json.dumps(dict(candidate_calls=0,post_hoc=True,models=scopes),indent=2)+'\n')

if __name__=='__main__':main()
