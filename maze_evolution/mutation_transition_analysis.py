"""V12P frozen descriptive analyses; no selection or inference."""
import hashlib,json,random
from collections import defaultdict,Counter
from .mutation_transition_data import OUT,load,mechanism_case,SEED
from .foundation_study import read_compressed,compressed_json
from .foundation_calibration import write_json
from .routing_transfer import lines,canonical


def stratum(m):
    return '/'.join(map(str,('stress' if m['stress'] else 'core',m['arm'],m['shape'],m['bend'],m['control'],m['prefix'],m['graph'])))


def summarize(rows,meta):
    groups=defaultdict(list);pair_rows=defaultdict(list);signature=hashlib.sha256();work=0
    for r in rows:
        m=meta[r['case']];groups[stratum(m)].append(r)
        if m['family']=='paired':pair_rows[m['config']+f'/pose{m["pose"]}'].append(r)
        signature.update(json.dumps([r['case'],r['mask'],r['status'],r['steps']],separators=(',',':')).encode())
        work+=r['reads']+r['dispatches']+r['exposure_checks']
    pairs={k:all(r['optimal'] for r in rs) for k,rs in pair_rows.items()};assert all(len(rs)==2 for rs in pair_rows.values())
    details={k:dict(complete=pairs[k],template=meta[rs[0]['case']]['template'],stratum=stratum(meta[rs[0]['case']]),
                   mechanism=mechanism_case(meta[rs[0]['case']])) for k,rs in pair_rows.items()}
    def counts(rs):
        return dict(inputs=len(rs),reachable=sum(r['reachable'] for r in rs),valid=sum(r['valid'] for r in rs),optimal=sum(r['optimal'] for r in rs),
            no_path=sum(r['no_path'] for r in rs),false_no_path=sum(r['reachable'] and r['status']=='no_path' for r in rs),
            corridors=sum(r['optimal'] for r in rs if meta[r['case']]['family']=='corridor'),
            failures=dict(Counter(r['failure'] for r in rs if not r['optimal'] and not r['no_path'])))
    ss={k:counts(rs) for k,rs in groups.items()}
    for k,v in ss.items():
        dd=[d for d in details.values() if d['stratum']==k];v.update(pairs=sum(d['complete'] for d in dd),opportunities=len(dd))
    return dict(**counts(rows),pairs=sum(pairs.values()),pair_opportunities=len(pairs),details=details,strata=ss,
                response_signature=signature.hexdigest(),work=work,max_array_bytes=max(r['array_bytes'] for r in rows))


def collect(path,meta):
    result={};current=None;rows=[]
    for rec in lines(path):
        key=rec['model']+'|'+rec['mode']
        if current is not None and key!=current:result[current]=summarize(rows,meta);rows=[]
        current=key;rows.append(rec['row'])
    if current is not None:result[current]=summarize(rows,meta)
    return result


def bootstrap(values):
    # Templates, not poses, are resampled. Conditional on this selected lineage/grammar.
    rng=random.Random(SEED+100);n=len(values)
    if not n:return dict(n=0)
    draws=sorted(sum(values[rng.randrange(n)] for _ in range(n))/n for _ in range(10000))
    return dict(n=n,mean=sum(values)/n,lower=draws[249],upper=draws[9749],unit='seeded template; correlated variants averaged')


def packet(metrics,panel):
    normal={alias:metrics[key+'|normal'] for alias,key in panel['aliases'].items()};transitions={};first={};mechanisms={}
    for top in ('local','evolved'):
        series=[normal[f'{top}/{label}'] for label in panel['chains']['route']];first[top]={}
        for pair in series[0]['details']:
            first[top][pair]=next((i for i,m in enumerate(series) if m['details'][pair]['complete']),None)
        transitions[top]=[]
        for depth in range(1,17):
            before,after=series[depth-1:depth+1]
            gains=[k for k,d in after['details'].items() if d['complete'] and not before['details'][k]['complete']]
            losses=[k for k,d in before['details'].items() if d['complete'] and not after['details'][k]['complete']]
            transitions[top].append(dict(depth=depth,pairs=after['pairs'],gained=len(gains),lost=len(losses),gained_keys=gains,lost_keys=losses,
                corridor_change=after['corridors']-before['corridors'],response_changed=after['response_signature']!=before['response_signature']))
    for key in panel['mechanisms']:
        base=metrics[key+'|normal'];mechanisms[key]={}
        for mode in ('pulse_off','flag_off','both_off','endpoint_off','nonlocal_off'):
            m=metrics[key+'|'+mode];normal_good={k for k in m['details'] if base['details'][k]['complete']};good={k for k,d in m['details'].items() if d['complete']}
            mechanisms[key][mode]=dict(eligible_normal_pairs=len(normal_good),retained=len(normal_good&good),lost=len(normal_good-good),new=len(good-normal_good),pairs=len(good),
                normal_input_subset=len(m['details']),work=m['work'])
    target=normal['local/route/d16'];paired_contrasts={}
    for prefix in (1,2,4):
        by=defaultdict(lambda:defaultdict(list))
        for d in target['details'].values():
            scope,arm,shape,bend,control,p,graph=d['stratum'].split('/')
            if scope=='core' and control=='full' and int(p) in (0,prefix):by[d['template']][int(p)].append(int(d['complete']))
        values=[sum(v[prefix])/len(v[prefix])-sum(v[0])/len(v[0]) for v in by.values()]
        paired_contrasts[f'full_prefix{prefix}_minus0']=bootstrap(values)
    return dict(normal=normal,transitions=transitions,first_success_depth=first,mechanisms=mechanisms,context_conditional_contrasts=paired_contrasts,
        O_informed=True,evolution=False,posthoc_selection=False)


def analyze():
    _,_,meta=load(OUT/'confirmation');panel=read_compressed(OUT/'panel.json.gz');ms=collect(OUT/'confirmation/responses.jsonl.gz',meta);compressed_json(OUT/'metrics.json.gz',ms)
    result=packet(ms,panel);compressed_json(OUT/'analysis.json.gz',result)
    concise={a:{f:m[f] for f in ('pairs','pair_opportunities','optimal','valid','corridors','no_path','false_no_path','work')} for a,m in result['normal'].items()}
    write_json(OUT/'analysis_summary.json',dict(normal=concise,transitions={t:[{k:v for k,v in d.items() if not k.endswith('_keys')} for d in rows] for t,rows in result['transitions'].items()},context_conditional_contrasts=result['context_conditional_contrasts']))
    print((OUT/'analysis_summary.json').read_text())
