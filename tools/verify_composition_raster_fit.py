"""Independent pure-graph verification of the post-hoc numpy raster observer."""
from pathlib import Path
from collections import deque
import gzip,json

OUT=Path(__file__).resolve().parents[1]/'results/composition_study'
def read(path):
    with gzip.open(path,'rt') as f:return json.load(f)


def main():
    fit=json.loads((OUT/'raster_hypothesis_fit.json').read_text())
    meta=read(OUT/'confirmation/metadata.json.gz');predicted={}
    for m in read(OUT/'confirmation/mazes.json.gz'):
        cells=bytes.fromhex(m['cells_hex']);w=m['w'];h=m['h']
        def neighbors(p):
            x,y=p%w,p//w
            return [q for q,ok in ((p-1,x>0),(p+1,x+1<w),(p-w,y>0),(p+w,y+1<h)) if ok and cells[q]]
        distances={m['goal']:0};queue=deque([m['goal']])
        while queue:
            p=queue.popleft()
            for q in neighbors(p):
                if q not in distances:distances[q]=distances[p]+1;queue.append(q)
        if m['start'] not in distances:continue
        mask={p for p,d in distances.items() if d<=distances[m['start']]}
        fixed={m['start'],m['goal']};encoded=[]
        for k in range(7):
            packed=bytearray((len(cells)+7)//8)
            for p in mask:packed[p//8]|=1<<(p%8)
            encoded.append(packed.hex())
            remove={p for p in mask-fixed if sum(q in mask for q in neighbors(p))<=1}
            mask=mask-remove
        predicted[m['case_id']]=encoded
    results={};rows=0
    with gzip.open(OUT/'confirmation/responses.jsonl.gz','rt') as f:
        for line in f:
            e=json.loads(line)
            if e['key'] not in fit['results']:continue
            groups={}
            for r in e['rows']:
                if r['case'] not in predicted:continue
                rows+=1;q=meta[r['case']]
                labels={'all_reachable',q['family'],'ordinary' if q['family'].startswith('ordinary_') else 'structured'}
                if q['family']=='paired':labels.add(f"paired/{q['graph']}/prefix{q['prefix']}")
                for label in labels:
                    s=groups.setdefault(label,dict(inputs=0,mask_matches=[0]*7,emitted_mask_matches=[0]*7));s['inputs']+=1
                    for k,value in enumerate(predicted[r['case']]):
                        s['mask_matches'][k]+=r['mask']==value
                        s['emitted_mask_matches'][k]+=r['mask']==value and r['status']=='emitted'
            results[e['key']]=groups
    assert results==fit['results']
    packet=dict(passed=True,candidate_calls=0,reachable_cases=len(predicted),normal_saved_rows=rows,
                models=len(results),rounds=list(range(7)),implementation='Independent graph BFS, neighbor-set pruning and manual bit packing; no numpy observer code reused')
    (OUT/'raster_hypothesis_verification.json').write_text(json.dumps(packet,indent=2)+'\n')
    print(packet)


if __name__=='__main__':main()
