"""Supplement M5 reports from saved records only; no selection or inference."""
import sys,json,sqlite3
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.holding_assay import OUT,RUN,check,readz,writej,load,feature,capabilities
from maze_evolution.deep_campaign_store import unpacked,packed,hashed


def main():
    check();assert not (OUT/'saved_diagnostics.json').exists()
    choices=readz(OUT/'choices.json.gz');pool=readz(OUT/'pool.json.gz');fs=choices['features'];signatures={}
    c=sqlite3.connect(f'file:{RUN}/screen/campaign.sqlite?mode=ro',uri=True)
    for (blob,) in c.execute('select result from tasks order by n'):
        for e in unpacked(blob)['entries']:
            h=hashed(packed([(r['mask'],r['status'],r['steps']) for r in e['rows']]))
            for i in e['aliases']:signatures[i]=h
    c.close()
    groups={};matched={}
    for k in range(2):
        for arm in ('hold','zero','standard'):
            ii=[i for i in pool['items'] if i.get('anchor')==k and i['arm']==arm]
            groups[f'a{k}/{arm}']=dict(proposals=len(ii),logical_queries=len(ii)*392,distinct_physical_genotypes=len({hashed(packed(i['model'])) for i in ii}),
                same_terminal_as_anchor=sum(signatures[i['id']]==signatures[f'anchor/{k}'] for i in ii),retained=sum(fs[i['id']]['retained'] for i in ii),
                passing_screen_gate=sum(fs[i['id']]['acquisition_gate'] for i in ii),max_new_upstream=max(fs[i['id']]['new_upstream_pairs'] for i in ii),
                passing_distinct_genotypes=len({hashed(packed(i['model'])) for i in ii if fs[i['id']]['acquisition_gate']}),
                passing_terminal_patterns=len({signatures[i['id']] for i in ii if fs[i['id']]['acquisition_gate']}),
                by_depth={str(d):dict(proposals=sum(i['depth']==d for i in ii),retained=sum(fs[i['id']]['retained'] for i in ii if i['depth']==d),passing=sum(fs[i['id']]['acquisition_gate'] for i in ii if i['depth']==d)) for d in (1,2)})
        pairs=[(f'a{k}/hold/{n:04}',f'a{k}/zero/{n:04}') for n in range(pool['count'])]
        matched[f'a{k}']=dict(pairs=len(pairs),terminal_equal=sum(signatures[h]==signatures[z] for h,z in pairs),
            hold_only_retained=sum(fs[h]['retained'] and not fs[z]['retained'] for h,z in pairs),zero_only_retained=sum(fs[z]['retained'] and not fs[h]['retained'] for h,z in pairs),
            both_retained=sum(fs[h]['retained'] and fs[z]['retained'] for h,z in pairs),
            hold_more_upstream=sum(fs[h]['new_upstream_pairs']>fs[z]['new_upstream_pairs'] for h,z in pairs),zero_more_upstream=sum(fs[z]['new_upstream_pairs']>fs[h]['new_upstream_pairs'] for h,z in pairs))
    data,rows,models=load(True);meta=data['metadata'];caps={i:capabilities(rs,meta) for i,rs in rows.items()}
    ordinary={m['base']:m for cid,m in meta.items() if cid in set(data['queries']['all']) and m['family'] in ('ordinary_perfect','ordinary_random')}
    assert len(ordinary)==256
    length={};comparisons={}
    for i,cap in caps.items():
        gg=defaultdict(set)
        for b,m in ordinary.items():gg[f"{m['family']}/{m['size']}/{m['length_bin']}"].add(b)
        length[i]={s:dict(bases=len(bs),correct=len(bs&cap['ordinary_bases'])) for s,bs in gg.items()}
        assert sum(v['bases'] for v in length[i].values())==256
        assert sum(v['correct'] for v in length[i].values())==cap['summary']['ordinary_bases_both_poses']
    for item in choices['items']:
        k=item.get('anchor');i=item['id']
        if k is not None:
            f=feature(rows[i],meta,caps[f'anchor/{k}']);f['events']=item['events'];f['depth']=item['depth']
            if item.get('arm') in ('hold','zero'):
                twin=i.replace('/hold/','/zero/') if item['arm']=='hold' else i.replace('/zero/','/hold/')
                if twin in rows:
                    f['opposite_fallback']=twin
                    f['terminal_equal_twin']=all((a['mask'],a['status'],a['steps'])==(b['mask'],b['status'],b['steps']) for a,b in zip(rows[i],rows[twin]))
            comparisons[i]=f
    writej(OUT/'saved_diagnostics.json',dict(label='Retrospective saved-response summaries; zero new evaluations; not new nominations',screen_groups=groups,paired_screen=matched,final_all_mutant_comparisons=comparisons,
        limitations=['Repeated proposals and exact genotypes correlate; no binomial independence or long-run policy estimate.','Terminal equality is on these inputs, not global semantic equivalence.']))
    writej(OUT/'ordinary_length_strata.json',length)
    print('Saved M5 diagnostics; zero new calls.')

if __name__=='__main__':main()
