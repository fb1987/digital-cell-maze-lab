"""Seal audited V12W artifacts and complete layout exclusions; no inference."""
from pathlib import Path
import sys,json,subprocess
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.compatibility_map_study import check_freeze,prior_check,sha
from maze_evolution.compatibility_map_data import OUT,FIXTURES,ROOT,exclusions,load,layout_hash,compressed_json
from maze_evolution.foundation_calibration import write_json

def main():
    reg=check_freeze();prior=prior_check();assert prior==5447 and not (OUT/'completion.json').exists()
    audit=json.loads((OUT/'audit.json').read_text());assert audit['passed']
    assert (ROOT/'results/compatibility_map.md').exists() and (OUT/'compatibility.png').exists()
    hashes=exclusions();sources={}
    for folder in (FIXTURES,OUT/'confirmation'):
        c,_,_=load(folder);hashes.update(layout_hash(o.maze) for o in c.values())
        path=folder/'mazes.json.gz';sources[str(path.relative_to(ROOT))]=sha(path)
    generation=json.loads((OUT/'confirmation/generation.json').read_text())
    assert len(hashes)==audit['counts']['whole_layouts']==generation['whole_layouts']
    compressed_json(OUT/'whole_layout_exclusions.json.gz',dict(scope='All whole layouts through V12W, including unqueried fixture/final variants and all poses',count=len(hashes),hashes=sorted(hashes),algorithm='maze_evolution.goal_data.layout_hash; endpoints excluded'))
    write_json(OUT/'exclusion_sources.json',dict(through_V_count=243540,through_V_hashset_sha256=sha(ROOT/'results/causal_dissection/whole_layout_exclusions.json.gz'),added_manifests=sources,through_W_count=len(hashes)))
    paths={ROOT/name for group in ('sources','inputs') for name in reg[group]}
    paths.update(p for base in (OUT,FIXTURES) for p in base.rglob('*') if p.is_file() and p.suffix!='.log')
    paths.update((ROOT/'tools').glob('*compatibility_map*.py'));paths.add(ROOT/'results/compatibility_map.md')
    revision=generation['revision']
    for name in ('panel.json.gz','preregistration.json'):assert subprocess.check_output(['git','show',f'{revision}:results/compatibility_map/{name}'])==(OUT/name).read_bytes()
    execution=json.loads((OUT/'confirmation/execution.json').read_text());assert execution['complete']
    write_json(OUT/'completion.json',dict(status='complete_and_audited',preregistration_revision=revision,
        source_and_artifact_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},prior_hash_entries=prior,
        audit_passed=True,main_candidate_calls=execution['budget']['calls'],whole_layouts_through_W=len(hashes),next_experiment_launched=False,
        mutable_handoffs_excluded=['AGENTS.md','README.md','docs/COMPATIBILITY_MAP_PROGRESS.md'],scientific_source_repair_after_registration=False))
    print(dict(hash_entries=len(paths),future_prior_entries=prior+len(paths),layouts=len(hashes)))

if __name__=='__main__':main()
