"""Post-freeze explanation from saved genomes and rasters only; no inference."""
import json,gzip,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution.fork_data import load
from maze_evolution.fork_study import lines
from maze_evolution.foundation_study import read_compressed
from maze_evolution.growth import Individual,replay_mutation
OUT=ROOT/'results/fork_pressure'


def run():
    cases,_=load(OUT/'confirmation');selection=read_compressed(OUT/'frozen_selections.json.gz')
    meta=read_compressed(OUT/'confirmation/models.json.gz');records={r['model']:r['rows'] for r in lines(OUT/'confirmation/outputs.jsonl.gz')}
    initial=read_compressed(OUT/'initial_states.json.gz');founders={i['id']:i for s in initial for i in s['population']+s['protected']};segments={};result={}
    def individual(identity):
        if identity in founders:return dict(**founders[identity],events=None)
        serial=int(identity.rsplit('/i',1)[1]);generation=serial//72
        if generation not in segments:segments[generation]={r['id']:r for r in lines(OUT/f'segments/{generation:04d}.lineage.jsonl.gz')}
        return segments[generation][identity]
    for key,s in selection.items():
        alias=key+'/archives/pair';model=meta['aliases'][alias];rows=records[model];item=s['archives']['pair']['item']
        chain=[];child=individual(item['id'])
        while True:
            chain.append({k:child[k] for k in ('id','parent','birth','events')})
            if child['id'] in founders or child['parent'] is None:break
            parent=individual(child['parent']);assert replay_mutation(Individual.load(parent).genome,child['events'],256)==Individual.load(child).genome
            child=parent
        successes=[]
        for i in range(0,len(rows),2):
            pair=rows[i:i+2]
            if not pair[0]['fork'] or not pair[0]['pair_optimal']:continue
            successes.append(dict(cases=[r['case'] for r in pair],lengths=[len(cases[r['case']].path)-1 for r in pair],prefix=cases[pair[0]['case']]._foundation_label['distance'],steps=[r['steps'] for r in pair],family=cases[pair[0]['case']].maze.family))
        result[key]=dict(model=model,selected_id=item['id'],selected_birth=item['birth'],selection_generation=s['archives']['pair']['generation'],gene_count=len(item['genome']['genes']),
            ancestry_steps=len(chain)-1,root_kind='prepared_population_or_anchor' if chain[-1]['id'] in founders else 'new_random_immigrant',ancestry=chain,completed_pairs=successes,
            lengths=dict(Counter(str(tuple(p['lengths'])) for p in successes)),families=dict(Counter(p['family'] for p in successes)),stage2_lengths=[p['lengths'] for p in successes if '/stage2/' in p['cases'][0]],
            max_array_bytes=max(r['array_bytes'] for r in rows),normal_work=sum(r['reads']+r['dispatches'] for r in rows),normal_nonlocal_reads=sum(sum(r['range_reads'][1:]) for r in rows))
    (OUT/'saved_evidence_diagnostics.json').write_text(json.dumps(dict(scope='Post-hoc saved-evidence explanation; no extra inference or reselection',conditions=result),indent=2)+'\n')
    for k,v in result.items():
        if v['completed_pairs']:print(k,v['selected_id'],'edits',v['ancestry_steps'],'root',v['root_kind'],'families',v['families'],'lengths',v['lengths'])

if __name__=='__main__':run()
