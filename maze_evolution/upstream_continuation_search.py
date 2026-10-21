"""M6 single-edit continuation of six preserved random-origin references."""
import random
from copy import deepcopy
from collections import defaultdict
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz
from .datasets import seed_for
from .routing_transfer import canonical
from .deep_campaign_store import packed,hashed
from .modular_genome import Genome,mutate,random_genome
from .modular_pilot_search import tupled,values,lexicase,candidates


def source_panel():
    import json
    p=ROOT/'results/holding_assay'
    choices=readz(p/'choices.json.gz')['items'];refs=readz(p/'references.json.gz')
    registry={i['id']:i for i in choices+refs}
    order=['a1/standard/0191','anchor/0','a0/standard/0434','anchor/1','root/0','root/1']
    result=[]
    for identity in order:
        i=registry[identity];g=i['model']['genome']
        assert i['model']['representation']=='holding'
        # Only standard M1 bodies; no conditional-writer metadata enters inference.
        assert all(v==64 for v in g['write_gates']) and all(v==0 for v in g['write_holds'])
        base=g['base'];Genome.from_dict(base)
        result.append(dict(id='m6/reference/'+identity,genome=base,source_record=i,
            source_file='results/holding_assay/choices.json.gz' if identity.startswith('a') and not identity.startswith('anchor') else 'results/holding_assay/references.json.gz'))
    return canonical(result)


def founders(seed,namespace='m6'):
    sources=source_panel();states=[]
    anchors=[dict(id=i['id'],genome=i['genome'],root=i['id'],parent=None,birth=0,
        mutation_depth=0,origin='preserved_M5_informed_random_origin',source_anchor=i['id']) for i in sources]
    for rep in range(3):
        # Thirty explicit clonal slots per focal genome, plus six protected references.
        # Cloning is neither a mutation nor a new independent random origin.
        items=deepcopy(anchors)
        for k in range(90):
            a=anchors[k%3]
            items.append(dict(a,id=f'{namespace}/initial/{rep}/{k}',root=a['id'],parent=a['id']))
        name=f'modular/{rep}/single'
        states.append(dict(name=name,namespace=namespace,representation='modular',replicate=rep,
            method='single',curriculum='long',generation=0,assessment_generation=-1,
            population=items,protected=deepcopy(anchors),archive=[],frozen=[],
            rng=random.Random(seed_for(seed,'evolution/'+name,0,0)).getstate()))
    return canonical(states)


def assessment_nominees(pool,rows,meta,protected):
    from .upstream_continuation_metrics import capabilities_plus, upstream_pairs
    caps={i['id']:capabilities_plus(rows[i['id']],meta) for i in pool}
    union=set().union(*(upstream_pairs(caps[i['id']],meta) for i in protected))
    a0=caps['m6/reference/anchor/0']['correct_no_path']
    def integrated(i):
        c=caps[i['id']]
        eligible=bool(a0) and len(c['correct_no_path'] & a0)/len(a0)>=.9 and not c['false']
        return (int(eligible),*rank(rows[i['id']],meta))
    def upstream(i):
        c=caps[i['id']]
        return (len(upstream_pairs(c,meta)-union),-len(c['false']),len(c['correct_no_path']),*rank(rows[i['id']],meta))
    def choose(key):return sorted(pool,key=lambda i:(tuple(-x for x in key(i)),i['id']))[0]
    return [choose(integrated),choose(upstream),ordered(pool,rows,meta,True)[0]]


def rank(rows,meta,ordinary=False):
    groups=defaultdict(list)
    for r in rows:
        m=meta[r['case']];family=m['family']
        if ordinary and family not in ('ordinary_perfect','ordinary_random'):continue
        if family=='paired':key=f"paired/{m['graph']}/{m['prefix']}"
        elif family.startswith('ordinary_'):key=f"{family}/{m['length_bin']}"
        else:key=family
        groups[key].append(r)
    scores=[0.,0.,0.]
    for rs in groups.values():
        false=sum(r['reachable'] and r['status']=='no_path' for r in rs)
        scores[0]+=(sum(r['optimal'] or r['no_path'] for r in rs)-false)/len(rs)
        scores[1]+=(sum(r['valid'] or r['no_path'] for r in rs)-false)/len(rs)
        scores[2]+=sum(r['partial'] for r in rs)/len(rs)
    return tuple(round(v/max(1,len(groups)),10) for v in scores)


def ordered(items,rows,meta,ordinary=False):
    return sorted(items,key=lambda i:(tuple(-v for v in rank(rows[i['id']],meta,ordinary)),i['id']))


def signature(rows):return hashed(packed([(r['status'],r['mask']) for r in rows]))


def retain(items,rows,meta,rng,protected,count=44):
    ranked=ordered(items,rows,meta);registry={i['id']:i for i in items}
    chosen=[registry[i['id']] for i in protected]
    assert all(registry[i['id']]==i for i in protected)
    left=[i for i in ranked if i['id'] not in {a['id'] for a in chosen}]
    merit=left[:8];chosen+=merit;left=left[8:]
    success={i['id']:{r['case'] for r in rows[i['id']] if r['optimal'] or r['no_path']} for i in items}
    covered=set().union(*(success[i['id']] for i in chosen))
    for _ in range(12):
        if not left or len(chosen)>=count:break
        best=max(left,key=lambda i:len(success[i['id']]-covered))
        if not success[best['id']]-covered:break
        chosen.append(best);covered|=success[best['id']];left.remove(best)
    # Retain up to18 distinct genotypes with the same observed behavior as merit
    # representatives. This is finite-panel neutrality, not semantic equivalence.
    signatures={signature(rows[i['id']]) for i in merit}
    neutral=[i for i in left if signature(rows[i['id']]) in signatures];rng.shuffle(neutral)
    seen={Genome.from_dict(i['genome']).digest for i in chosen};neutral_ids=[]
    for i in neutral:
        if len(chosen)>=count or len(neutral_ids)>=18:break
        digest=Genome.from_dict(i['genome']).digest
        if digest in seen:continue
        chosen.append(i);left.remove(i);seen.add(digest);neutral_ids.append(i['id'])
    vals={i['id']:values(rows[i['id']]) for i in left}
    while len(chosen)<count:
        best=lexicase(rng,left,vals);chosen.append(best);left.remove(best)
    return chosen,neutral_ids


def archive(items,rows,meta):
    ranked=ordered(items,rows,meta);chosen=ranked[:4];covered={r['case'] for i in chosen for r in rows[i['id']] if r['optimal'] or r['no_path']}
    left=ranked[4:]
    while left and len(chosen)<16:
        best=max(left,key=lambda i:sum(r['case'] not in covered and (r['optimal'] or r['no_path']) for r in rows[i['id']]))
        chosen.append(best);covered.update(r['case'] for r in rows[best['id']] if r['optimal'] or r['no_path']);left.remove(best)
    return chosen


def transition(states,data,results):
    rows=[{} for _ in states]
    for result in results:
        for e in result['entries']:
            for k,identity in e['aliases']:
                assert identity not in rows[k];rows[k][identity]=e['rows']
    states=deepcopy(states);decisions=[]
    for k,s in enumerate(states):
        r=rows[k];meta=data['metadata'];rng=random.Random();rng.setstate(tupled(s['rng']))
        assert set(r)=={i['id'] for i in candidates(s,data['kind']=='assessment')}
        if data['kind']=='assessment':
            pool=candidates(s,True);s['nominees']=assessment_nominees(pool,r,meta,s['protected'])
            if s['generation']==0:s['frozen']=deepcopy(s['nominees'])
            s['archive']=archive(pool,r,meta);s['assessment_generation']=s['generation']
            decision=dict(name=s['name'],nominees=[i['id'] for i in s['nominees']],archive=[i['id'] for i in s['archive']],births=[])
        else:
            survivors,neutral=retain(s['population'],r,meta,rng,s['protected']);vals={i['id']:values(r[i['id']]) for i in survivors};births=[]
            for b in range(52):
                identity=f'{s["namespace"]}/{s["name"]}/g{s["generation"]+1}/b{b}'
                if b<7:
                    g=random_genome(rng);parent=None;root=identity;depth=0;events=[];origin='M6_random_immigrant';anchor=None;intermediate=None
                else:
                    p=lexicase(rng,survivors,vals);g=Genome.from_dict(p['genome']);events=[];intermediate=None
                    assert s['method']=='single'
                    opportunities=1
                    for step in range(opportunities):
                        if step:intermediate=g.to_dict()
                        g,event=mutate(g,rng);events.append(event)
                    parent=p['id'];root=p['root'];depth=p['mutation_depth']+1;origin=p['origin'];anchor=p['source_anchor']
                child=dict(id=identity,genome=g.to_dict(),root=root,parent=parent,birth=s['generation']+1,mutation_depth=depth,origin=origin,source_anchor=anchor)
                births.append(dict(item=child,events=events,intermediate=intermediate))
            s['population']=survivors+[b['item'] for b in births];s['generation']+=1
            decision=dict(name=s['name'],survivors=[i['id'] for i in survivors],neutral_reserve=neutral,births=births)
        s['rng']=rng.getstate();assert len(s['population'])==len({i['id'] for i in s['population']})==96
        for i in s['protected']:assert next(p for p in s['population'] if p['id']==i['id'])==i
        decisions.append(decision)
    return canonical(states),canonical(decisions)
