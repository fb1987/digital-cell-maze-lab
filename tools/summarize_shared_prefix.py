"""Post-search Q saved-data diagnostics only; zero candidate calls."""
import json,sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.shared_prefix_study import *

def main():
    analysis=read_compressed(OUT/'analysis.json.gz');states=read_compressed(OUT/'next_states.json.gz');choices=read_compressed(OUT/'choices.json.gz');metrics=read_compressed(OUT/'confirmation/metrics.json.gz');pools=read_compressed(OUT/'pools.json.gz')
    ancestry={i['id']:dict(parent=i['parent'],birth=i['birth'],genes=len(i['genome']['genes']),initial=True) for p in pools.values() for i in p['items']}
    condition=defaultdict(lambda:dict(parent_same_batch_comparisons=0,parent_mask_status_changes=0,parent_tick_changes=0,parent_work_changes=0,route_descendant_births=0,max_route_depth=0,max_mutation_depth=0,births=0,mutations=0,random_draws=0,train_calls=0,validation_calls=0,seconds=0.,work=0,train_positive_pairs=0,positive_ids=set(),max_genes=0))
    roots={i:(i,0) for i in ancestry}
    for e in lines(OUT/'reproduction.jsonl.gz'):
        s=condition[e['key']]
        for b in e['births']:
            i=b['item'];root,depth=roots[i['parent']] if i['parent'] is not None else (i['id'],-1);roots[i['id']]=(root,depth+1);s['max_mutation_depth']=max(s['max_mutation_depth'],depth+1)
            if root in ('mutation_depth/r0/f71/walk0/d9','mutation_depth/r0/f71/walk0/d16'):s['route_descendant_births']+=1;s['max_route_depth']=max(s['max_route_depth'],depth+1)
            ancestry[i['id']]=dict(parent=i['parent'],birth=i['birth'],genes=len(i['genome']['genes']),initial=False,events=b['events']);s['births']+=1;s['mutations']+=b['events'] is not None;s['random_draws']+=b['events'] is None;s['max_genes']=max(s['max_genes'],len(i['genome']['genes']))
    tm=read_compressed(OUT/'train/metadata.json.gz');vm=read_compressed(OUT/'validation/metadata.json.gz')
    targets={roots[state['archives']['primary']['item']['id']][0] for state in states.values()};first_observations={}
    for e in lines(OUT/'initial.jsonl.gz'):
        if e['id'] in targets and e['id']+'/initial' not in first_observations:first_observations[e['id']+'/initial']=dict(stage=e['stage'],key=e['key'],generation=e['generation'],metrics=summary(e['rows'],vm))
    batch={};batch_key=None
    def flush():
        if not batch:return
        out=condition[batch_key[0]]
        for identity,rr in batch.items():
            parent=ancestry[identity]['parent']
            if parent not in batch:continue
            pp=batch[parent];out['parent_same_batch_comparisons']+=1
            out['parent_mask_status_changes']+=any((a['mask'],a['status'])!=(b['mask'],b['status']) for a,b in zip(rr,pp))
            out['parent_tick_changes']+=any(a['steps']!=b['steps'] for a,b in zip(rr,pp))
            out['parent_work_changes']+=any((a['reads'],a['dispatches'],a['exposure_checks'])!=(b['reads'],b['dispatches'],b['exposure_checks']) for a,b in zip(rr,pp))
    for e in lines(OUT/'search_responses.jsonl.gz'):
        if e['id'] in targets and e['id']+'/'+e['stage'] not in first_observations:first_observations[e['id']+'/'+e['stage']]=dict(stage=e['stage'],key=e['key'],generation=e['generation'],metrics=summary(e['rows'],tm if e['stage']=='train' else vm))
        s=condition[e['key']];s[e['stage']+'_calls']+=len(e['rows']);s['seconds']+=e['seconds'];s['work']+=e['work']
        if e['stage']=='train':
            key=(e['key'],e['generation'])
            if key!=batch_key:flush();batch={};batch_key=key
            batch[e['id']]=e['rows']
            p=summary(e['rows'],tm)['positive'];s['train_positive_pairs']+=p
            if p:s['positive_ids'].add(e['id'])
    flush()
    for s in condition.values():s['positive_ids']=sorted(s['positive_ids'])
    selected={}
    for key,state in states.items():
        raw=state['archives']['primary']['item'];i=raw['id'];chain=[]
        while i in ancestry:
            a=ancestry[i];chain.append(dict(id=i,**a))
            if a['initial'] or a['parent'] is None:break
            i=a['parent']
        selected[key]=dict(id=raw['id'],genes=len(raw['genome']['genes']),chain=chain,root=chain[-1]['id'],mutation_steps=sum(not a['initial'] and a['parent'] is not None for a in chain),selection_generation=state['archives']['primary']['generation'])
    per_archive={alias:metrics[pid] for alias,pid in choices['aliases'].items()}
    write_json(OUT/'saved_data_diagnostics.json',dict(candidate_calls=0,first_root_observations=first_observations,conditions=dict(condition),selected=selected,archives=per_archive))
    print(json.dumps({k:dict(id=v['id'],genes=v['genes'],root=v['root'],steps=v['mutation_steps']) for k,v in selected.items()},indent=2))
if __name__=='__main__':main()
