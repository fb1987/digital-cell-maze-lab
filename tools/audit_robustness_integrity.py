"""Supplemental V12K completeness/provenance audit; no candidate calls.

Added after registration to independently verify corpus regeneration, every
expected response identity, budgets and final aliases. Does not change protocol.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from collections import Counter,defaultdict
import json,random,time
from maze_evolution.robustness_data import *
from maze_evolution.robustness_study import check_freeze
from maze_evolution.foundation_calibration import write_json
from maze_evolution.growth import Individual,random_genome
from maze_evolution.routing_transfer import lines,canonical,sha


def run():
    started=time.perf_counter();check_freeze();counts=Counter()
    previous=exclusions();fixture=RobustnessData(FIXTURE_SEED,previous);fixtures(fixture)
    assert canonical(manifest(fixture.cache.values()))==read_compressed(FIXTURES/'mazes.json.gz')
    previous+=read_compressed(FIXTURES/'mazes.json.gz')+read_compressed(FIXTURES/'geometry_test_mazes.json.gz')
    for scope in ('diagnostic','search','final'):
        path=OUT/scope
        d=RobustnessData(SEED if scope=='search' else seed_for(SEED,scope,0,0),previous)
        if scope=='search':
            ids={str(r):validation(d,r) for r in range(3)}
            assert ids==json.loads((path/'validation_ids.json').read_text())
            summary=json.loads((OUT/'search_summary.json').read_text())
            for g in range(summary['rounds']):
                b={str(r):batch(d,r,g) for r in range(3)}
                assert b==json.loads((path/f'batch_{g:04d}.json').read_text())
            assert not (OUT/'partial_states.json.gz').exists(),'Partial round requires separate exclusion replay'
        else:confirmation(d,scope)
        assert canonical(manifest(d.cache.values()))==read_compressed(path/'mazes.json.gz')
        assert canonical(d.contexts)==read_compressed(path/'contexts.json.gz')
        assert canonical(d.metadata)==read_compressed(path/'metadata.json.gz')
        counts['regenerated_cases']+=len(d.cache);previous+=read_compressed(path/'mazes.json.gz')
    initial=read_compressed(OUT/'initial_states.json.gz');bykey={s['key']:s for s in initial}
    donor={s['key']:s for s in read_compressed(ROOT/'results/fork_pressure/checkpoint.latest.json.gz')['states']}
    prov=read_compressed(OUT/'parent_provenance.json.gz')
    for s in initial:
        c=s['config'];key=f"{c['origin']}/{c['topology']}/{c['replicate']}"
        if c['origin']=='carry':
            p=prov[key];old=donor[p['donor_key']]
            assert p['donor_generation']==113 and p['unmodified_population']==old['population']
            assert s['rng_state']==old['rng_state'] and s['protected']==p['protected']
            population=old['population'].copy();positions=[i for i,x in enumerate(population) if x['id'] not in {a['id'] for a in s['protected']}]
            for k,item in zip(reversed(positions),p['added_anchors']):population[k]=item
            assert population==s['population']
        else:
            rng=random.Random(seed_for(SEED,'founders',c['replicate'],0))
            pop=[Individual(f"robustness_founder/{c['topology']}/{c['replicate']}/i{k}",random_genome(rng,True),None,0).save() for k in range(96)]
            assert canonical(pop)==s['population'] and canonical(rng.getstate())==s['rng_state']
        assert len(s['population'])==96 and len(s['protected'])<=18
        counts['initial_states']+=1
    final=read_compressed(OUT/'checkpoint.latest.json.gz');summary=json.loads((OUT/'search_summary.json').read_text())
    assert final['rounds']==summary['rounds'] and summary['elapsed_seconds']<=720
    assert summary['budget']['calls']==summary['physical_calls_completed']
    assert summary['budget']['work']==summary['work_completed']
    assert summary['budget']['calls']<=4000000
    val=json.loads((OUT/'search/validation_ids.json').read_text())
    initial_seen=defaultdict(set)
    for rec in lines(OUT/'initial_evaluations.jsonl.gz'):
        key=rec['condition'];assert rec['id'] not in initial_seen[key];initial_seen[key].add(rec['id'])
        assert [r['case'] for r in rec['cases']]==val[str(bykey[key]['config']['replicate'])]
    assert len(initial_seen)==12
    for key,ids in initial_seen.items():assert ids=={i['id'] for i in bykey[key]['population']}
    for segment in final['segments']:
        g=segment['generation'];seen=defaultdict(list)
        for r in lines(OUT/segment['files'][1]):seen[(r['condition'],r['split'])].append(r['id'])
        for key in bykey:
            assert len(seen[(key,'train')])==len(set(seen[(key,'train')]))==96
            assert len(seen[(key,'validation')])==(4 if g%8==0 else 0)
        counts['matched_rounds']+=1
    for s in final['states']:
        assert s['generation']==summary['rounds'] and len(s['population'])==96
        assert {i['id'] for i in s['protected']}<={i['id'] for i in s['population']}
        assert all(len(i['genome']['genes'])<=256 for i in s['population'])
    panel=read_compressed(OUT/'panel.json.gz')
    assert panel==read_compressed(ROOT/'results/junction_distance/panel.json.gz')
    for scope,path in [('fixtures',FIXTURES),('diagnostic',OUT/'diagnostic'),('final',OUT/'final')]:
        cases,_,_=load(path);models=panel if scope=='fixtures' else read_compressed(path/'models.json.gz')
        seen=set();work=0
        for rec in lines(path/'responses.jsonl.gz'):
            key=(rec['model'],rec['mode'],rec['row']['case']);assert key not in seen;seen.add(key)
            work+=rec['row']['reads']+rec['row']['dispatches']
        modes=('normal','nonlocal_off') if scope=='diagnostic' else ('normal',)
        assert seen=={(n,m,cid) for n in models for m in modes for cid in cases}
        counts['response_coverage']+=len(seen)
        if scope!='fixtures':
            execution=json.loads((path/'execution.json').read_text());b=execution['budget']
            assert execution['complete'] and b['calls']==len(seen)==execution['planned_calls'] and b['work']==work and b['seconds']<=b['cap_seconds']
            baseline_seen=[(r['model'],r['row']['case']) for r in lines(path/'baselines.jsonl.gz')]
            assert len(baseline_seen)==len(set(baseline_seen))==3*len(cases)
            assert set(baseline_seen)=={(n,cid) for n in ('compiled_bfs','compiled_astar','wave_bit') for cid in cases}
    aliases=json.loads((OUT/'final/aliases.json').read_text());models=read_compressed(OUT/'final/models.json.gz')
    for key,s in read_compressed(OUT/'frozen_selections.json.gz').items():
        for stage in ('archives','frozen'):
            for a in ('context','pair'):
                physical=models[aliases[f'{key}/{stage}/{a}']]
                assert physical['topology']==s['config']['topology']
                assert Individual.load(physical['item']).genome==Individual.load(s[stage][a]['item']).genome
                counts['selection_aliases']+=1
    write_json(OUT/'integrity_verification.json',dict(passed=True,counts=dict(counts),seconds=time.perf_counter()-started,
        supplemental_source_sha256=sha(Path(__file__))))
    print(json.dumps(dict(passed=True,counts=dict(counts)),indent=2))

if __name__=='__main__':run()
