"""Post-freeze goal-context assay on unchanged selected choice models; no selection."""
import argparse,gzip,hashlib,json,time
from pathlib import Path
import numpy as np
from .growth_study import selections
from .beacon_probe import observe
from .growth_runtime import Organism
from .growth import Individual
from .evaluator import Maze,Oracle
from .experiment import write_json
from .runtime import Limits

HIDDEN=[0,1,3,4,5,6]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def unpack(value,n):return np.unpackbits(np.frombuffer(bytes.fromhex(value),dtype=np.uint8),bitorder='little')[:n]


def metrics(states):
    x=np.asarray(states,dtype=np.int64);on=x[0,0]!=x[1,0];off=x[0,1]!=x[1,1]
    interaction=(x[0,0]-x[1,0])!=(x[0,1]-x[1,1])
    return dict(goal_changes_hidden_region=bool(on[HIDDEN].any()),hidden_region_changes=int(on[HIDDEN].sum()),
        goal_changes_hidden_vertex=bool(on[HIDDEN,0].any()),goal_changes_hidden_exits=bool(on[HIDDEN,1:].any()),
        goal_changes_output_exits=bool(on[2,1:].any()),source_modulates_hidden_goal_contrast=bool(interaction[HIDDEN].any()),
        removed_source_hidden_goal_changes=int(off[HIDDEN].sum()))


def load(out):
    out=Path(out);config=json.loads((out/'config.json').read_text());champions=json.loads((out/'champions.json').read_text())
    oracles={}
    for r in json.loads(gzip.open(out/'mazes.json.gz','rt').read()):
        if r['split']!='test_pairs':continue
        m=Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id']);oracles[m.case_id]=Oracle.build(m)
    pairs=[r for r in json.loads((out/'pairs.json').read_text()) if r['first'] in oracles and not r['mixed']]
    models={};aliases={}
    for rep in range(3):
        _,items=selections(champions,rep,Limits(**config['eval_limits']))
        for arm,(item,topology,mode) in items.items():
            if not (arm.endswith('/choice') or arm.endswith('/frozen_choice')):continue
            key=f'{rep}/{topology}/{item.genome.digest}'
            aliases[f'{rep}/{arm}']=key
            models.setdefault(key,dict(individual=item.save(),replicate=rep,topology=topology))
    return config,oracles,pairs,models,aliases


def run(out):
    out=Path(out);target=out/'goal_context.json'
    if target.exists():raise FileExistsError('Goal-context assay already exists')
    started=time.perf_counter();config,oracles,pairs,models,aliases=load(out);rows=[];work=probes=0
    for key,saved in models.items():
        organism=Organism(Individual.load(saved['individual']).genome,saved['topology'],Limits(**config['eval_limits']),goal_pulse=True)
        for pair in pairs:
            if f"/r{saved['replicate']}/" not in pair['first']:continue
            region=[pair['decision']['vertex']]+pair['decision']['exits'];states=[];masks=[];meta=[];row_work=0
            for case in (pair['first'],pair['second']):
                m=oracles[case].maze;both=[];bits=[];metadata=[]
                for source in (True,False):
                    p=observe(organism,m.cells,m.w,m.h,m.start,m.goal,16,source)
                    both.append(p.state[:,region].tolist());bits.append(np.packbits(p.state[2]>0,bitorder='little').tobytes().hex())
                    metadata.append(dict(steps=p.steps,dispatches=p.dispatches,reads=p.reads,status=p.status,range_reads=p.range_reads,array_bytes=p.array_bytes))
                    row_work+=p.dispatches+p.reads;probes+=1
                states.append(both);masks.append(bits);meta.append(metadata)
            aligned=all(p['steps']==16 for goal in meta for p in goal)
            rows.append(dict(model=key,first=pair['first'],second=pair['second'],region=region,states=states,masks=masks,
                observations=meta,aligned=aligned,metrics=metrics(states),work=row_work));work+=row_work
    result=dict(scope='Post-hoc fixed-model assay after primary final results. Reuses final paired layouts;no new selection,training or accuracy claim. Hidden channels0,1,3,4,5,6 at fork+exits;output2/stop7 excluded.',
        models=models,aliases=aliases,records=rows,elapsed_seconds=time.perf_counter()-started,charged_work=work,probes=probes,
        source_sha256=sha(__file__),input_sha256={name:sha(out/name) for name in ('champions.json','config.json','mazes.json.gz','pairs.json','paired_holdout.jsonl.gz','goal_timecourse.json')})
    write_json(target,result);print({k:v for k,v in result.items() if k not in ('models','aliases','records','input_sha256')})


def verify(out):
    out=Path(out);started=time.perf_counter();r=json.loads((out/'goal_context.json').read_text());assert r['source_sha256']==sha(__file__)
    for name,h in r['input_sha256'].items():assert sha(out/name)==h
    config,oracles,pairs,models,aliases=load(out);assert r['models']==models and r['aliases']==aliases
    by_case={p['first']:p for p in pairs};native={};courses={}
    for line in gzip.open(out/'paired_holdout.jsonl.gz','rt'):
        d=json.loads(line)
        if 'baseline' in d:continue
        for c in d['cases']:native[(d['replicate'],d['arm'],c['case'])]=c
    for c in json.loads((out/'goal_timecourse.json').read_text()):
        if c['horizon']==16:courses[(c['replicate'],c['arm'],c['first'])]=c
    work=probes=checked=0
    for row in r['records']:
        model=models[row['model']];pair=by_case[row['first']];assert row['second']==pair['second'] and row['region']==[pair['decision']['vertex']]+pair['decision']['exits']
        x=np.asarray(row['states']);assert x.shape==(2,2,8,len(row['region'])) and np.all((0<=x)&(x<=65535))
        assert row['metrics']==metrics(row['states']) and row['aligned']==all(p['steps']==16 for goal in row['observations'] for p in goal)
        organism=Organism(Individual.load(model['individual']).genome,model['topology'],Limits(**config['eval_limits']),goal_pulse=True);cost=0
        for i,case in enumerate((row['first'],row['second'])):
            m=oracles[case].maze;n=len(m.cells)
            for j,source in enumerate((True,False)):
                saved=row['observations'][i][j];actual=observe(organism,m.cells,m.w,m.h,m.start,m.goal,16,source)
                assert np.array_equal(actual.state[:,row['region']],x[i,j]) and np.array_equal(actual.state[2]>0,unpack(row['masks'][i][j],n))
                assert (actual.steps,actual.dispatches,actual.reads,actual.status)==(saved['steps'],saved['dispatches'],saved['reads'],saved['status'])
                assert np.array_equal(x[i,j,2]>0,unpack(row['masks'][i][j],n)[row['region']])
                cost+=actual.dispatches+actual.reads;probes+=1
            for alias,key in aliases.items():
                if key!=row['model']:continue
                rep,arm=alias.split('/',1);saved=native[(int(rep),arm,case)]
                assert row['masks'][i]==[saved['probe_mask'],saved['source_removed_mask']]
                assert x[i,0,:,0].tolist()==courses[(int(rep),arm,row['first'])]['junction_states'][i];checked+=1
        assert cost==row['work'];work+=cost
    assert work==r['charged_work'] and probes==r['probes'];summary=[]
    for alias,key in aliases.items():
        rows=[x for x in r['records'] if x['model']==key];assert len(rows)==6
        summary.append(dict(alias=alias,model=key,pairs=6,aligned=sum(x['aligned'] for x in rows),
            hidden_region=sum(x['aligned'] and x['metrics']['goal_changes_hidden_region'] for x in rows),
            hidden_vertex=sum(x['aligned'] and x['metrics']['goal_changes_hidden_vertex'] for x in rows),
            hidden_exits=sum(x['aligned'] and x['metrics']['goal_changes_hidden_exits'] for x in rows),
            output_exits=sum(x['aligned'] and x['metrics']['goal_changes_output_exits'] for x in rows),
            source_goal_interaction=sum(x['aligned'] and x['metrics']['source_modulates_hidden_goal_contrast'] for x in rows)))
    write_json(out/'goal_context_summary.json',summary)
    write_json(out/'goal_context_verification.json',dict(all_checks_passed=True,elapsed_seconds=time.perf_counter()-started,
        replayed_probes=probes,replayed_work=work,native_mask_and_vertex_comparisons=checked,unique_models=len(models),unique_model_pairs=len(r['records']),
        source_sha256=sha(__file__),data_sha256=sha(out/'goal_context.json')))
    print('All context states/masks/metadata replayed;original probe masks and vertices match. Aliases',len(aliases),'unique models',len(models))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/capacity_growth');parser.add_argument('--verify',action='store_true');args=parser.parse_args();(verify if args.verify else run)(args.out)
