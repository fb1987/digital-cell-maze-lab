"""V12F frozen-genome transfer and mechanism confirmation; no training."""
import argparse
import base64
from collections import Counter
from dataclasses import asdict
import gzip
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import random
import resource
import subprocess
import time
import zlib

import numpy as np
from .baselines import baseline
from .foundation_calibration import ROOT, controls, write_json
from .foundation_data import load_pairs, layout_hash
from .foundation_pair_confirm import GENERAL_LIMITS as LIMITS, normal_row
from .foundation_study import read_compressed
from .growth import Individual, replay_mutation
from .growth_runtime import Organism
from .route_confirmation_data import OUT, FIXTURES, SEED, CONSTRUCTION_SEED, RouteData, exclusions
from .route_confirmation_runtime import respond

TARGET = 'foundation_study/local/fresh/evolution/1/i72095'
VARIANTS = {'normal': (True, True), 'pulse_off': (False, True),
            'flag_off': (True, False), 'both_off': (False, False)}
CAP_SECONDS = 600
HORIZON = 96


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lines(path):
    with gzip.open(path, 'rt') as f:
        for line in f:
            yield json.loads(line)


def freeze():
    if OUT.exists():
        raise FileExistsError('V12F freeze already exists')
    epath = ROOT/'results/foundation_pair/frozen_selections.json.gz'
    dpath = ROOT/'results/foundation_continuation/frozen_selections.json.gz'
    e, d = read_compressed(epath), read_compressed(dpath)
    target = e['foundation_pair_current/local/fresh/evolution/1']['common_archives']['paired']['item']
    assert target['id'] == TARGET
    ids = {TARGET, target['parent']}
    lineage, lineage_files = {}, set()
    for path in sorted((ROOT/'results/foundation_continuation/segments').glob('*.lineage.jsonl.gz'), reverse=True):
        for row in lines(path):
            if row['id'] in ids:
                lineage[row['id']] = row
                lineage_files.add(path)
        if len(lineage) == 2:
            break
    assert len(lineage) == 2
    parent = Individual.load(lineage[target['parent']])
    item = Individual.load(target)
    assert item.save() == Individual.load(lineage[TARGET]).save()
    assert replay_mutation(parent.genome, lineage[TARGET]['events'], 256) == item.genome
    frozen = dict(target=target, parent=parent.save(),
        checkpoint=d['foundation_study/local/fresh/evolution/1']['champion'],
        replacement=e['foundation_pair_paired/local/fresh/evolution/1']['common_archives']['paired']['item'],
        intact=controls()['intact'].save())
    assert item.genome.digest == 'aff6fc1a635d3c279d26'
    OUT.mkdir()
    write_json(OUT/'models.json', frozen)
    write_json(OUT/'lineage.json', lineage)
    inputs = [epath, dpath, *sorted(lineage_files),
        ROOT/'results/foundation_pair/completion.json', ROOT/'results/foundation_pair/verification.json',
        *sorted(FIXTURES.glob('*'))]
    # Hash every prior manifest used by the exclusion chain, without rescanning unrelated outputs.
    from .foundation_data import prior_hashes
    prior_files = prior_hashes(ROOT)
    # The recursive exclusion chain spans these later study datasets as well.
    inputs += [ROOT/p for p in ('results/foundation_calibration/mazes.json.gz',
        'results/foundation_calibration/fixtures.json.gz', 'results/foundation_repair/mazes.json.gz',
        'results/foundation_study_profile/unit_fixtures/mazes.json.gz',
        'results/foundation_confirmation_fixtures/mazes.json.gz')]
    inputs += [p for folder in ('foundation_study','foundation_study_fixtures','foundation_continuation',
                               'foundation_continuation_fixtures','foundation_pair','foundation_pair_fixtures')
               for p in (ROOT/'results'/folder).rglob('*mazes.json.gz')]
    sources = [*sorted((ROOT/'maze_evolution').glob('*.py')), ROOT/'cellular_maze_lab.py',
               ROOT/'docs/ROUTE_CONFIRMATION_V12F.md', ROOT/'tests/test_route_confirmation.py']
    record = dict(study='V12F', seed=SEED, construction_seed=CONSTRUCTION_SEED,
        parent_revision=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
        models_sha256=sha(OUT/'models.json'), lineage_sha256=sha(OUT/'lineage.json'),
        limits=asdict(LIMITS), candidate_inference_cap_seconds=CAP_SECONDS, trace_horizon=HORIZON,
        per_reachable_stratum=2, reachable_base_layouts=48, reachable_pairs=384, reachable_inputs=768,
        disconnected_base_layouts=4, disconnected_inputs=64, prior_layouts=124392,
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},
        input_sha256={**prior_files, **{str(p.relative_to(ROOT)):sha(p) for p in inputs}},
        model_digests={name:Individual.load(v).genome.digest for name,v in frozen.items()},
        transfer_screen=dict(longer_min_distance=9, minimum_successful_bases_per_family=3,
            all_eight_pose_base_per_family=1, interior_successful_base_per_family=1,
            misleading_successful_base_per_family=1, longest_band_successful_base_per_family=1),
        no_candidate_inference_before_freeze=True)
    write_json(OUT/'freeze.json', record)
    print(json.dumps(dict(models={n:(v['id'],v['birth']) for n,v in frozen.items()}, sources=len(sources),inputs=len(record['input_sha256'])),indent=2))


def check_freeze():
    f = json.loads((OUT/'freeze.json').read_text())
    for path, digest in {**f['source_sha256'], **f['input_sha256']}.items():
        assert sha(ROOT/path) == digest, path
    assert sha(OUT/'models.json') == f['models_sha256']
    assert sha(OUT/'lineage.json') == f['lineage_sha256']
    return f


class Budget:
    """Sum of bounded input-to-raster/trace calls, excluding grading and storage."""
    def __init__(self):
        self.seconds = 0.
        self.calls = 0
        self.work = 0
        self.max_call_seconds = 0.
        self.by_scope = {}

    def call(self, scope, function):
        # Leave a conservative reserve for one bounded VM response.
        if self.seconds >= CAP_SECONDS - max(5., 2*self.max_call_seconds):
            raise TimeoutError('Confirmation candidate-inference cap reached; preserve partial packet')
        t = time.perf_counter()
        result = function()
        elapsed = time.perf_counter()-t
        self.seconds += elapsed
        self.calls += 1
        self.max_call_seconds = max(self.max_call_seconds, elapsed)
        reaction = result.reaction if hasattr(result,'reaction') else result
        work = reaction.spatial_reads + reaction.instructions
        self.work += max(0,work)
        row = self.by_scope.setdefault(scope,dict(seconds=0.,calls=0,work=0))
        row['seconds'] += elapsed
        row['calls'] += 1
        row['work'] += max(0,work)
        assert self.seconds < CAP_SECONDS
        return result


def pack_history(state):
    raw = np.asarray(state,dtype='<u2').tobytes()
    return dict(shape=list(state.shape), dtype='<u2', raw_sha256=hashlib.sha256(raw).hexdigest(),
                raw_bytes=len(raw), zlib_base64=base64.b64encode(zlib.compress(raw,6)).decode())


def unpack_history(row):
    raw = zlib.decompress(base64.b64decode(row['zlib_base64']))
    assert hashlib.sha256(raw).hexdigest() == row['raw_sha256']
    assert len(raw) == row['raw_bytes']
    return np.frombuffer(raw,dtype='<u2').reshape(row['shape'])


def warm():
    """Software fixture and intact control only; exact production input signatures."""
    cases,_ = load_pairs(FIXTURES)
    m = next(iter(cases.values())).maze
    organism = Organism(controls()['intact'].genome,'local',LIMITS,goal_pulse=True)
    organism.react(m.cells,m.w,m.h,m.start,m.goal)
    respond(organism,m.cells,m.w,m.h,m.start,m.goal)
    respond(organism,m.cells,m.w,m.h,m.start,m.goal,halt_mode='forced',trace=True,horizon=96)
    baseline('compiled_bfs',m.cells,m.w,m.h,m.start,m.goal)


def run():
    frozen = check_freeze()
    target = OUT/'confirmation'
    if target.exists():
        raise FileExistsError('Confirmation already started; never overwrite or adapt it')
    # The protocol, source, software fixtures and all five genotypes must be committed.
    for path in ['results/route_confirmation/freeze.json', *frozen['source_sha256']]:
        subprocess.run(['git','diff','--exit-code','HEAD','--',path], check=True, capture_output=True)
        subprocess.run(['git','ls-files','--error-unmatch',path], check=True, capture_output=True)
    revision = subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip() == revision
    started = time.perf_counter()
    target.mkdir()
    write_json(target/'started.json',dict(freeze_revision=revision,freeze_sha256=sha(OUT/'freeze.json'),
        at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()))
    warm()
    warm_seconds = time.perf_counter()-started
    previous = exclusions()
    fixtures = json.load(gzip.open(FIXTURES/'mazes.json.gz','rt'))
    data = RouteData(SEED, previous+fixtures)
    before = set(data.layouts)
    construction = time.perf_counter()
    data.matrix('confirmation',2)
    for index in range(4):
        data.disconnected('confirmation',index)
    data.save(target)
    write_json(target/'layout_ledger.json',dict(prior_whole_layouts=124392,
        excluded_with_fixtures=len(before),new_whole_layouts=len(data.layouts-before),
        future_exclusion_count=len(data.layouts),new_hashes=sorted(data.layouts-before),
        rejections=data.rejections,construction_seconds=time.perf_counter()-construction))
    items = {k:Individual.load(v) for k,v in json.loads((OUT/'models.json').read_text()).items()}
    models = {k:Organism(v.genome,'local',LIMITS,goal_pulse=True) for k,v in items.items()}
    variants = {k:Organism(items['target'].genome,'local',LIMITS,goal_pulse=p) for k,(p,_) in VARIANTS.items()}
    budget = Budget()
    reachable = [o for o in data.cache.values() if o.path]
    all_cases = list(data.cache.values())
    rows = {}
    with gzip.open(target/'normal.jsonl.gz','wt') as log:
        for name, organism in models.items():
            for o in all_cases:
                m=o.maze
                r=budget.call('normal/'+name,lambda:organism.react(m.cells,m.w,m.h,m.start,m.goal))
                row=dict(model=name,variant='normal',**normal_row(r,o))
                rows[name,'normal',m.case_id]=row
                log.write(json.dumps(row,separators=(',',':'))+'\n')
            print(f'Normal {name} complete; candidate seconds {budget.seconds:.2f}',flush=True)
        for variant,organism in variants.items():
            if variant=='normal':
                continue
            for o in all_cases:
                m=o.maze
                flag=VARIANTS[variant][1]
                result=budget.call('ablation/'+variant,lambda:respond(organism,m.cells,m.w,m.h,m.start,m.goal,goal_flag=flag))
                row=dict(model='target',variant=variant,**normal_row(result.reaction,o))
                rows['target',variant,m.case_id]=row
                log.write(json.dumps(row,separators=(',',':'))+'\n')
        for o in all_cases:
            m=o.maze
            result=budget.call('halting/source_only',lambda:respond(models['target'],m.cells,m.w,m.h,m.start,m.goal,halt_mode='source_only'))
            log.write(json.dumps(dict(model='target',variant='source_only',**normal_row(result.reaction,o)),separators=(',',':'))+'\n')
        for o in all_cases:
            m=o.maze
            result=baseline('compiled_bfs',m.cells,m.w,m.h,m.start,m.goal)
            # Conventional methods have no VM active/range counters.
            result.dispatches=-1;result.active_instructions=-1;result.range_reads=(-1,)*4
            log.write(json.dumps(dict(model='bfs',variant='normal',**normal_row(result,o)),separators=(',',':'))+'\n')
    with gzip.open(target/'trajectories.jsonl.gz','wt') as log:
        for variant, organism in variants.items():
            flag=VARIANTS[variant][1]
            for o in reachable:
                m=o.maze
                result=budget.call('trace/'+variant,lambda:respond(organism,m.cells,m.w,m.h,m.start,m.goal,
                    goal_flag=flag,halt_mode='forced',trace=True,horizon=HORIZON))
                log.write(json.dumps(dict(model='target',variant=variant,
                    endpoint_halt=False,quiescence_halt=False,normally_emitted=False,
                    reaction=normal_row(result.reaction,o),history=pack_history(result.history)),separators=(',',':'))+'\n')
            print(f'Forced trajectories {variant} complete; candidate seconds {budget.seconds:.2f}',flush=True)
    # Success-conditioned timing is descriptive, never another selection or accuracy test.
    timed=[]
    for band in range(3):
        for family in ('tree','cyclic'):
            eligible=[o for g in data.groups.values() if g.level==band and g.key[3]==family
                for p in g.pairs for o in p.cases if rows['target','normal',o.maze.case_id]['optimal']]
            timed.extend(eligible[:2])
    timing=[]
    rng=random.Random(SEED+811)
    for o in timed:
        m=o.maze
        samples={n:[] for n in ('target','bfs','intact')}
        for repetition in range(31):
            names=list(samples);rng.shuffle(names)
            for name in names:
                t=time.perf_counter()
                if name=='bfs':
                    r=baseline('compiled_bfs',m.cells,m.w,m.h,m.start,m.goal)
                else:
                    r=budget.call('timing/'+name,lambda:models[name].react(m.cells,m.w,m.h,m.start,m.goal))
                samples[name].append(time.perf_counter()-t)
                assert normal_row_compatible(r,o)
        timing.append(dict(case=m.case_id,edges=len(o.path)-1,samples=samples))
    write_json(target/'timings.json',dict(selection='First two target successes per distance band/family in frozen manifest order; conditional on correct completed output.',
        repeats=31,scope='bytes input decoding, synchronous updates, halt and full raster emission; model setup/JIT excluded; Budget wrapper overhead included for VM calls.',rows=timing))
    write_json(target/'execution.json',dict(freeze_revision=revision,freeze_sha256=sha(OUT/'freeze.json'),
        candidate=vars(budget),warm_seconds=warm_seconds,wall_seconds=time.perf_counter()-started,
        max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        python=platform.python_version(),platform=platform.platform(),
        cpu=subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),
        packages={n:version(n) for n in ('numpy','numba','llvmlite','pytest')},
        completed=True,notes='No training. Serialization, dataset construction, grading, JIT and independent replay audit are outside candidate inference budget.'))
    print('Confirmation complete',flush=True)


def normal_row_compatible(r,o):
    from .evaluator import assess
    return assess(r,o).optimal


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('freeze','run'))
    a=p.parse_args()
    freeze() if a.action=='freeze' else run()
