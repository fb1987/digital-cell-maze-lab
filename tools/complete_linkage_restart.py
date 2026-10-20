"""Seal the audited activation pilot; no inference or budget extension."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.linkage_restart_study import check_freeze,prior_check,sha,OUT,FIXTURES,ROOT,exclusions,load,layout_hash,compressed_json,write_json

def main():
    reg=check_freeze();prior=prior_check();assert prior==6166 and not (OUT/'completion.json').exists()
    audit=json.loads((OUT/'audit.json').read_text());ex=json.loads((OUT/'execution.json').read_text());assert audit['passed'] and ex['complete']
    assert (ROOT/'results/linkage_restart.md').exists() and (OUT/'activation.png').exists()
    hashes=exclusions();sources={}
    for folder in (FIXTURES,*sorted((OUT/'software_fixtures').glob('g*')),*sorted((OUT/'train').glob('g*'))):
        c,_,_=load(folder);hashes.update(layout_hash(o.maze) for o in c.values());sources[str((folder/'mazes.json.gz').relative_to(ROOT))]=sha(folder/'mazes.json.gz')
    assert len(hashes)==audit['whole_layouts']==ex['whole_layouts']
    compressed_json(OUT/'whole_layout_exclusions.json.gz',dict(scope='All whole layouts through V12X-R1, including every generated unqueried fixture/software/training variant and pose',count=len(hashes),hashes=sorted(hashes)))
    write_json(OUT/'exclusion_sources.json',dict(through_invalid_X_count=253316,through_invalid_X_hashset_sha256=sha(ROOT/'results/linkage_pilot/whole_layout_exclusions.json.gz'),added_manifests=sources,through_restart_count=len(hashes)))
    paths={ROOT/name for group in ('sources','inputs') for name in reg[group]}
    paths.update(p for folder in (OUT,FIXTURES) for p in folder.rglob('*') if p.is_file() and p.suffix!='.log')
    paths.update((ROOT/'tools').glob('*linkage_restart*.py'));paths.add(ROOT/'results/linkage_restart.md')
    generation=json.loads((OUT/'train/g0000/generation.json').read_text());a=json.loads((OUT/'analysis.json').read_text())
    write_json(OUT/'completion.json',dict(status='complete_and_audited',source_and_artifact_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},prior_hash_entries=prior,preregistration_revision=generation['revision'],whole_layouts_through_restart=len(hashes),main_candidate_calls=ex['budget']['calls'],activation_gate_passed=a['longer_search_authorized_by_gate'],efficacy_study_launched=False,scientific_source_repair_after_registration=False,original_attempt_invalidated=True,original_failed_candidate_seconds=297.712951528898,combined_candidate_seconds=297.712951528898+ex['budget']['seconds'],combined_wall_seconds=512.7068764159922+ex['wall_seconds'],mutable_handoffs_excluded=['AGENTS.md','README.md','docs/LINKAGE_RESTART_PROGRESS.md']))
    print(dict(hash_entries=len(paths),future_prior_entries=prior+len(paths),layouts=len(hashes)))
if __name__=='__main__':main()
