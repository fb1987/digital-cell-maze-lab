"""Discarded artificial rehearsal, exact replay and excluded fixtures; never science."""
import sys,time,json,random,multiprocessing
from copy import deepcopy
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution import connected_evolution as m
from maze_evolution.connected_evolution_checkpoint import founders,inherited_registry,CHILD
from maze_evolution.modular_genome import Genome,random_node
from maze_evolution.deep_campaign_store import packed,hashed


def main():
    assert not (m.OUT/'registration.json').exists() and not (m.OUT/'profile.json').exists()
    previous=m.load_layouts(m.ROOT/'results/connected_copy_assay/whole_layout_exclusions.json')
    rng=random.Random(m.CONFIG['fixture_seed']);fake=deepcopy(m.readz(m.OUT/'sources.json.gz'))
    for i in fake['protected'].values():
        i['genome']=Genome(tuple((random_node(rng,0),) for _ in range(8)),(tuple(range(8)),)*8).to_dict()
    fake['anchors']['parent']=deepcopy(fake['protected']['m14/reference/gated_specialist'])
    fake['anchors']['child']['genome']=deepcopy(fake['anchors']['parent']['genome'])
    fake['last_birth']['events']=[dict(kind='fixture_inherited_edit',not_scientific=True)]
    states=founders(m.CONFIG['fixture_seed'],namespace='m19-fixture',sources=fake)
    m.writez(m.OUT/'fixture_founders.json.gz',states);m.writez(m.OUT/'fixture_registry.json.gz',inherited_registry(states,fake))
    steps=[];wall=[];started=time.monotonic()
    with ProcessPoolExecutor(m.CONFIG['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=m.shared.worker_init) as pool:
        for k in range(5):
            t=time.monotonic();g=states[0]['generation']
            data=m.data_builder.validation(m.CONFIG['validation_seed'],previous) if k in (0,4) else m.data_builder.training(m.CONFIG['fixture_seed'],g,previous)
            data['generation']=g;before=set(previous)
            if data['kind']=='train':assert m.canonical(m.data_builder.training(m.CONFIG['fixture_seed'],g,previous))==m.canonical(data)
            previous.update(data['new_layouts']);spec=m.task_specs(states,data);mz=data['mazes'];h=hashed(packed(mz))
            receipts=list(pool.map(m.evaluate_task,spec,[mz]*len(spec),[h]*len(spec)))
            nxt,event=m.transition(states,data,receipts)
            assert m.transition(m.unpacked(packed(states)),m.unpacked(packed(data)),m.unpacked(packed(receipts)))==(nxt,event)
            counts=[0]*9
            for task in spec:
                for e in task:
                    for n,identity in e['aliases']:counts[n]+=len(e['queries'])
            assert counts==([96*96]*9 if data['kind']=='train' else [115*392]*9)
            steps.append(dict(data=data,receipts=receipts,decisions=event,state_hash=hashed(packed(nxt))))
            states=nxt;wall.append(time.monotonic()-t)
            print('fixture stage',k,data['kind'],g,'calls',sum(r['calls'] for r in receipts),flush=True)
            assert time.monotonic()-started<600 and m.shared.process_resources()<m.CONFIG['memory_bytes']
    m.writez(m.OUT/'rehearsal.json.gz',steps)
    final=m.data_builder.confirmation(m.CONFIG['fixture_seed']+1,previous);previous.update(final['new_layouts'])
    m.writez(m.OUT/'final_fixture.json.gz',final)
    ids=final['queries']['all'];mz=[x for x in final['mazes'] if x['case_id'] in set(ids)]
    controls=m.evaluate_task([dict(model={k:c[k] for k in ('representation','genome')},queries=ids,aliases=[c['id']]) for c in m.controls()],mz,'m19fixturecontrols')
    assert all(r['optimal'] or r['no_path'] for e in controls['entries'] for r in e['rows'])
    m.writez(m.OUT/'control_fixture.json.gz',controls);m.write_layouts('exclusions',previous)
    profile=dict(scientific_calls=0,artificial_founders=True,calls=sum(r['calls'] for s in steps for r in s['receipts']),
        candidate_seconds=sum(r['candidate_seconds'] for s in steps for r in s['receipts']),control_calls=controls['calls'],
        control_candidate_seconds=controls['candidate_seconds'],wall_by_stage=wall,wall_seconds=time.monotonic()-started,
        all_controls_correct=True,all_selection_mutation_rng_replayed=True,equal_nominal_allocations=True,rehearsal_births=3*9*52,
        whole_layouts=len(previous))
    m.writej(m.OUT/'profile.json',profile);print(json.dumps(profile,indent=2))

if __name__=='__main__':main()
