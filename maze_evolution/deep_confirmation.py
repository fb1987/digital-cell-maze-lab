"""C1: frozen deep-campaign confirmation; no mutation, selection or new founders."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import multiprocessing
from pathlib import Path
import platform
import shutil
import sqlite3
import subprocess
import time
from collections import defaultdict
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz, compressed_json as writez
from .routing_transfer import sha
from .deep_campaign_store import Journal, writer_lock, hashed, packed
from .deep_campaign import run_stage, worker_init, evaluate_task, source_manifest
from . import deep_campaign as runner
from .deep_campaign import process_resources
from .deep_campaign_data import cases_from_manifest
from .exposure_selection import physical, record
from .exposure_genome import Individual, Genome
from .growth import Genome as Program, replay_mutation
from .regulatory import seeded_genome
from .baselines import baseline
from .foundation_pair_confirm import normal_row
from .routing_transfer import canonical
from .foundation_study_verify_core import Checker
from .reboot_data import confirmation

OUT=ROOT/'results/deep_confirmation'
RUN=ROOT/'runs/deep_confirmation_c1'
PRIOR=ROOT/'results/deep_campaign_run/milestone'
CONFIG=dict(phase='deep_confirmation_c1',seed=2026102009,fixture_seed=202610201009,
            workers=10,session_wall_seconds=3600,memory_bytes=12*2**30,
            storage_bytes=2*2**30,disk_free_floor_bytes=16*2**30,
            call_cap=1000000,work_cap=10**14)

def writej(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')

def checked_prior():
    seal=json.loads((PRIOR/'completion.json').read_text())
    for path,entry in seal['files'].items():
        assert sha(ROOT/path)==entry['sha256'],path
    return readz(PRIOR/'whole_layout_exclusions.json.gz')

def panel():
    starts=readz(ROOT/'results/deep_campaign_setup/founders.json.gz')
    choices=readz(PRIOR/'choices.json.gz')['items']
    ancestry=readz(PRIOR/'ancestry.json.gz')
    registry={};roles=defaultdict(list);initial=[]
    for island,s in enumerate(starts):
        for item in s['population']:
            if item['id'] in registry: assert registry[item['id']]==item
            registry[item['id']]=item;roles[item['id']].append(f'founder/{island}')
            initial.append(item['id'])
        for item in s['frozen_references']:roles[item['id']].append(f'reference/{island}')
    for island,items in enumerate(choices):
        for rank,r in enumerate(items):
            item=r['item'];registry[item['id']]=item;roles[item['id']].append(f'nominee/{island}/{rank}')
    comparisons=[];replayed=0
    for lineage in ancestry['lineages']:
        child=lineage['identity'];root=lineage['root'];events=lineage['ancestry_from_child_to_root']
        if lineage['root_kind']=='campaign_random_immigrant':
            assert root==child and not registry[child]['parent']
        current=registry[root]
        for identity in reversed(events):
            event=ancestry['records'][identity]
            if event['mutation'] is None:
                assert identity==root;continue
            assert event['parent']==current['id']
            genome=Genome(replay_mutation(Individual.load(current).genome.program,event['mutation'],256),7)
            assert genome.digest==event['genome_digest']
            parent=current
            current=dict(id=identity,genome=genome.to_dict(),parent=parent['id'],birth=event['birth'])
            replayed+=1
            if identity==child:registry[parent['id']]=parent
        assert current==registry[child],child
        parent=registry[child]['parent'] if lineage['campaign_mutation_births'] else None
        roles[root].append('root/'+child)
        if parent:roles[parent].append('parent/'+child)
        comparisons.append(dict(child=child,root=root,parent=parent,kind=lineage['root_kind'],mutations=lineage['campaign_mutation_births']))
    # Distinct positive control, never an evolutionary ancestor.
    g=seeded_genome();i=dict(id='control/intact_vm',genome=Genome(Program(g.genes),7).to_dict(),parent=None,birth=0)
    registry[i['id']]=i;roles[i['id']]=['control/intact_vm']
    models={}
    for identity in sorted(roles):
        item=registry[identity];key,model=physical(Individual.load(item),'neutral','local')
        models.setdefault(key,dict(model=model,aliases=[]))['aliases'].append(identity)
    return dict(items={i:registry[i] for i in sorted(roles)},roles=dict(roles),initial_identities=initial,
                comparisons=comparisons,physical_models=models,replayed_ancestral_events_including_shared=replayed)

def specs(p,ids):
    entries=[dict(model=v['model'],queries=ids,aliases=v['aliases']) for k,v in sorted(p['physical_models'].items())]
    return [[e] for e in entries]

def prepare():
    assert not (OUT/'registration.json').exists(),'Preparation already frozen'
    OUT.mkdir(exist_ok=True);prior=checked_prior();p=panel();writez(OUT/'panel.json.gz',p)
    fixture=confirmation(CONFIG['fixture_seed'],set(prior['hashes']),True);writez(OUT/'fixture.json.gz',fixture)
    previous=set(prior['hashes'])|set(fixture['new_layouts'])
    writez(OUT/'exclusions.json.gz',dict(count=len(previous),hashes=sorted(previous)))
    # Warm every measured runtime with the same readonly byte-backed signature.
    ids=fixture['queries'];mazes=[r for r in fixture['mazes'] if r['case_id'] in ids]
    keys=list(p['physical_models']);selected=[keys[0],next(k for k,v in p['physical_models'].items() if 'control/intact_vm' in v['aliases'])]
    for key in selected:evaluate_task([dict(**p['physical_models'][key],queries=ids[:1])],mazes,'fixture')
    receipts=[evaluate_task([dict(**p['physical_models'][key],queries=ids)],mazes,'fixture') for key in selected]
    writez(OUT/'fixture_receipts.json.gz',receipts)
    cases=cases_from_manifest(mazes);checker=Checker(cases)
    for cid,o in cases.items():
        for name in ('compiled_bfs','compiled_astar','wave_bit'):
            r=canonical(normal_row(baseline(name,o.maze.cells,o.maze.w,o.maze.h,o.maze.start,o.maze.goal),o));checker.row(r)
            assert r['optimal'] or r['no_path']
    writez(OUT/'fixture_receipts.json.gz',receipts)
    writej(OUT/'preflight.json',dict(candidate_calls=sum(r['calls'] for r in receipts),candidate_seconds=sum(r['candidate_seconds'] for r in receipts),
        physical_models=len(p['physical_models']),identities=len(p['items']),founder_slots=len(p['initial_identities']),fixture_queries=len(ids),
        fixture_generated=len(fixture['mazes']),ancestry_replay=True,independent_grades=True,scientific_calls=0))
    writej(OUT/'config.json',CONFIG)
    print(json.dumps(json.loads((OUT/'preflight.json').read_text()),indent=2))

def register():
    assert not (OUT/'registration.json').exists()
    manifest=source_manifest()
    paths=[OUT/'config.json',OUT/'panel.json.gz',OUT/'exclusions.json.gz',OUT/'fixture.json.gz',OUT/'fixture_receipts.json.gz',OUT/'preflight.json',ROOT/'docs/GENERAL_SOLVER_REBOOT.md',PRIOR/'completion.json']
    paths += [ROOT/'tests/test_reboot_confirmation.py',*sorted((OUT/'preflight_failure_001').glob('*')),OUT/'software_mazes.json.gz',OUT/'representative_profile.json',OUT/'representative_receipts.json.gz',OUT/'software_checks.json']
    manifest['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    manifest.update(phase='C1',created_utc=datetime.now(timezone.utc).isoformat(),scientific_cases_generated=0,scientific_calls=0)
    writej(OUT/'registration.json',manifest)

def check():
    r=json.loads((OUT/'registration.json').read_text())
    for p,h in r['files'].items():assert sha(ROOT/p)==h,p
    current=source_manifest()
    assert all(current[k]==r[k] for k in ('python','dependencies'))
    return json.loads((OUT/'config.json').read_text())

def resource_reason(directory, config, started):
    if time.monotonic()-started >= config['session_wall_seconds']: return 'session_wall'
    if process_resources() >= config['memory_bytes']: return 'memory'
    if shutil.disk_usage(directory).free < config['disk_free_floor_bytes']: return 'disk_free'
    size=sum(f.stat().st_size for base in (Path(directory),OUT) for f in base.rglob('*') if f.is_file())
    if size >= config['storage_bytes']: return 'storage'
    return None


def run():
    config=check();RUN.mkdir(parents=True,exist_ok=True)
    tracked=subprocess.check_output(['git','status','--porcelain','--',str(OUT/'registration.json')],cwd=ROOT,text=True)
    assert not tracked,'Commit and push registration before generation'
    local=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    remote=subprocess.check_output(['git','rev-parse','@{u}'],cwd=ROOT,text=True).strip()
    assert local==remote,'Push registered source before generation'
    runner.resource_reason=resource_reason  # New-phase accounting; frozen source stays untouched.
    started=time.monotonic();p=readz(OUT/'panel.json.gz');previous=set(readz(OUT/'exclusions.json.gz')['hashes'])
    with writer_lock(RUN):
        j=Journal(RUN);j.initialize(config,dict(panel_sha256=sha(OUT/'panel.json.gz')),previous);j.verify_chain()
        if j.get('latest')>=0:print('Already complete');j.close();return
        pending=j.pending()
        if pending:n,data=pending
        else:
            data=confirmation(config['seed'],previous)
            writez(OUT/'confirmation.json.gz',data)
            data['queries']={'all':data['queries']}
            tasks=specs(p,data['queries']['all'])
            assert sum(len(e['queries']) for task in tasks for e in task)<=config['call_cap']
            n=j.prepare(data,tasks)
        assert [s for _,s,_ in j.tasks(n)]==specs(p,data['queries']['all'])
        print('START',len(data['queries']['all']),'queries',len(p['physical_models']),'models',flush=True)
        with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=worker_init) as pool:
            reason=run_stage(j,n,data,pool,config,started,[False])
        if reason:writej(OUT/'session.json',dict(status='checkpoint',reason=reason,usage=j.get('usage')));j.close();return
        chain=j.commit(n,j.state(),dict(no_selection=True))
        writej(OUT/'session.json',dict(status='complete',chain=chain,usage=j.get('usage'),wall_seconds=time.monotonic()-started))
        j.close()
    print('COMPLETE',flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('action',choices=['prepare','register','run']);args=a.parse_args()
    globals()[args.action]()
