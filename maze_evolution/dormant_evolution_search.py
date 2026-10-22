"""M23 common exploration allocation; matched ordinary/enabled/disabled expression variation."""
import random
from copy import deepcopy
from collections import defaultdict
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz
from .datasets import seed_for
from .routing_transfer import canonical
from .deep_campaign_store import packed,hashed
from .dormant_evolution_genome import Genome,vary,random_genome,ARMS,embed
from .dormant_evolution_checkpoint import founders
from .modular_pilot_search import tupled,values,lexicase,candidates


PARENT='m14/reference/quota_parent'
SPECIALIST='m14/modular/1/explore/g320/b48'

def integration_rank(i,rows,meta,caps):
    from .exploration_allocation_metrics import integration
    v=integration(caps[i['id']],caps[PARENT],caps[SPECIALIST],meta,1)
    keep=[x for x in v['parent_retention'].values() if x is not None]
    return (int(not caps[i['id']]['false']),min(keep,default=0),
        v['specialist_pair_fraction'] or 0,sum(keep)/max(1,len(keep)),*rank(rows[i['id']],meta))

def assessment_nominees(pool,rows,meta,protected):
    from .exploration_allocation_metrics import capabilities_plus,upstream_pairs
    caps={i['id']:capabilities_plus(rows[i['id']],meta) for i in pool}
    union=set().union(*(upstream_pairs(caps[i['id']],meta) for i in protected))
    def upstream(i):
        c=caps[i['id']];return (len(upstream_pairs(c,meta)-union),-len(c['false']),len(c['correct_no_path']),*rank(rows[i['id']],meta))
    def choose(key):return sorted(pool,key=lambda i:(tuple(-x for x in key(i)),i['id']))[0]
    return [choose(lambda i:integration_rank(i,rows,meta,caps)),choose(upstream),ordered(pool,rows,meta,True)[0]]


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
    if ordinary:return sorted(items,key=lambda i:(tuple(-v for v in rank(rows[i['id']],meta,True)),i['id']))
    from .exploration_allocation_metrics import capabilities_plus
    caps={i:capabilities_plus(rs,meta) for i,rs in rows.items()}
    return sorted(items,key=lambda i:(tuple(-v for v in integration_rank(i,rows,meta,caps)),i['id']))


def signature(rows):return hashed(packed([(r['status'],r['mask']) for r in rows]))


def quality_profile(rows):
    """Finite-panel routing performance, not arbitrary raster novelty.

    A correct disconnected answer cannot alone qualify. Missing-endpoint partial
    progress must be emitted and >=0.25 under the existing branch/stray-penalized
    oracle fitness. This is selection-only information, never candidate inference.
    """
    if any(r['reachable'] and r['status']=='no_path' for r in rows):return None
    vector=[]
    for r in rows:
        value=0
        if r['reachable']:
            if r['optimal']:value=4
            elif r['valid']:value=3
            elif r['status']=='emitted' and r['failure']=='missing_endpoint' and r['partial']>=.25:
                value=min(2,int(r['partial']*4))
        vector.append(value)
    return tuple(vector) if any(vector) else None


def exploration_pool(left,rows,meta,core,rng):
    represented={quality_profile(rows[i['id']]) for i in core}
    cells={};eligible=0;rejected=0;represented_count=0
    for i in left:
        profile=quality_profile(rows[i['id']])
        if profile is None:rejected+=1;continue
        if profile in represented:represented_count+=1;continue
        eligible+=1
        key=(tuple(-v for v in rank(rows[i['id']],meta)),Genome.from_dict(i['genome']).digest,i['id'])
        if profile not in cells or key<cells[profile][0]:cells[profile]=(key,i)
    # Sample behavior cells equally, not proportional to clone count or raw
    # Hamming novelty. No additional organism evaluations or persistence cache.
    candidates=[cells[p][1] for p in sorted(cells)]
    rng.shuffle(candidates);selected=candidates[:12]
    return selected,dict(enabled=True,quality_eligible_distinct_cells=len(cells),
        eligible_individuals=eligible,rejected_no_useful_progress_or_false_no_path=rejected,
        already_represented_individuals=represented_count,
        selected=[dict(id=i['id'],profile=list(quality_profile(rows[i['id']]))) for i in selected],
        reserved_mutation_births=12 if selected else 0)


def retain(items,rows,meta,rng,protected,count=44,exploration=False):
    ranked=ordered(items,rows,meta);registry={i['id']:i for i in items}
    chosen=[registry[i['id']] for i in protected]
    assert all(registry[i['id']]==i for i in protected)
    left=[i for i in ranked if i['id'] not in {a['id'] for a in chosen}]
    merit=left[:8];chosen+=merit;left=left[8:]
    explorers,exploration_log=exploration_pool(left,rows,meta,chosen,rng) if exploration else ([],dict(enabled=False))
    chosen+=explorers;explorer_ids={i['id'] for i in explorers}
    left=[i for i in left if i['id'] not in explorer_ids]
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
    return chosen,neutral_ids,explorers,exploration_log


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
                if identity.startswith('budget_padding/'):
                    assert data['kind']=='assessment';continue
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
            survivors,neutral,explorers,exploration_log=retain(s['population'],r,meta,rng,s['protected'],exploration=s['allocation']=='explore');vals={i['id']:values(r[i['id']]) for i in survivors};births=[]
            for b in range(52):
                identity=f'{s["namespace"]}/{s["name"]}/g{s["generation"]+1}/b{b}'
                if b<7:
                    g=random_genome(rng);parent=None;root=identity;depth=0;events=[];origin='M23_random_immigrant';anchor=None;intermediate=None
                else:
                    eligible=survivors;quota_root=None
                    from_exploration=bool(explorers and b<19)
                    p=explorers[(b-7)%len(explorers)] if from_exploration else lexicase(rng,eligible,vals); g=Genome.from_dict(p['genome']);events=[];intermediate=None
                    assert s['method']=='single'
                    opportunities=1
                    for step in range(opportunities):
                        if step:intermediate=g.to_dict()
                        g,event=vary(g,rng,s['arm']);events.append(event)
                    parent=p['id'];root=p['root'];depth=p['mutation_depth']+1;origin=p['origin'];anchor=p['source_anchor']
                child=dict(id=identity,genome=g.to_dict(),root=root,parent=parent,birth=s['generation']+1,mutation_depth=depth,origin=origin,source_anchor=anchor)
                births.append(dict(item=child,events=events,intermediate=intermediate,quota_root=quota_root if b>=7 else None,parent_policy=('exploration_cycle' if from_exploration else 'shared_lexicase') if b>=7 else 'random_immigrant'))
            s['population']=survivors+[b['item'] for b in births];s['generation']+=1
            decision=dict(name=s['name'],survivors=[i['id'] for i in survivors],neutral_reserve=neutral,exploration=exploration_log,explorer_ids=[i['id'] for i in explorers],births=births)
        s['rng']=rng.getstate();assert len(s['population'])==len({i['id'] for i in s['population']})==96
        for i in s['protected']:assert next(p for p in s['population'] if p['id']==i['id'])==i
        decisions.append(decision)
    return canonical(states),canonical(decisions)
