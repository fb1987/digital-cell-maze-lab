"""Pre-registration scorer checks and separate constructed positive controls."""
from types import SimpleNamespace
import numpy as np
from .selectivity_study import *
from .regulatory import Gene
from .growth import Genome as Program

def synthetic(cases,meta):
    cid=next(c for c,m in meta.items() if m['family']=='paired' and m['prefix']==1 and m['shape']=='straight' and m['arm']==[3,4] and m['side']==0 and m['pose']==0)
    o=cases[cid];j=meta[cid]['junction'];route=set(o.path);masks={'exact':route,'one_extra':route|{j+1},'two_extra':route|{j+1,j+2},'four_extra':route|{j+1,j+2,j+3,j+4},'partial':route-{j},'empty':set(),'flood':{k for k,v in enumerate(o.maze.cells) if v}}
    rows={}
    for name,points in masks.items():
        mask=np.array([k in points for k in range(len(o.maze.cells))],np.uint8)
        r=SimpleNamespace(mask=mask,status='emitted',steps=1,spatial_reads=0,dispatches=0,instructions=0,active_instructions=0,array_bytes=mask.nbytes,range_reads=(0,0,0,0),exposure_checks=0,suppressed_reads=0)
        rows[name]=scored_record(r,o)
    assert rows['exact']['optimal'] and all(not r['optimal'] for k,r in rows.items() if k!='exact')
    assert rows['one_extra']['partial']==rows['two_extra']['partial']==rows['four_extra']['partial']
    assert 1==rows['exact']['selectivity']>rows['one_extra']['selectivity']>rows['two_extra']['selectivity']>rows['four_extra']['selectivity']>rows['flood']['selectivity']>.5>rows['partial']['selectivity']>rows['empty']['selectivity']==0
    return dict(case=cid,rows=rows,candidate_calls=0,interpretation='Observer-only masks; never candidates. Current branch score ties long/short stubs, replacement strictly orders them. Coverage tier preserves complete routes; flooded routes remain invalid, never solution-ranked.')

def positive_controls():
    from .foundation_calibration import controls
    old=controls();base=old['output_register'];items={}
    for name in ('intact','output_register'):
        i=old[name];items[name]=Individual('diagnostic/selectivity/'+name,Genome(i.genome,7),None,0)
    for src in range(64):
        rows=[g.row() for g in base.genome.genes];rows[28][2]=src
        items[f'repair{src}']=Individual(f'diagnostic/selectivity/repair{src}',Genome(Program(tuple(Gene(*r) for r in rows)),7),None,0)
    return items

def control_ids(meta):
    return [c for c,m in meta.items() if m['family']=='paired' and m['prefix'] in (1,2) and m['pose']==0]

def profile():
    assert not (FIXTURES/'profile.json').exists();t=time.perf_counter();cases,_,meta=load(FIXTURES);w=warm(cases);b=Budget(180);pools=read_compressed(OUT/'pools.json.gz');ids=profile_ids(meta);rates={};opseconds=0.;synth=synthetic(cases,meta);write_json(FIXTURES/'objective_checks.json',synth)
    assert len(ids)==24
    with gzip.open(FIXTURES/'responses.jsonl.gz','wt',compresslevel=1) as log,gzip.open(FIXTURES/'reproduction.jsonl.gz','wt',compresslevel=1) as births:
        for key,pool in pools.items():
            before=b.seconds;pop=[Individual.load(raw) for raw in pool['items']];rr={i.identity:assay(i,cases,ids,b,log,'profile',key,-1) for i in pop};rates[key]=(b.seconds-before)/(96*len(ids))
            for arm in ARMS:
                rank=ranked(pop,rr,meta,arm);state=init_state(key+'/'+arm,pool);start=time.perf_counter();new,event=reproduce(state,rank,{})
                opseconds+=time.perf_counter()-start;assert reproduce(state,rank,{})==(new,event)
                logrow(births,dict(event=event,next_state_digest=digest(new)))
        pcs=positive_controls();cr={}
        for name,i in pcs.items():cr[i.identity]=assay(i,cases,control_ids(meta),b,log,'positive_control',name,-1)
        scores={arm:ranked(list(pcs.values()),cr,meta,arm)[0][1].identity for arm in ('current','selective')}
        assert all(r['optimal'] for r in cr[pcs['intact'].identity])
        assert not all(r['optimal'] for r in cr[pcs['output_register'].identity])
        assert all(all(r['optimal'] for r in cr[i]) for i in scores.values())
        # Feasibility only; every construct stays outside all random-origin pools.
        controls=dict(items={k:v.save() for k,v in pcs.items()},best=scores,inputs=len(control_ids(meta)),optimal={k:sum(r['optimal'] for r in cr[v.identity]) for k,v in pcs.items()})
        compressed_json(FIXTURES/'positive_controls.json.gz',controls)
    rate=1.5*sum(rates.values());nv=len(validation_ids(meta));estimated_initial=96*nv*rate;estimated_round=(4*96*12+4*2*nv/16)*rate+2*opseconds
    write_json(FIXTURES/'profile.json',dict(passed=estimated_initial+16*estimated_round<660,planning_rate=rate,pool_rates=rates,reproduction_seconds=opseconds,validation_inputs=nv,estimated_initial_seconds=estimated_initial,estimated_round_seconds=estimated_round,estimated_16_round_seconds=estimated_initial+16*estimated_round,budget=b.save(),warmup=w,wall_seconds=time.perf_counter()-t,scores_used_for_schedule=False,calibration_births_discarded=True))
    print((FIXTURES/'profile.json').read_text(),flush=True)
