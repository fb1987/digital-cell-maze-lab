"""Retrospective summaries of M4 saved responses; zero inference or selection."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from maze_evolution.mechanism_retention import OUT, check, load, readz, writej, writez
from maze_evolution.deep_confirmation_analysis import capabilities
from maze_evolution.wave_continuation_analysis import complex_sets
from maze_evolution.deep_campaign_store import hashed, packed


def main():
    check()
    assert not (OUT/'saved_response_diagnostics.json').exists()
    data, rows, models = load()
    meta = data['metadata']
    caps = {i: capabilities(rs, meta) for i, rs in rows.items()}
    queried=set(data['queries']['all'])
    ordinary = {m['base']:m for cid,m in meta.items() if cid in queried and m['family'] in ('ordinary_perfect','ordinary_random')}
    paired = {(m['base'],m['pose']):m for cid,m in meta.items() if cid in queried and m['family']=='paired'}
    assert len(ordinary)==256 and len(paired)==400
    signature = {i:hashed(packed([(r['case'],r['mask'],r['status'],r['steps']) for r in rs])) for i,rs in rows.items()}
    def comparison(i,j):
        a,b = caps[i],caps[j]
        out = {}
        for key in ('pairs','corridors','ordinary_bases','false','success'):
            out[key] = dict(new=len(a[key]-b[key]),lost=len(b[key]-a[key]),retained=len(a[key]&b[key]),reference=len(b[key]))
        new = a['pairs']-b['pairs']
        out['new_pair_by_graph_prefix'] = dict(Counter(f"{paired[p]['graph']}/{paired[p]['prefix']}" for p in new))
        out['new_pair_contexts'] = len({paired[p]['template'] for p in new})
        out['new_ordinary_lengths'] = sorted(len(ordinary[p]['path'])-1 for p in a['ordinary_bases']-b['ordinary_bases'])
        out['identical_terminal_output_status_steps'] = signature[i]==signature[j]
        return out
    originals = {}
    for k in (0,1):
        for role in ('child','root','parent'):
            i=f'a{k}/{role}';cap=caps[i]
            originals[i]=dict(ordinary_successes=[dict(base=b,family=ordinary[b]['family'],size=ordinary[b]['size'],edges=len(ordinary[b]['path'])-1) for b in sorted(cap['ordinary_bases'])],
                versus_root=comparison(i,f'a{k}/root'),versus_parent=comparison(i,f'a{k}/parent'))
    strata = {}
    for i,cap in caps.items():
        groups=defaultdict(set)
        for b,m in ordinary.items():groups[f"{m['family']}/{m['size']}/{m['length_bin']}"].add(b)
        strata[i]={s:dict(bases=len(bs),correct=len(bs&cap['ordinary_bases'])) for s,bs in groups.items()}
    zeros = {f'a{k}/zero/{ch}':comparison(f'a{k}/zero/{ch}',f'a{k}/child') for k in (0,1) for ch in range(8)}
    landscape = {}
    for k in (0,1):
        ids=[i for i in rows if i.startswith(f'a{k}/restore/')]
        ref=caps[f'a{k}/child'];eligible=[]
        for i in ids:
            if all(not ref[key] or len(ref[key]&caps[i][key])/len(ref[key])>=.9 for key in ('pairs','corridors','ordinary_bases')) and not caps[i]['false']:eligible.append(i)
        landscape[f'a{k}']=dict(count=len(ids),identical_child=sum(signature[i]==signature[f'a{k}/child'] for i in ids),
            identical_root=sum(signature[i]==signature[f'a{k}/root'] for i in ids),
            retain_own_child_90_percent_no_false=eligible,
            maximum_pairs=max(len(caps[i]['pairs']) for i in ids),maximum_ordinary=max(len(caps[i]['ordinary_bases']) for i in ids),
            maximum_hard_pairs=max(len(complex_sets(caps[i],meta)['hard_pairs']) for i in ids),
            maximum_long_bases=max(len(complex_sets(caps[i],meta)['long_bases']) for i in ids),
            single_restorations={str(ch):comparison(f'a{k}/restore/{1<<ch:03d}',f'a{k}/child') for ch in range(8)})
    writej(OUT/'saved_response_diagnostics.json',dict(label='Retrospective fixed-panel description only; zero new calls, no nominees',originals=originals,zeros=zeros,restoration_landscape=landscape))
    writej(OUT/'ordinary_length_strata.json',strata)
    if not (OUT/'responses.json.gz').exists():
        writez(OUT/'responses.json.gz',dict(models=[dict(aliases=e['aliases'],rows=rs) for e,rs in models]))
    print('Saved-response diagnostics exported; zero new inference.')


if __name__=='__main__':main()
