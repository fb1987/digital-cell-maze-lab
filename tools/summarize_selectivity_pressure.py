"""Descriptive V13B summaries after frozen final evaluation; never used for selection."""
import sys,json,re,gzip
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.selectivity_study import *

def main():
    ex=json.loads((OUT/'search_execution.json').read_text());assert ex['complete']
    states=read_compressed(OUT/'next_states.json.gz');choices=read_compressed(OUT/'choices.json.gz')
    metrics=read_compressed(OUT/'confirmation/metrics.json.gz');a=read_compressed(OUT/'analysis.json.gz')
    parents={};series={k:[] for k in states};mutations=0;births=0
    for e in lines(OUT/'reproduction.jsonl.gz'):
        series[e['key']].append(dict(generation=e['generation']+1,**e['families']))
        for b in e['births']:
            parents[b['item']['id']]=b['parents'][0] if b['parents'] else None
            mutations+=b['mutation'] is not None;births+=1
    def ancestry(identity):
        depth=0;chain=[]
        while identity in parents:
            chain.append(identity)
            if parents[identity] is None:break
            depth+=1;identity=parents[identity]
        return dict(pilot_mutation_steps=depth,pilot_root=identity,pilot_chain=chain)
    counts={}
    for key,s in states.items():
        p=s['archives']['primary'];pid=choices['aliases'][key+'/primary'];m=metrics[pid]
        counts[key]=dict(identity=p['item']['id'],genes=len(p['item']['genome']['genes']),birth=p['item']['birth'],nomination=p['generation'],metrics=m,**ancestry(p['item']['id']))
    stages={n:dict(records=0,calls=0,seconds=0.,work=0) for n in ('train','validation')};by_condition={k:{n:dict(calls=0,seconds=0.,work=0) for n in stages} for k in states}
    pattern=re.compile(r'"stage":"([^"]+)".*?"seconds":([0-9.eE+\-]+),"work":([0-9]+)')
    for path in sorted((OUT/'train').glob('g*/responses.jsonl.gz')):
        with gzip.open(path,'rt') as f:
            for line in f:
                match=pattern.search(line[:700]);assert match
                stage,secs,work=match.groups();v=stages[stage];v['records']+=1
                v['calls']+=12 if stage=='train' else 340;v['seconds']+=float(secs);v['work']+=int(work)
                key=re.search(r'"key":"([^"]+)"',line[:700]).group(1);bc=by_condition[key][stage]
                bc['calls']+=12 if stage=='train' else 340;bc['seconds']+=float(secs);bc['work']+=int(work)
    assert sum(v['calls'] for v in stages.values())+ex['initial_budget']['calls']==ex['budget']['calls']
    assert abs(sum(v['seconds'] for v in stages.values())+ex['initial_budget']['seconds']-ex['budget']['seconds'])<1e-5
    packet=dict(search_stages=stages,condition_stages=by_condition,search=ex,confirmation=json.loads((OUT/'confirmation/execution.json').read_text()),primaries=counts,family_trajectories=series,total_births=births,total_mutations=mutations,replicated=a['replicated'],physical_models=len(choices['models']),aliases=len(choices['aliases']))
    compressed_json(OUT/'descriptive_summary.json.gz',packet)
    for origin in ('carry','fresh'):
        for arm in ARMS:
            mm=[counts[f'{origin}/{r}/{arm}']['metrics'] for r in range(3)]
            print(origin,arm,{n:[m[n] for m in mm] for n in ('upstream','p2','prefix4','prefix8','cycle','pairs','ordinary','corridors','no_path','false_no_path')})
    course={}
    for path in [OUT/'initial_states.json.gz',*sorted((OUT/'checkpoints').glob('g*.json.gz'))]:
        snapshot=read_compressed(path);generation=next(iter(snapshot.values()))['generation']
        course[generation]={k:{n:v['archives']['primary']['metrics'][n] for n in ('upstream','p2','pairs')} for k,v in snapshot.items()}
    write_json(OUT/'validation_time_course.json',dict(selection_data_only=True,independent_tests=False,primary_complete_pairs=course))
    print('search',ex['generations'],ex['wall_seconds'],'births',births,'mutations',mutations)

if __name__=='__main__':main()
