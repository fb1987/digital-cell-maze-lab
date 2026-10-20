"""Post-hoc diagnosis of saved normal rasters; no new inference or reselection."""
from pathlib import Path
import sys
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.selectivity_study import OUT,load,lines,read_compressed,compressed_json

def main():
    cases,_,meta=load(OUT/'confirmation');choices=read_compressed(OUT/'choices.json.gz');models={};metrics=read_compressed(OUT/'confirmation/metrics.json.gz')
    for e in lines(OUT/'confirmation/responses.jsonl.gz'):
        groups={}
        for row in e['rows']:
            q=meta[row['case']];o=cases[row['case']]
            if q['family']=='paired':group='prefix'+str(q['prefix'])
            elif q['family'].startswith('ordinary_') and o.path:group='ordinary_reachable'
            else:continue
            c=groups.setdefault(group,Counter());c['inputs']+=1
            if row['optimal']:c['shortest']+=1;c['shortest_edges_'+str(len(o.path)-1)]+=1;continue
            if row['status']!='emitted':c['not_emitted']+=1;continue
            bits=int.from_bytes(bytes.fromhex(row['mask']),'little');lit={k for k in range(len(o.maze.cells)) if (bits>>k)&1}
            route=set(o.path);extra=len(lit-route);missing=len(route-lit)
            if missing==0:
                assert extra>0
                c['complete_route_with_extras']+=1;c['excess_cells_on_complete_routes']+=extra
            elif not lit:c['empty']+=1
            else:c['incomplete_route']+=1
        for group,c in groups.items():
            assert sum(c.get(k,0) for k in ('shortest','not_emitted','complete_route_with_extras','empty','incomplete_route'))==c['inputs']
        m=metrics[e['key']]
        assert groups['ordinary_reachable']['shortest']==m['ordinary']
        assert sum(c['shortest'] for k,c in groups.items() if k.startswith('prefix'))==m['optimal']-m['corridors']-m['ordinary']
        models[e['key']]={k:dict(v) for k,v in groups.items()}
    primaries={a:models[p] for a,p in choices['aliases'].items() if a.endswith('/primary')}
    compressed_json(OUT/'saved_raster_diagnostics.json.gz',dict(post_hoc=True,new_candidate_calls=0,models=models,primary_aliases=primaries,preserved_anchors={a:dict(identity=choices['items'][a]['id'],metrics=metrics[pid]) for a,pid in choices['aliases'].items() if a.startswith('anchor/') and a!='anchor/intact'}))
    for a,g in primaries.items():
        if '/frozen/' not in a:print(a,{k:v for k,v in g.items() if k in ('prefix1','prefix2')})
if __name__=='__main__':main()
