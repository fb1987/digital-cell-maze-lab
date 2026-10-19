"""V12K fixed numerical gates and context-level results; no final reselection."""
from collections import defaultdict
import json
from copy import deepcopy
from .foundation_calibration import ROOT,write_json
from .foundation_study import read_compressed
from .routing_transfer import lines
from .robustness_data import OUT,load,BRANCHES
from .robustness_search import annotate
from .robustness_study import metrics


def pair_set(rows,meta,far=False):
    rows=deepcopy(rows);annotate(rows,meta)
    return {(r['base'],r['family'],r['pose']) for r in rows if r['pair_optimal'] and (not far or r['prefix']>=4)}


def success_record(rows,meta):
    m=metrics(rows,meta)
    m['strata']={}
    for shape in ('straight','turning'):
        for prefix in (1,2,4,8):
            for source in ('straight','bent'):
                for family in BRANCHES:
                    subset=[r for r in rows if meta[r['case']]['goal_shape']==shape and meta[r['case']]['prefix']==prefix and meta[r['case']]['source_shape']==source and meta[r['case']]['family']==family]
                    if subset:m['strata'][f'{shape}/p{prefix}/{source}/{family}']=metrics(subset,meta)
    return m


def expansion(a,b,f,meta,rounds):
    x,y,z=(metrics(r,meta) for r in (a,b,f));required=pair_set(b,meta,True)|pair_set(f,meta,True)
    lost=required-pair_set(a,meta,True)
    checks=dict(context_vs_pair=x['contexts']>=y['contexts']+2,pairs_vs_pair=x['pairs']>=y['pairs']+16,
        context_vs_frozen=x['contexts']>=z['contexts']+2,pairs_vs_frozen=x['pairs']>=z['pairs']+16,
        corridor=x['corridor']>=.95*max(y['corridor'],z['corridor']),far_retention=not lost,
        false_no_path=x['false_no_path']<=min(y['false_no_path'],z['false_no_path']),rounds=rounds>=16)
    return dict(passed=all(checks.values()),checks=checks,context=x,pair=y,frozen=z,lost_far_pairs=sorted(lost))


def analyze():
    outputs={};allrows={};metas={}
    for scope in ('diagnostic','final'):
        _,_,meta=load(OUT/scope);metas[scope]=meta;rows=defaultdict(list)
        for rec in lines(OUT/scope/'responses.jsonl.gz'):rows[(rec['model'],rec['mode'])].append(rec['row'])
        allrows[scope]=rows;outputs[scope]={f'{n}|{mode}':success_record(rs,meta) for (n,mode),rs in rows.items()}
    rescue={};meta=metas['diagnostic'];rows=allrows['diagnostic']
    for name in read_compressed(OUT/'panel.json.gz'):
        normal,zero=rows[(name,'normal')],rows[(name,'nonlocal_off')]
        a,b=pair_set(normal,meta),pair_set(zero,meta);gained=b-a;lost=a-b
        net={base:sum(k[0]==base for k in b)-sum(k[0]==base for k in a) for base in {m['base'] for m in meta.values()}}
        positive={base for base,n in net.items() if n>0}
        shapes={m['goal_shape'] for m in meta.values() if m['base'] in positive}
        x,y=(metrics(rs,meta) for rs in (normal,zero))
        newfull=[k for k,v in y['by_group'].items() if v==8 and x['by_group'].get(k,0)<8]
        lost_far=pair_set(normal,meta,True)-pair_set(zero,meta,True)
        passed=len(positive)>=4 and shapes=={'straight','turning'} and len(newfull)>=2 and y['corridor']>=x['corridor'] and not lost_far
        rescue[name]=dict(passed=passed,normal=x,zero=y,gained_pairs=sorted(gained),lost_pairs=sorted(lost),lost_far_pairs=sorted(lost_far),positive_contexts=sorted(positive),new_full_groups=newfull)
    aliases=json.loads((OUT/'final/aliases.json').read_text());summary=json.loads((OUT/'search_summary.json').read_text());gates={};rows=allrows['final'];meta=metas['final']
    def get(key,stage='archives',archive='context'):return rows[(aliases[f'{key}/{stage}/{archive}'],'normal')]
    for origin in ('carry','fresh'):
        for topology in ('local','evolved'):
            cohort=[]
            for rep in range(3):
                a=f'robustness/{origin}/{topology}/context/evolution/{rep}';b=f'robustness/{origin}/{topology}/pair/evolution/{rep}'
                cohort.append(expansion(get(a),get(b),get(a,'frozen'),meta,summary['rounds']))
            gates[f'{origin}/{topology}']=dict(passed=sum(r['passed'] for r in cohort)>=2,replicates=cohort)
    write_json(OUT/'analysis.json',dict(results=outputs,rescue=rescue,gates=gates))
    print(json.dumps(dict(rescue={n:dict(passed=r['passed'],normal=r['normal']['pairs'],zero=r['zero']['pairs'],positive_contexts=len(r['positive_contexts']),lost_far=len(r['lost_far_pairs'])) for n,r in rescue.items()},
        gates={k:dict(passed=v['passed'],replicates=[dict(passed=r['passed'],context=r['context']['pairs'],pair=r['pair']['pairs'],frozen=r['frozen']['pairs']) for r in v['replicates']]) for k,v in gates.items()}),indent=2),flush=True)
