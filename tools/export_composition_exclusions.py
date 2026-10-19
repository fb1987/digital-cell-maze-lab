"""Export every prior/S whole-layout hash, independently matching the S audit."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.composition_data import OUT,FIXTURES,ROOT,exclusions,read_compressed,compressed_json,AccessData
from maze_evolution.routing_transfer import sha


def main():
    audit=json.loads((OUT/'audit.json').read_text());assert audit['passed']
    prior=exclusions();old=AccessData(0,prior);assert len(old.layouts)==191784
    paths=[FIXTURES/'mazes.json.gz',OUT/'schedule_fixtures/mazes.json.gz',
           OUT/'validation/mazes.json.gz',*sorted((OUT/'train').glob('g*/mazes.json.gz')),
           OUT/'confirmation/mazes.json.gz']
    sources={}
    for p in paths:
        rows=read_compressed(p);prior.extend(rows)
        sources[str(p.relative_to(ROOT))]=dict(sha256=sha(p),inputs=len(rows))
    all_data=AccessData(0,prior)
    assert len(all_data.layouts)==audit['whole_layouts']
    compressed_json(OUT/'whole_layout_exclusions.json.gz',dict(
        scope='All whole layouts through V12S, including fixtures and unqueried poses',
        algorithm='maze_evolution.goal_data.layout_hash; endpoints excluded',
        count=len(all_data.layouts),hashes=sorted(all_data.layouts)))
    (OUT/'exclusion_sources.json').write_text(json.dumps(dict(
        through_R_count=len(old.layouts),through_R_supplier='maze_evolution.composition_data.exclusions',
        through_R_supplier_sha256=sha(ROOT/'maze_evolution/composition_data.py'),
        added_manifests=sources,through_S_count=len(all_data.layouts)),indent=2)+'\n')
    print(dict(through_R=len(old.layouts),through_S=len(all_data.layouts),added_manifests=len(paths)))


if __name__=='__main__':main()
