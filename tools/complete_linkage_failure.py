"""Preserve invalid V12X attempt, its cost and all layouts; do not treat as evidence."""
from pathlib import Path
import sys,json
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.linkage_study import OUT,FIXTURES,ROOT,check_freeze,prior_check,sha,lines,load,layout_hash,exclusions,read_compressed,compressed_json,write_json

def main():
    reg=check_freeze();assert prior_check()==5706;ex=json.loads((OUT/'execution.json').read_text());assert not ex['complete']
    pools=read_compressed(OUT/'pools.json.gz');protected={r['id']:r for p in pools.values() for r in p['protected']};collisions=[];events=0
    for e in lines(OUT/'reproduction.jsonl.gz'):
        events+=1
        for b in e.get('births',[]):
            if b['item']['id'] in protected:collisions.append(dict(key=e['key'],generation=e['generation'],identity=b['item']['id'],historical=protected[b['item']['id']],newborn=b['item']))
    assert collisions and collisions[0]['generation']==0
    states=read_compressed(OUT/'latest_states.json.gz');duplicates={key:{i:n for i,n in Counter(r['id'] for r in s['population']).items() if n>1} for key,s in states.items()}
    mismatch={key:[r['id'] for r in s['population'] if len(s['gene_ids'][r['id']])!=len(r['genome']['genes'])] for key,s in states.items()}
    write_json(OUT/'failure.json',dict(status='invalidated_software_identity_collision',scientific_activation_decision=None,
        reason='New offspring IDs reused historical namespaces. At generation0 carry/0/resample/i63 collides with a protected historical genome; at generation26 carry/0/mutation/i1919 collides with protected d07. Dictionaries keyed by identity can substitute evaluations/gene maps. No efficacy or activation conclusion is admissible.',
        complete_rounds=ex['generations'],partial_round=28,logged_reproduction_events=events,collisions=collisions,latest_duplicate_identities=duplicates,latest_gene_map_length_mismatches=mismatch,
        preserved_original_source=True,original_candidate_seconds=ex['budget']['seconds'],original_wall_seconds=ex['wall_seconds'],restart_combined_candidate_cap=720,restart_candidate_allowance=720-ex['budget']['seconds']))
    hashes=exclusions()
    for folder in (FIXTURES,*sorted((OUT/'software_fixtures').glob('g*')),*sorted((OUT/'train').glob('g*'))):
        c,_,_=load(folder);hashes.update(layout_hash(o.maze) for o in c.values())
    assert len(hashes)==ex['whole_layouts'];compressed_json(OUT/'whole_layout_exclusions.json.gz',dict(count=len(hashes),hashes=sorted(hashes),scope='Includes invalid V12X fixtures and all complete/partial training layouts; excluded from restart, not scientific efficacy evidence'))
    paths={ROOT/name for group in ('sources','inputs') for name in reg[group]}
    paths.update(p for folder in (OUT,FIXTURES) for p in folder.rglob('*') if p.is_file() and p.suffix!='.log')
    paths.add(ROOT/'tools/complete_linkage_failure.py');paths.add(ROOT/'results/linkage_pilot.md')
    write_json(OUT/'completion.json',dict(status='invalidated_software_identity_collision',audit_passed=False,
        source_and_artifact_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},prior_hash_entries=5706,whole_layouts_through_invalid_X=len(hashes),scientific_result_usable=False,original_source_preserved=True))
    print(dict(collisions=[(c['key'],c['generation'],c['identity']) for c in collisions],sealed_entries=len(paths),future_prior_entries=5706+len(paths),excluded_layouts=len(hashes)))
if __name__=='__main__':main()
