"""Saved V12K selections, provenance and matched tables, without inference."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution.robustness_data import OUT
from maze_evolution.foundation_study import read_compressed
from maze_evolution.routing_transfer import lines
from maze_evolution.foundation_calibration import write_json


def run():
    a=json.loads((OUT/'analysis.json').read_text());aliases=json.loads((OUT/'final/aliases.json').read_text())
    sels=read_compressed(OUT/'frozen_selections.json.gz');states=read_compressed(OUT/'initial_states.json.gz')
    items={i['id']:i for s in states for i in s['population']+s['protected']}
    initial=set(items);events={}
    for path in sorted((OUT/'segments').glob('*.lineage.jsonl.gz')):
        for r in lines(path):items[r['id']]={k:r[k] for k in ('id','genome','parent','birth')};events[r['id']]=r['events']
    lineage={};table={}
    for key,s in sels.items():
        for stage in ('archives','frozen'):
            for archive in ('context','pair'):
                alias=f'{key}/{stage}/{archive}';item=s[stage][archive]['item'];steps=[];current=item
                while current['id'] not in initial and current['parent'] is not None:
                    steps.append(dict(id=current['id'],parent=current['parent'],birth=current['birth'],events=events[current['id']]))
                    current=items[current['parent']]
                lineage[alias]=dict(selected_id=item['id'],selected_birth=item['birth'],genes=len(item['genome']['genes']),
                    selected_generation=s[stage][archive]['generation'],new_mutation_steps=len(steps),entry=current,
                    entry_was_initial=current['id'] in initial,steps=steps)
                stats=a['results']['final'][aliases[alias]+'|normal']
                table[alias]=dict(id=item['id'],birth=item['birth'],genes=len(item['genome']['genes']),new_mutation_steps=len(steps),
                    pairs=stats['pairs'],contexts=stats['contexts'],corridors=stats['corridor'],far_pairs=stats['far_pairs'],
                    optimal=stats['optimal'],no_path=stats['no_path'],false_no_path=stats['false_no_path'])
    write_json(OUT/'selected_ancestry.json',lineage);write_json(OUT/'selection_table.json',table)
    for origin in ('carry','fresh'):
        for topology in ('local','evolved'):
            print(origin,topology)
            for policy,method,stage in [('pair','evolution','archives'),('context','evolution','archives'),('pair','evolution','frozen')]+([('pair','resample','archives')] if origin=='fresh' else []):
                rs=[table[f'robustness/{origin}/{topology}/{policy}/{method}/{r}/{stage}/context'] for r in range(3)]
                print(policy,method,stage,'pairs',[r['pairs'] for r in rs],'full',[r['contexts'] for r in rs],'corr',[r['corridors'] for r in rs],'far',[r['far_pairs'] for r in rs],'steps',[r['new_mutation_steps'] for r in rs])
    final={s['key']:s for s in read_compressed(OUT/'checkpoint.latest.json.gz')['states']}
    differences=[]
    for origin in ('carry','fresh'):
        for topology in ('local','evolved'):
            for rep in range(3):
                x=final[f'robustness/{origin}/{topology}/pair/evolution/{rep}'];y=final[f'robustness/{origin}/{topology}/context/evolution/{rep}']
                diff=[g for g,(u,v) in enumerate(zip(x['history'],y['history'])) if u['population_sha256']!=v['population_sha256']]
                differences.append(dict(origin=origin,topology=topology,replicate=rep,different_rounds=len(diff),first_difference=diff[0] if diff else None,
                    pair_top_sets_differ=sum(h['top_sets_differ'] for h in x['history']),context_top_sets_differ=sum(h['top_sets_differ'] for h in y['history']),
                    final_rng_equal=x['rng_state']==y['rng_state']))
    write_json(OUT/'pressure_differences.json',differences)
    print('Pressure differences',differences)
    print('Unique final models',len(read_compressed(OUT/'final/models.json.gz')))

if __name__=='__main__':run()
