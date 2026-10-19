"""V12I fixed-genome, equal-input validation breadth comparison.

Commands deliberately separate pool freeze, selection and final generation.
The final command verifies the selected artifacts exist in pushed Git history.
"""
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
import gzip
import hashlib
from importlib.metadata import version
import json
import platform
import resource
import subprocess
import time

from .baselines import baseline
from .datasets import manifest
from .foundation_calibration import ROOT, LIMITS, controls, write_json
from .foundation_data import FoundationData
from .foundation_pair_confirm import normal_row
from .foundation_study import compressed_json, read_compressed
from .growth import Individual
from .growth_runtime import Organism
from .routing_transfer import canonical, lines, logrow, sha
from .validation_breadth_data import (OUT, FIXTURES, SEED, FIXTURE_SEED, FAMILIES,
    BreadthData, exclusions, load, validation, final as final_data)

CAP_SECONDS = 720.
MAX_CALLS = 1_200_000
G = ROOT/'results/fork_pressure'


def inventory():
    """Reconstruct membership from G history without reading any final score."""
    initial = read_compressed(G/'initial_states.json.gz')
    states = {s['key']: s for s in read_compressed(G/'checkpoint.latest.json.gz')['states']}
    requests = {}; items = {}; files = [G/'initial_states.json.gz', G/'checkpoint.latest.json.gz']
    for s in initial:
        nominees = defaultdict(list)
        for h in states[s['key']]['history']:
            for identity in h['nominees']:
                nominees[identity].append(h['generation'])
        founders = {i['id'] for i in s['population']}
        for item in s['population']:
            if item['id'] in items:
                assert items[item['id']] == item
            items[item['id']] = item
        requests[s['key']] = dict(config=s['config'], founders=founders, nominees=nominees,
                                 ids=founders | set(nominees))
    wanted = set().union(*(r['ids'] for r in requests.values()))
    for path in sorted((G/'segments').glob('*.lineage.jsonl.gz')):
        files.append(path)
        for row in lines(path):
            if row['id'] in wanted:
                item = {k: row[k] for k in ('id', 'genome', 'parent', 'birth')}
                assert row['id'] not in items or items[row['id']] == item
                items[row['id']] = item
    assert wanted <= items.keys()
    models = {}; conditions = {}
    for key, r in requests.items():
        members = []
        for identity in sorted(r['ids']):
            item = Individual.load(items[identity])
            mk = f"{r['config']['topology']}/{item.genome.digest}"
            models.setdefault(mk, dict(item=item.save(), topology=r['config']['topology']))
            members.append(dict(id=identity, model=mk, parent=item.parent, birth=item.birth,
                initial=identity in r['founders'], nomination_generations=r['nominees'].get(identity, [])))
        conditions[key] = dict(config=r['config'], members=members,
                               models=sorted({m['model'] for m in members}))
    return dict(models=models, conditions=conditions,
                membership_rule='All 96 initial validation-screened G individuals plus every subsequent validation nominee; genotype deduplication only within each condition.',
                input_sha256={str(p.relative_to(ROOT)): sha(p) for p in files})


def pool():
    assert not OUT.exists(), 'Never replace a frozen pool'
    t = time.perf_counter(); packet = inventory(); OUT.mkdir()
    compressed_json(OUT/'pool.json.gz', packet)
    write_json(OUT/'pool_freeze.json', dict(sha256=sha(OUT/'pool.json.gz'),
        conditions=len(packet['conditions']), physical_models=len(packet['models']),
        identity_memberships=sum(len(c['members']) for c in packet['conditions'].values()),
        genotype_memberships=sum(len(c['models']) for c in packet['conditions'].values()),
        wall_seconds=time.perf_counter()-t))
    print((OUT/'pool_freeze.json').read_text(), flush=True)


def read_pool():
    assert sha(OUT/'pool.json.gz') == json.loads((OUT/'pool_freeze.json').read_text())['sha256']
    return read_compressed(OUT/'pool.json.gz')


def organism(entry):
    return Organism(Individual.load(entry['item']).genome, entry['topology'], LIMITS, goal_pulse=True)


def react(org, o):
    m = o.maze
    return org.react(m.cells, m.w, m.h, m.start, m.goal)


def summarize(rows, metadata):
    groups = defaultdict(list)
    for row in rows:
        m = metadata[row['case']]
        groups[m['family'], m['stratum']].append(row)
    strata = {}
    for (family, stratum), part in groups.items():
        paired = defaultdict(list)
        for r in part:
            m = metadata[r['case']]; paired[m['base'], m['symmetry']].append(r)
        complete = {k: len(v)==2 and all(r['optimal'] for r in v) for k,v in paired.items()} if family in FAMILIES else {}
        bases = Counter()
        for (base, _), value in complete.items():
            bases[base] += int(value)
        strata[f'{family}/s{stratum}'] = dict(inputs=len(part), valid=sum(r['valid'] for r in part),
            optimal=sum(r['optimal'] for r in part), no_path=sum(r['no_path'] for r in part),
            false_no_path=sum(r['reachable'] and r['status']=='no_path' for r in part),
            pairs=sum(complete.values()), any_contexts=sum(v>0 for v in bases.values()),
            all_eight_contexts=sum(v==8 for v in bases.values()), base_pairs=dict(bases),
            failures=dict(Counter(r['failure'] for r in part if not r['valid'] and not r['no_path'])))
    branch = [r for r in rows if metadata[r['case']]['family'] in FAMILIES]
    pairs_by_family = [sum(s['pairs'] for k,s in strata.items() if k.startswith(f+'/')) for f in FAMILIES]
    corridor = sum(s['optimal'] for k,s in strata.items() if k.startswith('corridor/'))
    # This ordering is common to both selectors; it does not use cost to reward
    # incomplete outputs, no-path proxies, or H outcomes.
    rank = (sum(pairs_by_family), min(pairs_by_family), sum(r['optimal'] for r in branch),
            sum(r['valid'] for r in branch), corridor,
            -sum(r['reachable'] and r['status']=='no_path' for r in rows),
            round(sum(r['partial'] for r in branch), 8))
    return dict(inputs=len(rows), rank=list(rank), strata=strata,
        work=sum(max(0,r['reads'])+max(0,r['dispatches']) for r in rows),
        array_bytes=max((r['array_bytes'] for r in rows), default=0))


def choose(models, scores):
    # Lexicographically smallest topology/digest wins a complete score tie.
    return min(models, key=lambda m: (tuple(-v for v in scores[m]['rank']), m))


class Budget:
    def __init__(self, previous=None, cap_seconds=CAP_SECONDS, max_calls=MAX_CALLS):
        self.seconds=0.; self.calls=0; self.work=0; self.maximum=0.; self.scopes={}
        self.cap_seconds=cap_seconds; self.max_calls=max_calls
        if previous:
            self.__dict__.update(previous)

    def call(self, scope, org, o):
        if self.calls >= self.max_calls or self.seconds >= self.cap_seconds-max(5.,2*self.maximum):
            raise TimeoutError('V12I fixed call/time cap; retain partial results, never extend')
        t=time.perf_counter(); r=react(org,o); dt=time.perf_counter()-t
        work=r.instructions+r.spatial_reads
        self.seconds+=dt; self.calls+=1; self.work+=work; self.maximum=max(self.maximum,dt)
        part=self.scopes.setdefault(scope, dict(seconds=0.,calls=0,work=0))
        part['seconds']+=dt; part['calls']+=1; part['work']+=work
        assert self.seconds<self.cap_seconds
        return r


def warm():
    cases,_,_=load(FIXTURES); o=next(iter(cases.values())); t=time.perf_counter()
    react(organism(dict(item=controls()['intact'].save(),topology='local')),o)
    m=o.maze
    for name in ('compiled_bfs','compiled_astar','wave_bit'):
        baseline(name,m.cells,m.w,m.h,m.start,m.goal)
    return dict(candidate_calls=1,baseline_calls=3,seconds=time.perf_counter()-t,
                case=o.maze.case_id,readonly_uint8=True,work_metered=False)


def fixtures():
    assert not FIXTURES.exists()
    d=BreadthData(FIXTURE_SEED,exclusions())
    assert d.previous_count==138904
    for s in range(4):
        d.context('fixture',0,s,cut=True)
    d.save(FIXTURES)
    write_json(FIXTURES/'generation.json',dict(prior_layouts=d.previous_count,
        resulting_layouts=len(d.layouts),seed=FIXTURE_SEED))


def profile():
    from .validation_breadth_audit import geometry
    assert not (FIXTURES/'calibration.json').exists()
    p=read_pool(); cases,contexts,metadata=load(FIXTURES)
    t=time.perf_counter(); warmed=warm(); graphs=geometry(cases,contexts,metadata)
    budget=Budget(cap_seconds=60,max_calls=10000); summaries={}
    with gzip.open(FIXTURES/'outputs.jsonl.gz','wt',compresslevel=1) as log:
        for name in ('intact','west_return_gate'):
            org=organism(dict(item=controls()[name].save(),topology='local'))
            rows=[normal_row(budget.call('controls',org,o),o) for o in cases.values()]
            logrow(log,dict(model='known/'+name,rows=rows)); summaries[name]=summarize(rows,metadata)
        # Fixed profiling panel: first fork goal, pose 0, each of four strata,
        # for EVERY physical pool model. No profile score enters selection.
        ids=[c['poses'][0]['cases']['fork'][0] for c in contexts]
        for mk,entry in sorted(p['models'].items()):
            org=organism(entry)
            rows=[normal_row(budget.call('profile',org,cases[cid]),cases[cid]) for cid in ids]
            logrow(log,dict(model=mk,rows=rows))
    assert sum(s['optimal']+s['no_path'] for s in summaries['intact']['strata'].values())==len(cases)
    assert sum(s['optimal'] for s in summaries['west_return_gate']['strata'].values())<256
    assert budget.seconds<60, 'Calibration/profile cap is separate and closed at 60 seconds'
    physical=sum(len({m for c in p['conditions'].values() if c['config']['replicate']==r for m in c['models']}) for r in range(3))
    predicted=budget.scopes['profile']['seconds']/len(p['models'])/4*physical*256
    write_json(FIXTURES/'calibration.json',dict(passed=True,geometry=graphs,summaries=summaries,
        warmup=warmed,budget=vars(budget),physical_validation_models=physical,
        projected_validation_candidate_seconds=predicted,wall_seconds=time.perf_counter()-t,
        pool_sha256=sha(OUT/'pool.json.gz'),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print(json.dumps(dict(profile_seconds=budget.seconds,predicted_validation_seconds=predicted,
                         physical_validation_models=physical,geometry=graphs)),flush=True)


def source_hashes():
    paths=[*sorted((ROOT/'maze_evolution').glob('*.py')), ROOT/'cellular_maze_lab.py',
           ROOT/'docs/VALIDATION_BREADTH_V12I.md',ROOT/'tests/test_validation_breadth.py']
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}


def freeze():
    assert not (OUT/'preregistration.json').exists()
    profile=json.loads((FIXTURES/'calibration.json').read_text())
    assert profile['passed'] and profile['projected_validation_candidate_seconds']<500
    inputs=[OUT/'pool.json.gz',OUT/'pool_freeze.json',ROOT/'results/routing_transfer/completion.json',
            ROOT/'results/fork_pressure/completion.json',*FIXTURES.glob('*'),
            *(ROOT/'results/validation_breadth_preflight').glob('*')]
    write_json(OUT/'preregistration.json',dict(source_sha256=source_hashes(),
        input_sha256={str(p.relative_to(ROOT)):sha(p) for p in inputs if p.is_file()},
        seed=SEED,fixture_seed=FIXTURE_SEED,cap_seconds=CAP_SECONDS,max_calls=MAX_CALLS,
        limits=asdict(LIMITS),python=platform.python_version(),platform=platform.platform(),
        packages={n:version(n) for n in ('numpy','numba','llvmlite','pytest')},
        revision_before_freeze=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()))


def committed(path):
    """Require exact artifact bytes in HEAD and a pushed ancestor, before holdout."""
    rel=str(path.relative_to(ROOT))
    saved=subprocess.check_output(['git','show',f'HEAD:{rel}'])
    assert hashlib.sha256(saved).hexdigest()==sha(path), f'Uncommitted freeze: {rel}'
    subprocess.run(['git','merge-base','--is-ancestor','HEAD','origin/main'],check=True)
    return subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()


def check_freeze():
    p=json.loads((OUT/'preregistration.json').read_text())
    for name,digest in {**p['source_sha256'],**p['input_sha256']}.items():
        assert sha(ROOT/name)==digest,name
    return p


def selections(pool, scores):
    result={}
    for key,c in pool['conditions'].items():
        rep=str(c['config']['replicate']); result[key]={}
        for arm in ('narrow','broad'):
            mk=choose(c['models'],scores[rep][arm])
            members=[m for m in c['members'] if m['model']==mk]
            result[key][arm]=dict(model=mk,aliases=members,rank=scores[rep][arm][mk]['rank'])
    return result


def select():
    check_freeze(); revision=committed(OUT/'preregistration.json')
    assert not (OUT/'validation').exists()
    t=time.perf_counter(); p=read_pool(); warmed=warm(); budget=Budget()
    d=BreadthData(SEED,exclusions()+read_compressed(FIXTURES/'mazes.json.gz'))
    schedule=validation(d); d.save(OUT/'validation'); write_json(OUT/'validation/schedule.json',schedule)
    scores={}; counts={}; model_setup=0.
    try:
        with gzip.open(OUT/'validation/outputs.jsonl.gz','wt',compresslevel=1) as log:
            for rep in range(3):
                models=sorted({m for c in p['conditions'].values() if c['config']['replicate']==rep for m in c['models']})
                scores[str(rep)]={a:{} for a in ('narrow','broad')}; counts[str(rep)]=len(models)
                for index,mk in enumerate(models):
                    started=time.perf_counter(); org=organism(p['models'][mk]); model_setup+=time.perf_counter()-started
                    # Alternate arm order, keeping exact same input allowance.
                    for arm in (('narrow','broad') if index%2==0 else ('broad','narrow')):
                        rows=[normal_row(budget.call('validation/'+arm,org,d.cache[cid]),d.cache[cid]) for cid in schedule[str(rep)][arm]]
                        logrow(log,dict(replicate=rep,arm=arm,model=mk,rows=rows))
                        scores[str(rep)][arm][mk]=summarize(rows,d.metadata)
                    if index%100==0:
                        print(json.dumps(dict(replicate=rep,models_done=index+1,models_total=len(models),candidate_seconds=budget.seconds)),flush=True)
    finally:
        write_json(OUT/'validation/budget.json',vars(budget))
    chosen=selections(p,scores)
    compressed_json(OUT/'validation/scores.json.gz',scores)
    compressed_json(OUT/'selections.json.gz',chosen)
    write_json(OUT/'selection_freeze.json',dict(selections_sha256=sha(OUT/'selections.json.gz'),
        pool_sha256=sha(OUT/'pool.json.gz'),scores_sha256=sha(OUT/'validation/scores.json.gz'),
        validation_sha256={str(p.relative_to(ROOT)):sha(p) for p in (OUT/'validation').glob('*')},
        preregistration_revision=revision,budget=vars(budget),warmup=warmed,physical_models_by_draw=counts,
        logical_input_calls_per_arm=128*sum(len(c['models']) for c in p['conditions'].values()),
        inputs_per_model_per_arm=128,model_setup_seconds=model_setup,
        wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        prior_layouts=d.previous_count,resulting_layouts=len(d.layouts)))
    print(json.dumps(dict(selection_complete=True,unique_selected=len({v['model'] for s in chosen.values() for v in s.values()}),budget=vars(budget))),flush=True)


def confirmation():
    check_freeze(); revision=committed(OUT/'selection_freeze.json'); committed(OUT/'selections.json.gz')
    freeze=json.loads((OUT/'selection_freeze.json').read_text())
    assert sha(OUT/'selections.json.gz')==freeze['selections_sha256']
    for name,digest in freeze['validation_sha256'].items():
        assert sha(ROOT/name)==digest
    assert not (OUT/'confirmation').exists()
    t=time.perf_counter(); p=read_pool(); chosen=read_compressed(OUT/'selections.json.gz')
    budget=Budget(freeze['budget']); warmed=warm()
    d=BreadthData(SEED,exclusions()+read_compressed(FIXTURES/'mazes.json.gz')+read_compressed(OUT/'validation/mazes.json.gz'))
    final_data(d); d.save(OUT/'confirmation')
    entries={m:p['models'][m] for m in sorted({s['model'] for c in chosen.values() for s in c.values()})}
    entries.update({'known/'+name:dict(item=controls()[name].save(),topology='local') for name in ('intact','west_return_gate')})
    summaries={}; setup=0.
    try:
        with gzip.open(OUT/'confirmation/outputs.jsonl.gz','wt',compresslevel=1) as log:
            for mk,entry in entries.items():
                started=time.perf_counter(); org=organism(entry); setup+=time.perf_counter()-started
                rows=[normal_row(budget.call('final',org,o),o) for o in d.cache.values()]
                logrow(log,dict(model=mk,rows=rows)); summaries[mk]=summarize(rows,d.metadata)
                print(json.dumps(dict(model=mk,pairs=summaries[mk]['rank'][0],candidate_seconds=budget.seconds)),flush=True)
    finally:
        write_json(OUT/'confirmation/budget.json',vars(budget))
    with gzip.open(OUT/'confirmation/baselines.jsonl.gz','wt',compresslevel=1) as log:
        for name in ('compiled_bfs','compiled_astar','wave_bit'):
            rows=[]
            for o in d.cache.values():
                m=o.maze; r=baseline(name,m.cells,m.w,m.h,m.start,m.goal)
                rows.append(normal_row(r,o))
            logrow(log,dict(model=name,rows=rows)); summaries[name]=summarize(rows,d.metadata)
    for name in ('known/intact','compiled_bfs','compiled_astar','wave_bit'):
        assert sum(s['optimal']+s['no_path'] for s in summaries[name]['strata'].values())==4224
    compressed_json(OUT/'confirmation/summaries.json.gz',summaries)
    write_json(OUT/'confirmation/summary.json',dict(selection_revision=revision,seed=SEED,
        budget=vars(budget),warmup=warmed,physical_models=len(entries),baseline_calls=3*len(d.cache),
        input_count=len(d.cache),contexts=len(d.contexts),model_setup_seconds=setup,
        prior_layouts=d.previous_count,resulting_layouts=len(d.layouts),
        wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=['pool','fixtures','profile','freeze','select','confirmation'])
    globals()[parser.parse_args().action]()
