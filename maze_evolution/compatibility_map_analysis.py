"""V12W complete factorial effects: no final-based selection or primary replacement."""
from collections import defaultdict,Counter
import json
from .compatibility_map_data import *
from .compatibility_map_study import label,EDIT_IDS
from .routing_mechanism_analysis import summarize
from .lineage_mapping_analysis import comparison
from .causal_dissection_analysis import equality
from .routing_transfer import lines,canonical
from .foundation_calibration import write_json

def mobius(values):
    """Anchored exact finite differences, indexed by subsets, not fitted coefficients."""
    out=list(values)
    for bit in range(4):
        for mask in range(16):
            if mask&(1<<bit):out[mask]-=out[mask^(1<<bit)]
    return out

def totals(m):
    return dict(positive=m['positive'],pairs=m['pairs'],corridors=m['families']['corridor']['optimal'],
        ordinary=sum(m['families'][f]['optimal'] for f in ('ordinary_perfect','ordinary_random')),
        no_path=sum(v['no_path'] for v in m['families'].values()))

def compute(panel,meta,events):
    native=defaultdict(dict)
    for e in events:
        assert e['scope']==e['mode']=='normal'
        native[e['model']][e['row']['case']]=e['row']
    metrics={pid+'|normal':summarize(list(rows.values()),meta) for pid,rows in native.items()};aliases=panel['aliases']
    for m in metrics.values():
        groups=defaultdict(list)
        for key,d in m['details'].items():groups[key.rsplit('/pose',1)[0]].append(d)
        m['positive_full_queried_pose_groups']=sum(len(v)==len(POSES) and all(d['complete'] and d['prefix']>0 for d in v) for v in groups.values())
    totals_by_alias={a:totals(metrics[p+'|normal']) for a,p in aliases.items()}
    comp=lambda a,b:comparison(a,b,metrics,native,aliases,meta)
    store_effects={str(mask):comp(label(mask,False),label(mask,True)) for mask in range(16)}
    toggles={}
    for bit,edit in enumerate(EDIT_IDS):
        for mask in range(16):
            if mask&(1<<bit):continue
            for store in (False,True):
                a,b=label(mask,store),label(mask|(1<<bit),store)
                toggles[f'edit{edit}|{a}']=comp(a,b)
    effects={str(mask):{k:totals_by_alias[label(mask,True)][k]-totals_by_alias[label(mask,False)][k] for k in totals_by_alias[label(mask,True)]} for mask in range(16)}
    interactions={}
    for bit,edit in enumerate(EDIT_IDS):
        for mask in range(16):
            if mask&(1<<bit):continue
            interactions[f'edit{edit}|background{mask}']={k:effects[str(mask|(1<<bit))][k]-effects[str(mask)][k] for k in effects[str(mask)]}
    coefficients={k:mobius([effects[str(mask)][k] for mask in range(16)]) for k in effects['0']}
    per_context={}
    for mask,contrast in store_effects.items():
        for context,v in contrast['positive_by_context'].items():per_context.setdefault(context,{})[mask]=v['after']-v['before']
    context_coefficients={c:mobius([v[str(mask)] for mask in range(16)]) for c,v in per_context.items()}
    minimal={}
    for k in effects['0']:
        harmful=[mask for mask in range(16) if effects[str(mask)][k]<0]
        minimal[k]=[m for m in harmful if not any(s!=m and s&m==s for s in harmful)]
    eq={a+'->'+b:equality(native[aliases[a]],native[aliases[b]]) for a,b in ((label(0,False),'d08'),(label(15,False),'d12'))}
    controls={a+'->'+b:comp(a,b) for a,b in (('fresh2_root','fresh2'),('broad_root','carry1'))}
    return canonical(metrics),canonical(dict(totals=totals_by_alias,store_effects=store_effects,edit_toggles=toggles,
        store_net_effects=effects,conditional_interactions=interactions,anchored_higher_order=coefficients,
        context_store_effects=per_context,context_anchored_higher_order=context_coefficients,minimal_net_harmful_subsets=minimal,
        eq_controls=eq,controls=controls,interpretation='V-informed synthetic factorial; context-conditional causal instruction effects, not evolution or selection. Four structured poses only. Net losses do not mean every case loses. No universal module, general solver, evolutionary operator benefit or speedup established.'))

def analyze():
    panel=read_compressed(OUT/'panel.json.gz');_,_,meta=load(OUT/'confirmation')
    metrics,analysis=compute(panel,meta,lines(OUT/'confirmation/responses.jsonl.gz'))
    compressed_json(OUT/'metrics.json.gz',metrics);compressed_json(OUT/'analysis.json.gz',analysis)
    brief={a:dict(kind=panel['kinds'][a],pairs=metrics[p+'|normal']['pairs'],positive=metrics[p+'|normal']['positive'],families=metrics[p+'|normal']['families']) for a,p in panel['aliases'].items()}
    write_json(OUT/'summary.json',brief)
    print(json.dumps(dict(totals=analysis['totals'],store_net_effects=analysis['store_net_effects'],minimal=analysis['minimal_net_harmful_subsets']),indent=2),flush=True)
