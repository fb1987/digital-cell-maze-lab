"""V12R normal full-board scoring; geometric diagnostics never enter inference."""
import hashlib,json
from collections import defaultdict
from .routing_transfer import canonical

def selected(row):
    raw=bytes.fromhex(row['mask']);return {p for p in range(361) if raw[p//8] & (1<<(p%8))}

def summary(rows,meta):
    groups=defaultdict(list);details=[]
    for r in rows:
        m=meta[r['case']]
        if m['family']=='paired':groups[m['base'],m['pose']].append(r)
    for (base,pose),rs in sorted(groups.items()):
        assert len(rs)==2;a,b=sorted(rs,key=lambda r:meta[r['case']]['side']);mm=meta[a['case']]
        paths=[set(meta[r['case']]['path']) for r in (a,b)];masks=[selected(r) for r in (a,b)];goals={meta[r['case']]['path'][-1] for r in (a,b)}
        private=[(paths[i]-paths[1-i])-goals for i in (0,1)];normal=all(r['status']=='emitted' for r in (a,b))
        signed=sum((len(masks[i]&private[i])-len(masks[1-i]&private[i]))/len(private[i]) for i in (0,1))/2 if normal and all(private) else 0.
        f1=min(2*len(x&p)/max(1,len(x)+len(p)) for x,p in zip(masks,paths));score=max(0.,signed)*f1 if normal else 0.
        details.append(dict(base=base,template=mm['template'],pose=pose,prefix=mm['prefix'],graph=mm['graph'],stress=mm['stress'],arm=mm['arm'],shape=mm['shape'],complete=all(r['optimal'] for r in rs),score=score,partial=min(r['partial'] for r in rs),spill=sum(len(masks[i]-paths[i]) for i in (0,1)),missing=sum(len(paths[i]-masks[i]) for i in (0,1)),normal=normal))
    target=[d for d in details if d['prefix']==1 and not d['stress']];zero=[d for d in details if d['prefix']==0 and not d['stress']]
    return canonical(dict(pairs=sum(d['complete'] for d in details),positive=sum(d['complete'] for d in target),zero=sum(d['complete'] for d in zero),mean_score=sum(d['score'] for d in target)/len(target),target_pairs=len(target),corridors=sum(r['optimal'] for r in rows if meta[r['case']]['family']=='corridor'),no_path=sum(r['no_path'] for r in rows),false_no_path=sum(r['reachable'] and r['status']=='no_path' for r in rows),optimal=sum(r['optimal'] for r in rows),valid=sum(r['valid'] for r in rows),details=details,response=hashlib.sha256(json.dumps([(r['mask'],r['status']) for r in rows],separators=(',',':')).encode()).hexdigest(),counters=hashlib.sha256(json.dumps([(r['steps'],r['active'],r['reads'],r['dispatches'],r['exposure_checks']) for r in rows],separators=(',',':')).encode()).hexdigest(),active=sum(r['active'] for r in rows),reads=sum(r['reads'] for r in rows),dispatches=sum(r['dispatches'] for r in rows),work=sum(r['reads']+r['dispatches']+r['exposure_checks'] for r in rows)))

def compare(child,root):
    assert [(d['base'],d['pose']) for d in child['details']]==[(d['base'],d['pose']) for d in root['details']]
    gains=[a for a,b in zip(child['details'],root['details']) if a['prefix']==1 and not a['stress'] and a['score']>=b['score']+.1-1e-12]
    new=[a for a,b in zip(child['details'],root['details']) if a['prefix']==1 and not a['stress'] and a['complete'] and not b['complete']]
    retained=child['zero']>=.95*root['zero'] and child['corridors']>=.95*root['corridors'] and child['false_no_path']<=root['false_no_path']
    partial=retained and child['mean_score']>=root['mean_score']+.05-1e-12 and len(gains)>=8 and len({d['template'] for d in gains})>=2 and len({d['pose'] for d in gains})>=2
    correct=retained and len(new)>=8 and len({d['template'] for d in new})>=2 and len({d['pose'] for d in new})>=2
    return dict(retained=retained,partial=partial,correct=correct,new_pairs=len(new),score_gains=len(gains),gain_contexts=len({d['template'] for d in gains}),changed=child['response']!=root['response'],counters_changed=child['counters']!=root['counters'])

def rank(m,r):
    c=compare(m,r)
    return (m['positive'],int(c['retained']),round(m['mean_score'],10),m['zero'],m['corridors'],m['no_path']-m['false_no_path'])

def choose(ids,pool,metrics):
    aliases=pool['aliases'];entries=pool['entries']
    order=sorted(ids,key=lambda i:(tuple(-v for v in rank(metrics[aliases[i]],metrics[aliases[entries[i]['root']]])),entries[i]['digest'],i))
    return dict(best=order[0],nominees=order[:2],order=order)
