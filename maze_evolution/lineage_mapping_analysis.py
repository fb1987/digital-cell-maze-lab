"""V12U adjacent historical edit effects, including tradeoffs and mechanisms."""
from collections import defaultdict,Counter
import json
from .lineage_mapping_data import *
from .lineage_mapping_study import CHAIN,MODES
from .routing_mechanism_analysis import summarize
from .routing_transfer import lines,canonical
from .foundation_calibration import write_json

FIELDS=('mask','status','steps','reads','dispatches','exposure_checks')

def comparison(a,b,metrics,native,aliases,meta):
    pa,pb=aliases[a],aliases[b];sa,sb=metrics[pa+'|normal'],metrics[pb+'|normal']
    old={k for k,d in sa['details'].items() if d['complete']};new={k for k,d in sb['details'].items() if d['complete']}
    contexts={}
    for k,d in sb['details'].items():
        s=contexts.setdefault(d['template'],Counter())
        if d['prefix']>0:
            s['before']+=k in old;s['after']+=k in new;s['gained']+=k in new-old;s['lost']+=k in old-new
    changes=Counter();byfamily={};ticks=Counter()
    for cid,ra in native[pa].items():
        rb=native[pb][cid];s=byfamily.setdefault(meta[cid]['family'],Counter())
        for field in FIELDS:changes[field]+=ra[field]!=rb[field]
        s['gained_shortest']+=rb['optimal'] and not ra['optimal'];s['lost_shortest']+=ra['optimal'] and not rb['optimal']
        if ra['steps']!=rb['steps']:ticks[f"{ra['steps']}->{rb['steps']}"]+=1
    return canonical(dict(before=a,after=b,pairs_before=len(old),pairs_after=len(new),positive_before=sa['positive'],positive_after=sb['positive'],gained=sorted(new-old),lost=sorted(old-new),positive_by_context=contexts,changed_responses=changes,by_family=byfamily,tick_transitions=ticks))

def compute(panel,meta,events):
    rows=defaultdict(list);native=defaultdict(dict)
    for e in events:
        if e['scope']=='parity':continue
        rows[e['model']+'|'+e['mode']].append(e['row'])
        if e['scope']=='normal':native[e['model']][e['row']['case']]=e['row']
    metrics={k:summarize(v,meta) for k,v in rows.items()};aliases=panel['aliases']
    contrasts=[(a,b) for a,b in zip(CHAIN,CHAIN[1:])]+[('d00','d12'),('fresh2_root','fresh2'),('broad_root','carry1')]
    comparisons={a+'->'+b:comparison(a,b,metrics,native,aliases,meta) for a,b in contrasts}
    interventions={}
    for name,pid in aliases.items():
        normal=metrics[pid+'|normal']['details'];interventions[name]={}
        for mode in MODES:
            if pid+'|'+mode not in metrics:continue
            ds=metrics[pid+'|'+mode]['details'];old={k for k in ds if normal[k]['complete']};new={k for k,d in ds.items() if d['complete']}
            interventions[name][mode]=dict(opportunities=len(ds),normal_success=len(old),retained=len(old&new),lost=len(old-new),new=len(new-old),complete=len(new))
    return canonical(metrics),canonical(dict(comparisons=comparisons,interventions=interventions,interpretation='Each edit effect is conditional on its historical parent and this new grammar. Contexts are independent sampled units; poses and variants correlated. No replacement selection, synthetic reversion, independent lineage replication or timing benchmark.'))

def analyze():
    panel=read_compressed(OUT/'panel.json.gz');_,_,meta=load(OUT/'confirmation')
    metrics,analysis=compute(panel,meta,lines(OUT/'confirmation/responses.jsonl.gz'))
    compressed_json(OUT/'metrics.json.gz',metrics);compressed_json(OUT/'analysis.json.gz',analysis)
    brief={a:dict(pairs=metrics[p+'|normal']['pairs'],positive=metrics[p+'|normal']['positive'],families=metrics[p+'|normal']['families']) for a,p in panel['aliases'].items()}
    write_json(OUT/'summary.json',brief)
    print(json.dumps(brief,indent=2),flush=True)
