"""Read-only V12I saved-raster diagnostics; never runs or reselects a genome."""
from collections import Counter,defaultdict
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution.foundation_calibration import write_json
from maze_evolution.foundation_study import read_compressed,compressed_json
from maze_evolution.routing_transfer import lines
from maze_evolution.validation_breadth_data import OUT,FAMILIES,load


def run():
    pool=read_compressed(OUT/'pool.json.gz'); chosen=read_compressed(OUT/'selections.json.gz')
    cases,contexts,metadata=load(OUT/'confirmation')
    pose_lookup={(c['id'],p['symmetry']):p for c in contexts for p in c['poses']}
    models={}; certificates=[]
    for packet in lines(OUT/'confirmation/outputs.jsonl.gz'):
        mk=packet['model']; rows=packet['rows']; grouped=defaultdict(list)
        for row in rows:
            m=metadata[row['case']]
            if m['family'] in FAMILIES:
                grouped[m['base'],m['symmetry'],m['family']].append(row)
        successful=[]
        for (base,symmetry,family),pair in grouped.items():
            if all(r['optimal'] for r in pair):
                pose=pose_lookup[base,symmetry]; lengths=[len(p)-1 for p in pose['meta']['paths']]
                row=dict(model=mk,base=base,symmetry=symmetry,family=family,
                    cases=[r['case'] for r in pair],shortest_edges=lengths,
                    prefix_edges=pose['meta']['lengths'][0],tail_edges=pose['meta']['lengths'][1:],
                    alternative_edges=[len(p)-1 for p in pose['meta']['alternatives']] if family=='alternate_cycle' else None)
                successful.append(row); certificates.append(row)
        pairs_by_base=Counter((r['family'],r['base']) for r in successful)
        all_eight={base for (family,base),n in pairs_by_base.items() if n==8}
        all_graphs_all_eight={base for base in all_eight if all(pairs_by_base[f,base]==8 for f in FAMILIES)}
        normals=[r for r in rows if r['optimal'] and metadata[r['case']]['family'] in FAMILIES]
        models[mk]=dict(genes=len(pool['models'][mk]['item']['genome']['genes']) if mk in pool['models'] else None,
            pairs=len(successful),max_paired_route_edges=max((max(r['shortest_edges']) for r in successful),default=None),
            max_paired_prefix_edges=max((r['prefix_edges'] for r in successful),default=None),
            max_individual_branch_edges=max((len(cases[r['case']].path)-1 for r in normals),default=None),
            individual_branch_legal_not_shortest=sum(r['valid'] and not r['optimal'] and metadata[r['case']]['family'] in FAMILIES for r in rows),
            all_eight_contexts_any_family=sorted(all_eight),all_eight_contexts_all_families=sorted(all_graphs_all_eight),
            paired_distances=dict(sorted(Counter('/'.join(map(str,sorted(r['shortest_edges'])) ) for r in successful).items())),
            cycle_contexts=sorted({r['base'] for r in successful if r['family']=='alternate_cycle'}),
            cycles_by_prefix=dict(Counter(str(r['prefix_edges']) for r in successful if r['family']=='alternate_cycle')),
            no_path=sum(r['no_path'] for r in rows),false_no_path=sum(r['reachable'] and r['status']=='no_path' for r in rows),
            max_array_bytes=max(r['array_bytes'] for r in rows),
            input_raster_bytes=sum(len(cases[r['case']].maze.cells) for r in rows),
            returned_raster_bytes=sum(len(cases[r['case']].maze.cells) for r in rows),
            packed_saved_raster_bytes=sum(len(bytes.fromhex(r['mask'])) for r in rows),
            nonlocal_reads=sum(sum(r['range_reads'][1:]) for r in rows),
            active_dispatches=sum(r['active'] for r in rows),
            total_dispatches=sum(r['dispatches'] for r in rows),
            statuses=dict(Counter(r['status'] for r in rows)))
    aliases={}
    for key,s in chosen.items():
        aliases[key]={}
        for arm,c in s.items():
            aliases[key][arm]=dict(model=c['model'],in_G_initial_pool=any(m['initial'] for m in c['aliases']),
                identities=[m['id'] for m in c['aliases']],births=[m['birth'] for m in c['aliases']],
                genes=models[c['model']]['genes'])
    result=dict(models=models,selections=aliases,
        scope='Descriptive extraction from the frozen normal final rasters only. No new candidate inference or mechanism intervention.',
        physical_random_models=len([m for m in models if not m.startswith('known/')]),
        paired_successful_random_models=len([m for m,v in models.items() if not m.startswith('known/') and v['pairs']>0]))
    write_json(OUT/'saved_raster_diagnostics.json',result)
    compressed_json(OUT/'successful_pair_certificates.json.gz',certificates)
    print(json.dumps(dict(physical_random_models=result['physical_random_models'],successful_random_models=result['paired_successful_random_models'],
        models={m:{k:v[k] for k in ('genes','pairs','max_paired_route_edges','max_paired_prefix_edges')} for m,v in models.items() if not m.startswith('known/')}),indent=2))


if __name__=='__main__':run()
