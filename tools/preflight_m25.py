"""M25 discarded evolution rehearsal, artificial models and ONLY old excluded inputs."""
import sys,time,multiprocessing
from pathlib import Path
from copy import deepcopy
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution import skill_integration as m
from maze_evolution.skill_integration_checkpoint import START,POLICIES
from maze_evolution import skill_integration_data as db
from maze_evolution.routing_transfer import canonical
from maze_evolution.deep_campaign_store import hashed,packed


def fixture_founders():
    old=m.readz(m.ROOT/'results/dormant_evolution/fixture_founders.json.gz');states=[]
    for source in old:
        if source['arm']!='enabled':continue
        for policy in POLICIES:
            s=deepcopy(source);s.update(name=source['name']+'/'+policy,namespace='m25-fixture',policy=policy,predecessor_name=source['name'],
                generation=START,phase_start=START,assessment_generation=-1)
            states.append(s)
    return canonical(states)


def fixture_steps():
    old=m.readz(m.ROOT/'results/dormant_evolution/rehearsal.json.gz');assessment=deepcopy(old[0]['data']);assessment['new_layouts']=[]
    extras=db.retention_panel(assessment);steps=[];oldmazes={x['case_id']:x for x in assessment['mazes']}
    for entry in old:
        d=deepcopy(entry['data']);d['new_layouts']=[];d['generation']+=START
        if d['kind']=='train':
            mazes={r['case_id']:r for r in d['mazes']};d['retention_queries']={}
            for key,queries in d['queries'].items():
                extra=extras[key.split('/')[0]];assert not set(extra)&set(queries)
                d['queries'][key]=queries+extra;d['retention_queries'][key]=extra
                for c in extra:mazes[c]=oldmazes[c];d['metadata'][c]=assessment['metadata'][c]
            d['mazes']=list(mazes.values());assert all(len(q)==120 for q in d['queries'].values())
        steps.append(d)
    return steps


def main():
    assert not (m.OUT/'registration.json').exists() and not (m.OUT/'profile.json').exists()
    ss=fixture_founders();registry={}
    for s in ss:
        for label in ('population','protected','archive','frozen','nominees'):
            for i in s.get(label,[]):registry[i['id']]=dict(item=deepcopy(i),events=[],phase='M25_fixture_inherited')
    m.writez(m.OUT/'fixture_founders.json.gz',ss);m.writez(m.OUT/'fixture_registry.json.gz',registry)
    steps=[];started=time.time()
    with ProcessPoolExecutor(10,mp_context=multiprocessing.get_context('spawn'),initializer=m.shared.worker_init) as pool:
        for n,data in enumerate(fixture_steps()):
            specs=m.task_specs(ss,data);h=hashed(packed(data['mazes']));receipts=list(pool.map(m.evaluate_task,specs,[data['mazes']]*len(specs),[h]*len(specs)))
            nxt,events=m.transition(ss,data,receipts);assert m.transition(m.unpacked(packed(ss)),data,receipts)==(nxt,events)
            steps.append(dict(data=data,receipts=receipts,decisions=events,state_hash=hashed(packed(nxt))))
            ss=nxt;print('M25 discarded stage',n,data['kind'],sum(r['calls'] for r in receipts),flush=True)
    m.writez(m.OUT/'rehearsal.json.gz',steps)
    m.writej(m.OUT/'profile.json',dict(status='PASS',scientific_calls=0,new_layouts=0,artificial_founders=True,
        calls=sum(r['calls'] for s in steps for r in s['receipts']),candidate_seconds=sum(r['candidate_seconds'] for s in steps for r in s['receipts']),
        cpu_seconds=sum(r['cpu_seconds'] for s in steps for r in s['receipts']),wall_seconds=time.time()-started,
        births=sum(len(e['births']) for s in steps for e in s['decisions']),all_transition_rng_replay=True))

if __name__=='__main__':main()
