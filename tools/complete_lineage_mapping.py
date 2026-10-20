"""Seal audited V12U artifacts and all constructed layout exclusions."""
from pathlib import Path
import sys,json,subprocess
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.lineage_mapping_study import check_freeze,prior_check,sha
from maze_evolution.lineage_mapping_data import OUT,FIXTURES,ROOT,exclusions,load,layout_hash,compressed_json
from maze_evolution.foundation_calibration import write_json

def main():
    reg=check_freeze();prior=prior_check();assert prior==4937 and not (OUT/'completion.json').exists()
    audit=json.loads((OUT/'audit.json').read_text());assert audit['passed']
    assert (ROOT/'results/lineage_mapping.md').exists() and (OUT/'normal_outputs.png').exists()
    hashes=exclusions();sources={}
    for folder in (FIXTURES,OUT/'confirmation'):
        c,_,_=load(folder);hashes.update(layout_hash(o.maze) for o in c.values())
        path=folder/'mazes.json.gz';sources[str(path.relative_to(ROOT))]=sha(path)
    assert len(hashes)==audit['counts']['whole_layouts']==233432
    compressed_json(OUT/'whole_layout_exclusions.json.gz',dict(scope='All whole layouts through V12U including all fixture/final poses and unqueried variants',count=len(hashes),hashes=sorted(hashes),algorithm='maze_evolution.goal_data.layout_hash; endpoints excluded'))
    write_json(OUT/'exclusion_sources.json',dict(through_T_count=225592,through_T_hashset_sha256=sha(ROOT/'results/routing_mechanism/whole_layout_exclusions.json.gz'),added_manifests=sources,through_U_count=len(hashes)))
    paths={ROOT/name for group in ('sources','inputs') for name in reg[group]}
    paths.update(p for base in (OUT,FIXTURES) for p in base.rglob('*') if p.is_file() and p.suffix!='.log')
    paths.update((ROOT/'tools').glob('*lineage_mapping*.py'));paths.add(ROOT/'results/lineage_mapping.md')
    revision=json.loads((OUT/'confirmation/generation.json').read_text())['revision']
    for name in ('panel.json.gz','preregistration.json'):assert subprocess.check_output(['git','show',f'{revision}:results/lineage_mapping/{name}'])==(OUT/name).read_bytes()
    execution=json.loads((OUT/'confirmation/execution.json').read_text());assert execution['complete']
    write_json(OUT/'completion.json',dict(status='complete_and_audited',preregistration_revision=revision,
        source_and_artifact_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},prior_hash_entries=prior,
        audit_passed=True,main_candidate_calls=execution['budget']['calls'],whole_layouts_through_U=len(hashes),next_experiment_launched=False,
        mutable_handoffs_excluded=['AGENTS.md','README.md','docs/LINEAGE_MAPPING_PROGRESS.md'],scientific_source_repair_after_registration=False))
    print(dict(hash_entries=len(paths),future_prior_entries=prior+len(paths),layouts=len(hashes)))

if __name__=='__main__':main()
