"""Post-confirmation descriptive extraction from saved evidence; zero inference."""
import json,sqlite3,sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.wave_continuation import ROOT,OUT,RUN,readz,writej,check
from maze_evolution.deep_campaign_store import unpacked
from maze_evolution.deep_confirmation_analysis import capabilities

def main():
    check();assert not (OUT/'completion.json').exists()
    s=json.loads((OUT/'summary.json').read_text());data=readz(OUT/'confirmation.json.gz');meta=data['metadata']
    rows=readz(OUT/'final_responses.json.gz')['rows'];choices=readz(OUT/'choices.json.gz');ancestry=readz(OUT/'ancestry.json.gz')
    caps={i:capabilities(rs,meta) for i,rs in rows.items()};union=set().union(*(caps[i]['ordinary_bases'] for i in s['protected_identities']))
    ordinary_meta={m['base']:m for m in meta.values() if m['family'] in ('ordinary_perfect','ordinary_random')}
    details=[]
    for c in s['conditions']:
        i=c['child'];item=choices['items'][i];chain=[];cursor=i
        while ancestry[cursor]['item']['parent']:
            event=ancestry[cursor];chain.append(event);cursor=event['item']['parent']
        assert cursor==c['root'] and len(chain)==c['mutations']
        cs=caps[i];rs=caps[c['root']];parent=caps[c['parent']] if c['parent'] else None
        bases=[]
        for b in sorted(cs['ordinary_bases']):
            m=ordinary_meta[b];bases.append(dict(base=b,family=m['family'],size=m['size'],edges=len(m['path'])-1,
                new_to_root=b not in rs['ordinary_bases'],new_to_protected_union=b not in union))
        details.append(dict(condition=c['condition'],rank=c['rank'],id=i,root=c['root'],parent=c['parent'],origin=item['origin'],
            mutation_births=len(chain),mutation_opportunities=sum(len(e['events']) for e in chain),
            two_opportunity_births=sum(len(e['events'])==2 for e in chain),ordinary_successes=bases,
            new_ordinary_beyond_root_and_protected=len(cs['ordinary_bases']-rs['ordinary_bases']-union),
            parent_pairs=len(parent['pairs']) if parent else None,parent_ordinary=len(parent['ordinary_bases']) if parent else None,
            root_correct_no_path=sum(r['no_path'] for r in rows[c['root']]),
            retained_root_pairs=len(cs['pairs']&rs['pairs']),retained_root_ordinary=len(cs['ordinary_bases']&rs['ordinary_bases'])))
    # Logical alias evaluations versus physical shared-model receipts are separate.
    db=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True);counts={kind:[0]*6 for kind in ('train','assessment')}
    for kind,blob in db.execute('select stages.kind,tasks.spec from tasks join stages on tasks.stage=stages.n where stages.complete=1'):
        for e in unpacked(blob):
            for k,i in e['aliases']:counts[kind][k]+=len(e['queries'])
    db.close()
    queried={r['case'] for r in next(iter(rows.values()))};base_meta={meta[c]['base']:meta[c] for c in queried if meta[c]['family'] in ('ordinary_perfect','ordinary_random')}
    strata=Counter('short' if len(m['path'])-1<8 else 'medium' if len(m['path'])-1<16 else 'long' for m in base_meta.values())
    writej(OUT/'completion_details.json',dict(source='Post-confirmation saved-data extraction; no new inference/cases or reselection',
        conditions=details,logical_alias_evaluations=counts,condition_order=[x['name'] for x in readz(OUT/'founders.json.gz')],
        ordinary_bases=256,ordinary_length_totals=dict(strata),physical_final_models=len(readz(OUT/'final_responses.json.gz')['models']),
        nominee_aliases=12,distinct_nominees=len({c['child'] for c in s['conditions']}),selected_ancestry_records=len(ancestry),
        birth_counts=dict(total=866*6*52,random_immigrants=866*6*7,mutated=866*6*45,mutation_opportunities=866*3*(45+67))))
    print('Saved descriptive final details.')
    for d in details:
        if d['condition']=='modular/0/mixed' and d['rank']==0:
            print('Mixed0 ancestry:',d['mutation_births'],d['mutation_opportunities'],d['two_opportunity_births'])
            print('Mixed0 successful lengths:',dict(Counter(b['edges'] for b in d['ordinary_successes'])))
            print('Novel long:',[(b['family'],b['size'],b['edges']) for b in d['ordinary_successes'] if b['edges']>=8])
    print('Length totals',dict(strata),'logical evaluations',counts)

if __name__=='__main__':main()
