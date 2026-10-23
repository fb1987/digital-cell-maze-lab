"""Posthoc single-input versus complete-pair distinction; no new inference."""
import json,sys
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.integration_accessibility import OUT,check,readz,load,capabilities,FIELDS,writej


def main():
    check();assert not (OUT/'structured_gain_analysis.json').exists()
    pool=readz(OUT/'pool.json.gz');choices=readz(OUT/'choices.json.gz');output={}
    for name in ('development','final'):
        data,rows,_,_,_=load(name);meta,caps=capabilities(data,rows)
        old={k:set().union(*(caps[i][k] for i in pool['historical_references'])) for k in (*FIELDS,'success','false')}
        ids=[c['id'] for c in pool['conditions'] if c['id'] in rows];details={};groups=defaultdict(list)
        for cid,m in meta.items():
            if m['family']=='paired':groups[(m['base'],m['pose'])].append(cid)
        for i in ids:
            c=caps[i];new=c['success']-old['success'];newpairs=c['pairs']-old['pairs'];newcorr=c['corridors']-old['corridors']
            if not (new or newpairs or newcorr):continue
            records=[];lookup={r['case']:r for r in rows[i]}
            for cid in sorted(new):
                m=meta[cid];partners=[p for p in groups.get((m['base'],m['pose']),[]) if p!=cid]
                records.append(dict(case=cid,family=m['family'],graph=m.get('graph'),prefix=m.get('prefix'),edges=len(m['path'])-1,
                    side=m.get('side'),pose=m['pose'],partners=[dict(case=p,optimal=lookup[p]['optimal'],failure=lookup[p]['failure'],status=lookup[p]['status']) for p in partners]))
            details[i]=dict(new_individual_inputs=records,new_complete_pairs=sorted(newpairs),new_corridor_inputs=sorted(newcorr))
        output[name]=dict(details=details,models_with_new_complete_pairs=sum(bool(d['new_complete_pairs']) for d in details.values()),
            models_with_new_corridors=sum(bool(d['new_corridor_inputs']) for d in details.values()),
            new_individual_inputs=sum(len(d['new_individual_inputs']) for d in details.values()))
    writej(OUT/'structured_gain_analysis.json',dict(status='PASS',scope='Posthoc saved response analysis; does not alter primary or nominees.',panels=output,
        limitation='A new single-sided fork response is not a complete paired discrimination or ordinary maze solution.'))


if __name__=='__main__':main()
