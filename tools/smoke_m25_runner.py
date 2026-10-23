"""Exercise M25 orchestration with durable artificial receipts; zero new inference."""
import sys,json
from copy import deepcopy
from pathlib import Path
from concurrent.futures import Future
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution import skill_integration as m
from maze_evolution import skill_integration_checkpoint as cp
from maze_evolution.deep_campaign_store import packed,hashed
from maze_evolution.referenced_campaign_store import write_reference,load_layouts


def main():
    out=m.OUT;assert not (out/'registration.json').exists() and not (out/'runner_smoke.json').exists()
    steps=m.readz(out/'rehearsal.json.gz');ss=m.readz(out/'fixture_founders.json.gz');cache={}
    for st in steps:
        specs=m.task_specs(ss,st['data'])
        for spec,receipt in zip(specs,st['receipts']):cache[hashed(packed(spec))]=receipt
        ss,_=m.transition(ss,st['data'],st['receipts'])
    initial=m.readz(out/'fixture_founders.json.gz')
    for s in initial:s.setdefault('nominees',deepcopy(s['protected'][:3]))
    class ReplayExecutor:
        def __init__(self,*args,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def submit(self,fn,spec,*args):
            f=Future();f.set_result(deepcopy(cache[hashed(packed(spec))]));return f
    target=out/'runner_smoke';target.mkdir();m.RUN=m.ROOT/'runs/skill_integration_m25/runner_smoke';m.OUT=target
    config=dict(m.CONFIG,max_rounds=246,layout_base_manifest=str(out/'registered_exclusions.json'))
    m.check=lambda:config;m.pushed=lambda path:None;m.ProcessPoolExecutor=ReplayExecutor
    m.writez(target/'founders.json.gz',initial);m.writez(target/'inherited_registry.json.gz',m.readz(out/'fixture_registry.json.gz'))
    m.writez(target/'comparison_archive.json.gz',[dict(id='archive/artificial',representation='connected',genome=initial[0]['protected'][0]['genome'])])
    write_reference(target/'exclusions.json',out/'registered_exclusions.json',load_layouts(out/'registered_exclusions.json'))
    validation=deepcopy(steps[0]['data']);validation['generation']=0
    m.data_builder.validation=lambda seed,previous:deepcopy(validation)
    data={st['data']['generation']:st['data'] for st in steps if st['data']['kind']=='train'}
    m.data_builder.training=lambda seed,g,previous:deepcopy(data[g])
    m.run();session=json.loads((target/'session.json').read_text())
    assert session['status']=='complete' and session['generation']==246 and session['new_rounds']==3 and session['stop']['reason']=='round_ceiling'
    assert m.readz(target/'final_states.json.gz')==ss
    m.writej(out/'runner_smoke.json',dict(status='PASS',actual_orchestrator_exercised=True,new_inference_calls=0,
        artificial_receipts_reused=True,elapsed_clock_and_resource_guards_exercised=True,normal_stop_and_freeze_exercised=True,session=session))

if __name__=='__main__':main()
