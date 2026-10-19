"""Posthoc same-batch parent/child pressure contrasts; no new inference."""
import sys
from pathlib import Path
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.shared_prefix_study import *
from maze_evolution.exposure_selection import evaluate

def main():
    pools=read_compressed(OUT/'pools.json.gz');parents={i['id']:i['parent'] for p in pools.values() for i in p['items']}
    for e in lines(OUT/'reproduction.jsonl.gz'):
        for b in e['births']:parents[b['item']['id']]=b['item']['parent']
    meta=read_compressed(OUT/'train/metadata.json.gz');totals=defaultdict(lambda:dict(comparisons=0,prefix_improves=0,overall_better=0,overall_equal=0,overall_worse=0,loses_zero_pairs=0,loses_corridors=0));examples=[];batch={};batch_key=None
    def flush():
        if not batch or not batch_key[0].endswith('/mixed'):return
        s=totals[batch_key[0]]
        for identity,rows in batch.items():
            parent=parents[identity]
            if parent not in batch:continue
            prior=batch[parent];s['comparisons']+=1
            subset=lambda rs:[r for r in rs if meta[r['case']]['family']=='paired' and meta[r['case']]['prefix']==1]
            a,b=evaluate(subset(rows),meta).fitness,evaluate(subset(prior),meta).fitness
            if a<=b:continue
            s['prefix_improves']+=1;c,d=evaluate(rows,meta).fitness,evaluate(prior,meta).fitness
            direction='overall_better' if c>d else 'overall_worse' if c<d else 'overall_equal';s[direction]+=1
            m,n=summary(rows,meta),summary(prior,meta);s['loses_zero_pairs']+=m['zero']<n['zero'];s['loses_corridors']+=m['corridors']<n['corridors']
            examples.append(dict(condition=batch_key[0],generation=batch_key[1],child=identity,parent=parent,prefix_child=list(a),prefix_parent=list(b),overall_child=list(c),overall_parent=list(d),direction=direction))
    for e in lines(OUT/'search_responses.jsonl.gz'):
        if e['stage']!='train':continue
        key=e['key'],e['generation']
        if key!=batch_key:flush();batch={};batch_key=key
        batch[e['id']]=e['rows']
    flush();write_json(OUT/'pressure_diagnostics.json',dict(candidate_calls=0,posthoc=True,scope='Correlated parent/child co-presence subset; aggregate rank contrast is not lexicase parent probability or an alternative evolved trajectory. Partial-score gains are not solved routes.',totals=dict(totals),examples=examples))
if __name__=='__main__':main()
