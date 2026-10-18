"""Post-freeze V11 provenance, saved-output and accounting verification."""
import argparse
from collections import Counter,defaultdict
import ast,gzip,hashlib,json,math,time,resource
from pathlib import Path
import numpy as np
from .evaluator import Maze,Oracle,assess
from .experiment import write_json
from .goal_data import GoalPair,layout_hash
from .growth_data import prior_manifests
from .growth_search import learned_parents
from .goal_fitness import goal_metrics,source_component
from .junction_fitness import decision
from .growth import Genome,Individual
from .runtime import Reaction
from .signal_audit import lines


def unpack(value,n):
    return np.unpackbits(np.frombuffer(bytes.fromhex(value),dtype=np.uint8),bitorder='little')[:n]



def trace_array(parent_bytes,events,ceiling):
    """Independent concrete edit replay and old seven-mode eligibility checks."""
    from .regulatory import SPECS,REMOTE,REMOTE_MIN,Gene
    rows=np.frombuffer(parent_bytes,dtype='<i4').reshape(-1,7).tolist()
    assert 1<=len(events)<=6 and ceiling in (128,256)
    for e in events:
        n=len(rows);i=e['index'];mode=e['requested_mode'];assert n==e['before_length'] and 0<=i<n and 0<=mode<7
        expected='insert' if mode==0 and n<ceiling else 'delete' if mode==1 and n>1 else 'replace' if mode==2 else 'swap' if mode==3 else 'duplicate' if mode==4 and n<ceiling else 'operand'
        assert e['kind']==expected
        if expected=='insert':rows.insert(i,Gene(*e['row']).row())
        elif expected=='delete':rows.pop(i)
        elif expected=='replace':rows[i]=Gene(*e['row']).row()
        elif expected=='swap':
            j=e['other'];assert 0<=j<n;rows[i],rows[j]=rows[j],rows[i]
        elif expected=='duplicate':
            k=e['count'];assert 1<=k<=min(8,n-i,ceiling-n);rows[i:i]=[list(row) for row in rows[i:i+k]]
        else:
            old=rows[i];new=Gene(*e['row']).row();field=e['field']
            fields=list(range(1,1+len(SPECS[old[0]])))+[6]+([5] if old[0] in (REMOTE,REMOTE_MIN) else [])
            assert field in fields and all(a==b for j,(a,b) in enumerate(zip(old,new)) if j!=field)
            rows[i]=new
        assert len(rows)==e['after_length'] and 1<=len(rows)<=ceiling
    return np.asarray(rows,dtype='<i4').tobytes()


def repack(out):
    """Lossless compression of new V11 logs only, after inference timing."""
    out=Path(out)
    if (out/'storage.json').exists():raise FileExistsError('Storage audit already exists')
    champions=json.loads((out/'champions.json').read_text())
    if not all(v['config']['search_version']==11 for v in champions.values()):
        raise ValueError('Only V11 logs may be repacked here')
    started=time.perf_counter();rows=[]
    for p in sorted((out/'logs').glob('*/*.jsonl.gz')):
        old_size=p.stat().st_size;decoded=hashlib.sha256();size=0;tmp=p.with_suffix('.tmp')
        with gzip.open(p,'rb') as src, open(tmp,'wb') as raw:
            with gzip.GzipFile(filename='',fileobj=raw,mode='wb',compresslevel=9,mtime=0) as dst:
                while chunk:=src.read(1<<20):
                    decoded.update(chunk);size+=len(chunk);dst.write(chunk)
        verify=hashlib.sha256();verified_size=0
        with gzip.open(tmp,'rb') as src:
            while chunk:=src.read(1<<20):verify.update(chunk);verified_size+=len(chunk)
        assert verify.hexdigest()==decoded.hexdigest() and verified_size==size
        tmp.replace(p)
        rows.append(dict(path=str(p.relative_to(out)),before_bytes=old_size,stored_bytes=p.stat().st_size,
            stored_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),decoded_sha256=decoded.hexdigest(),decoded_bytes=size))
    result=dict(before_bytes=sum(r['before_bytes'] for r in rows),after_bytes=sum(r['stored_bytes'] for r in rows),
        elapsed_seconds=time.perf_counter()-started,files=rows)
    write_json(out/'storage.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))


def audit(out):
    out=Path(out);root=Path(__file__).resolve().parents[1];started=time.perf_counter()
    env=json.loads((out/'environment.json').read_text())
    assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in env['source_sha256'].items())
    assert hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()==env['champions_sha256']
    if (out/'diagnostics.json').exists():
        diagnostic=json.loads((out/'diagnostics.json').read_text())
        assert hashlib.sha256((root/'maze_evolution/growth_diagnostics.py').read_bytes()).hexdigest()==diagnostic['source_sha256']
        assert diagnostic['champions_sha256']==env['champions_sha256']
    proof=json.loads((out/'equivalence.json').read_text());assert proof['all_checks_passed'] and proof['seed']!=json.loads((out/'config.json').read_text())['seed']
    for path,h in {**proof['source_sha256'],**proof['input_sha256']}.items():assert hashlib.sha256((root/path).read_bytes()).hexdigest()==h
    if (out/'limits_verification.json').exists():
        bounds=json.loads((out/'limits_verification.json').read_text());assert bounds['all_checks_passed']
        assert hashlib.sha256((root/bounds['source_path']).read_bytes()).hexdigest()==bounds['source_sha256']
    test_source=(root/'tests/test_growth.py').read_text()
    preflight=next(n for n in ast.parse(test_source).body if isinstance(n,ast.FunctionDef) and n.name=='test_v11_fresh_capacity_independent_preflight_seed')
    data_call=next(n for n in ast.walk(preflight) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='GrowthData')
    preflight_seed=ast.literal_eval(data_call.args[0]);study_seed=json.loads((out/'config.json').read_text())['seed']
    assert preflight_seed!=study_seed
    write_json(out/'protocol_notes.json',dict(construction_preflight_seed=preflight_seed,study_seed=study_seed,
        independent_preflight_seed=True,source_sha256=hashlib.sha256(test_source.encode()).hexdigest()))
    packed_files=0
    if (out/'storage.json').exists():
        for r in json.loads((out/'storage.json').read_text())['files']:
            p=out/r['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['stored_sha256']
            digest=hashlib.sha256();size=0
            with gzip.open(p,'rb') as f:
                while chunk:=f.read(1<<20):digest.update(chunk);size+=len(chunk)
            assert digest.hexdigest()==r['decoded_sha256'] and size==r['decoded_bytes']
            packed_files+=1
    packed={};lengths={};mutation_events=defaultdict(Counter);trace_checks=0
    ancestors={};learned={};fork_groups=defaultdict(dict);supplement=None;source_ancestry=None
    def ancestor_item(item):
        digest=Genome.from_dict(item['genome']).digest
        assert item['id'] not in ancestors or ancestors[item['id']]==digest
        ancestors[item['id']]=digest;packed[item['id']]=Genome.from_dict(item['genome']).array().astype('<i4').tobytes();lengths[item['id']]=len(item['genome']['genes'])
    for path,h in json.loads((out/'forks.json').read_text()).items():
        assert hashlib.sha256((root/path).read_bytes()).hexdigest()==h
        saved=json.loads((root/path).read_text())
        if 'records' in saved:
            if isinstance(saved['records'],list):
                source_ancestry=saved['records']
                for record in source_ancestry:
                    for node in record['nodes']:ancestor_item(node['individual'])
            else:
                supplement=saved['records']
                for record in supplement.values():ancestor_item(record['individual'])
            continue
        assert saved['config']['origin']=='random' and saved['config']['search_version']==10
        for item in saved['population']+saved['protected']+[v['individual'] for v in saved['archives'].values()]:ancestor_item(item)
        c=saved['config'];fork_groups[(c['topology'],c['replicate'])][c['pressure']]=saved
    assert supplement is not None and source_ancestry is not None
    for (topology,rep),group in fork_groups.items():
        extra=[supplement[f'distance/{topology}/{mode}/{rep}']['individual'] for mode in ('fixed','curriculum')]
        for record in source_ancestry:
            if record['condition'].split('/')[1]==topology and int(record['condition'].split('/')[3])==rep:
                extra.extend(n['individual'] for n in record['nodes'])
        learned[(topology,rep)]={Genome.from_dict(i['genome']).digest for i in learned_parents([group[a] for a in ('fixed','curriculum')],extra)}
    known=dict(ancestors);ancestry={};maximum_genes=0
    for p in sorted((out/'logs').glob('*/*.genomes.jsonl.gz')):
        for r in lines(p):
            item=Individual.load(r);assert item.identity not in known
            assert item.parent is None or item.parent in known
            if item.birth==0:assert item.parent in ancestors and item.genome.digest==ancestors[item.parent]
            ceiling=int(item.identity.split('/')[2][3:]);assert len(item.genome.genes)<=ceiling and r['genome']['version']==3
            if item.birth==0 or item.parent is None:
                assert not r['mutation']
                if item.parent is None:assert 64<=len(item.genome.genes)<=128
            else:
                replayed=trace_array(packed[item.parent],r['mutation'],ceiling)
                assert replayed==item.genome.array().astype('<i4').tobytes();trace_checks+=1
                counts=mutation_events['/'.join(item.identity.split('/')[:-1])]
                for event in r['mutation']:
                    counts['events']+=1;counts[event['kind']]+=1
                    counts['requested_'+str(event['requested_mode'])]+=1
                    counts['capacity_fallbacks']+=event['requested_mode'] in (0,4) and event['before_length']==ceiling
                counts['children']+=1;counts['grew']+=len(item.genome.genes)>lengths[item.parent]
                counts['above128_children']+=len(item.genome.genes)>128
            packed[item.identity]=item.genome.array().astype('<i4').tobytes();lengths[item.identity]=len(item.genome.genes)
            known[item.identity]=item.genome.digest;ancestry[item.identity]=(item.parent,item.birth)
            maximum_genes=max(maximum_genes,len(item.genome.genes))
    del packed
    assert maximum_genes<=256
    champions=json.loads((out/'champions.json').read_text());lineages=[]
    for key,saved in champions.items():
        c=saved['config'];p=out/'checkpoints'/(key.replace('/','_')+'.json');checkpoint=json.loads(p.read_text())
        assert len(checkpoint['population'])==96
        protected=[Individual.load(i) for i in checkpoint['protected']]
        assert {i.genome.digest for i in protected}==learned[(c['topology'],c['replicate'])]
        assert {i.identity for i in protected} <= {i['id'] for i in checkpoint['population']}
        for source in ('archives','frozen'):
            for label,record in saved[source].items():
                item=Individual.load(record['individual']);assert known[item.identity]==item.genome.digest
                if source=='frozen':continue
                identity=item.identity;depth=0
                while True:
                    parent,birth=ancestry[identity]
                    if parent not in ancestry:break
                    depth+=1;identity=parent
                lineages.append(dict(condition=key,archive=label,id=item.identity,mutation_depth=depth,
                    root_id=identity,root_birth=birth,root_parent=parent,
                    root_type='checkpoint' if parent in ancestors else 'fresh_immigrant'))
    for t in ('local','evolved'):
        for rep in range(3):
            assert champions[f'growth/{t}/cap128/{rep}']['initial_digests']==champions[f'growth/{t}/cap256/{rep}']['initial_digests']
    for t in ('local','evolved'):
        for rep in range(3):
            a=champions[f'growth/{t}/cap256/{rep}'];b=champions[f'growth/{t}/cap128/{rep}']
            for label in a['frozen']:
                assert a['frozen'][label]['rank']==b['frozen'][label]['rank']
                assert a['frozen'][label]['individual']['genome']==b['frozen'][label]['individual']['genome']
    write_json(out/'lineage_audit.json',lineages)
    previous=prior_manifests(root)
    previous_layouts={hashlib.sha256(f"{r['w']},{r['h']}:".encode()+bytes.fromhex(r['cells_hex'])).hexdigest() for r in previous}
    manifest=json.loads(gzip.open(out/'mazes.json.gz','rt').read());oracles={};layouts=defaultdict(list);digests=set()
    for r in manifest:
        m=Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id'])
        assert m.digest==r['sha256'] and m.digest not in digests
        digests.add(m.digest);lh=layout_hash(m);assert lh not in previous_layouts
        layouts[lh].append(m.case_id);oracles[m.case_id]=Oracle.build(m)
    pairs={};pair_entries=json.loads((out/'pairs.json').read_text())
    for r in pair_entries:
        pair=GoalPair(oracles[r['first']],oracles[r['second']],r['mixed'])
        a,b=pair.cases;assert layout_hash(a.maze)==r['layout_sha256']
        near=a.maze.split.startswith('train_near')
        assert len(a.path)-1>=(3 if near else 8)
        if pair.mixed:assert not b.path and not near
        else:
            assert len(b.path)-1>=(3 if near else 8)
            if not near:assert a.to_goal[b.maze.goal]>=max(len(a.path)-1,len(b.path)-1)
        label=decision(pair);assert label==r['decision']
        if not pair.mixed:
            assert label and 2<=label['distance']<=8
            from cellular_maze_lab import neighbors
            for i,o in enumerate(pair.cases):
                v=label['vertex']
                exact={q for q in neighbors(v,o.maze.w,o.maze.h) if o.maze.cells[q] and o.to_goal[q]==o.to_goal[v]-1}
                assert exact==set(label['allowed'][i]) and o.to_goal[v]>=(1 if near else 4)
            index=int(r['first'].split('/p')[1].split('/')[0])
            if near:
                from .growth_data import cue_distances
                generation=index//2;rep=int(r['first'].split('/r')[1].split('/')[0])
                expected=cue_distances(generation,rep);assert expected is not None
                assert a.maze.split==('train_near1_goal' if generation<16 else 'train_near2_goal')
                assert [o.to_goal[label['vertex']] for o in pair.cases]==list(expected)
                far=GoalPair(*(oracles[o.maze.case_id.replace(o.maze.split+'/','train_goal/',1)] for o in pair.cases))
                anchor=decision(far)
                assert all(label[k]==anchor[k] for k in ('vertex','prefix','incoming','distance','exits'))
                for o,f,length in zip(pair.cases,far.cases,expected):
                    target=anchor['vertex']
                    for _ in range(length):target=min(q for q in neighbors(target,f.maze.w,f.maze.h) if f.maze.cells[q] and f.to_goal[q]==f.to_goal[target]-1)
                    assert target==o.maze.goal and layout_hash(o.maze)==layout_hash(f.maze) and o.maze.start==f.maze.start
                assert all(set(x)<=set(y) for x,y in zip(label['allowed'],anchor['allowed']))
            elif index%2==0:assert any(label['detours'])
        pairs[(r['first'],r['second'])]=pair
    for lh,ids in layouts.items():
        groups={('train' if oracles[i].maze.split.startswith('train') else oracles[i].maze.split) for i in ids}
        assert len(groups)==1
        assert len(ids)==(1 if groups=={'test_goal'} else 4 if any(oracles[i].maze.split.startswith('train_near') for i in ids) else 2)
    def check_output(r,paired=False):
        oracle=oracles[r['case'] if paired else r['case_id']];mask=unpack(r['mask'],len(oracle.maze.cells))
        result=Reaction(mask,r['status'],r['steps'],0,0,0);a=assess(result,oracle)
        fields={'valid':'valid_path','optimal':'optimal','no_path':'no_path_correct','failure':'failure'} if paired else {k:k for k in ('reachable','valid_path','optimal','no_path_correct','path_length','oracle_length','failure')}
        assert all(r[k]==getattr(a,v) for k,v in fields.items()),(r,fields)
        assert abs(r['partial']-a.partial)<1e-9
    def check_balanced(record,objective=None):
        values=[];families=defaultdict(list)
        for a,b in zip(record['cases'][::2],record['cases'][1::2]):
            pair=pairs[(a['case'],b['case'])];regular=not pair.mixed
            minimum=min(a['goal']['score'],b['goal']['score']) if regular else None
            if regular:
                values.append(minimum);families[pair.first.maze.family].append(minimum)
            for row in (a,b):
                if 'pair_min_goal' in row:assert row['pair_min_goal']==minimum
                if objective in ('mean','balanced'):
                    g=row['goal']['score'];bonus=g+minimum if objective=='balanced' and regular else 2*g
                    assert abs(row['factor_bonus']-bonus)<1e-12
        value=float(np.mean(values)) if values else 0.
        if 'balanced' in record:assert abs(record['balanced']-value)<1e-12
        if 'balanced_families' in record:
            expected={k:float(np.mean(v)) for k,v in families.items()}
            assert record['balanced_families']==expected
        return value
    choice_records=[];junction_checks=0;entry_choices=[]
    def check_junction(record,objective=None,case_key='case'):
        nonlocal junction_checks
        minima=[];strict=[];families=defaultdict(list)
        for a,b in zip(record['cases'][::2],record['cases'][1::2]):
            pair=pairs[(a[case_key],b[case_key])];label=decision(pair);values=[];entries=[]
            aligned=all(r['signal']['aligned'] for r in (a,b))
            for i,row in enumerate((a,b)):
                n=len(pair.first.maze.cells);mask=unpack(row['probe_mask'],n);off=unpack(row['source_removed_mask'],n)
                if label is None:
                    want_score=0.;want_strict=False
                else:
                    # Independently walk the emitted component and count causal prefix/exits.
                    from collections import deque
                    from cellular_maze_lab import neighbors
                    m=pair.first.maze;seen=set()
                    if mask[m.start] and not any(mask[p] and not m.cells[p] for p in range(n)):
                        queue=deque([m.start]);seen.add(m.start)
                        while queue:
                            for q in neighbors(queue.popleft(),m.w,m.h):
                                if mask[q] and q not in seen:seen.add(q);queue.append(q)
                    want=set(label['allowed'][i]);wrong=set(label['exits'])-want
                    lit=[p for p in want if mask[p]];bad=[p for p in wrong if mask[p]]
                    prefix=label['prefix'][2:];R=sum(p in seen and not off[p] for p in prefix)/len(prefix)
                    C=(sum(not off[p] for p in lit)/len(lit))*(1-len(bad)/len(wrong))/len(lit) if lit and label['vertex'] in seen else 0.
                    want_score=(.25*R+.75*C) if aligned else 0.
                    want_strict=bool(aligned and label['vertex'] in seen and len(lit)==1 and not bad and not off[lit[0]])
                    assert abs(row['junction']['prefix']-R)<1e-12 and abs(row['junction']['choice']-C)<1e-12
                assert abs(row['junction']['score']-want_score)<1e-12 and row['junction']['strict']==want_strict
                values.append(want_score);junction_checks+=1
                entry_distance=None
                if want_strict:
                    # Additional diagnostic specified during training: a raster
                    # should enter the fork from source, not through its wanted exit.
                    blocked=set(label['allowed'][i]);m=pair.first.maze
                    d={m.start:0} if mask[m.start] and m.start not in blocked else {}
                    queue=deque(d)
                    while queue:
                        current=queue.popleft()
                        for q in neighbors(current,m.w,m.h):
                            if mask[q] and q not in blocked and q not in d:d[q]=d[current]+1;queue.append(q)
                    entry_distance=d.get(label['vertex'])
                entries.append(dict(strict=want_strict,entry_distance=entry_distance,
                    enters_without_desired_exit=entry_distance is not None,
                    entry_is_shortest=bool(entry_distance is not None and entry_distance==label['distance'])))
            both=all(r['junction']['strict'] for r in (a,b))
            assert all(r['junction']['pair_both']==both for r in (a,b))
            if both:
                entry_choices.append(dict(condition=record.get('condition',record.get('original_arm',record.get('arm'))),
                    split=record.get('split',record.get('assay','native')),id=record.get('id'),generation=record.get('generation'),
                    first=a[case_key],family=pair.first.maze.family,entries=entries,
                    both_enter_from_source=all(r['enters_without_desired_exit'] for r in entries),
                    both_shortest_prefixes=all(r['entry_is_shortest'] for r in entries)))
            if label is not None:
                minima.append(min(values));strict.append(both);families.setdefault(pair.first.maze.family,[]).append(min(values))
                if pair.first.maze.split=='test_pairs':
                    choice_records.append(dict(arm=record.get('original_arm',record.get('arm')),replicate=record.get('replicate'),
                        assay=record.get('assay','native'),first=a[case_key],decision=label,
                        metrics=[a['junction'],b['junction']],both=both))
            if objective:
                for i,row in enumerate((a,b)):
                    expected=values[i]+min(values) if objective=='junction' and label else row['goal']['score']+(min(a['goal']['score'],b['goal']['score']) if label else row['goal']['score'])
                    assert abs(row['factor_bonus']-expected)<1e-12
        for key,want in (('junction',float(np.mean(minima)) if minima else 0.),('junction_both',float(np.mean(strict)) if strict else 0.)):
            if key in record:assert abs(record[key]-want)<1e-12
        if 'junction_families' in record:
            assert set(record['junction_families'])==set(families)
            assert all(abs(record['junction_families'][k]-float(np.mean(v)))<1e-12 for k,v in families.items())
    priority_checks=0
    def check_priority(record,pressure):
        nonlocal priority_checks
        K=0;families=defaultdict(list);credits=[]
        for a,b in zip(record['cases'][::2],record['cases'][1::2]):
            pair=pairs[(a['case'],b['case'])];eligible=decision(pair) is not None
            strict=int(eligible and a['junction']['strict'] and b['junction']['strict']);K+=strict
            if eligible:families[pair.first.maze.family].append(strict)
            credit=strict if pressure=='choice' else 0
            for row in (a,b):
                assert row['junction']['eligible']==eligible and row['strict_pair_credit']==credit
                credits.append(credit)
        assert record['strict_pairs']==K and record['selection_credit']==(K if pressure=='choice' else 0)
        expected={k:sum(v)/len(v) for k,v in families.items()}
        assert record['choice_families']==expected
        if 'fitness' in record:
            smooth=record['smooth_fitness'];assert len(smooth)==5
            assert record['fitness']==smooth[:3]+[record['selection_credit']]+smooth[3:]
            assert len(record['case_values'])==len(record['cases'])
            for values,row,credit in zip(record['case_values'],record['cases'],credits):
                assert values[:3]==[int(row['valid'] or row['no_path']),int(row['optimal'] or row['no_path']),credit]
                assert abs(values[3]-(row['partial']+row['signal']['score']+row['factor_bonus']))<1e-12
        priority_checks+=1
    primary=paired_outputs=goal_checks=signal_checks=replayed=0;probe_routes=[];saved_probes={};replay_keys=set();junctions=[]
    for r in lines(out/'holdout.jsonl.gz'):
        assert oracles[r['case_id']].maze.split=='test_goal';check_output(r);primary+=1
        if '/' in r['arm'] and (r['arm'],r['replicate']) not in replay_keys:
            from .growth_runtime import Organism
            from .runtime import Limits
            t,mode,label=r['arm'].split('/');saved=champions[f'growth/{t}/{mode}/{r["replicate"]}']
            source='frozen' if label.startswith('frozen_') else 'archives';archive=label.removeprefix('frozen_')
            item=Individual.load(saved[source][archive]['individual']);m=oracles[r['case_id']].maze
            actual=Organism(item.genome,t,Limits(**saved['config']['eval_limits']),goal_pulse=True).react(m.cells,m.w,m.h,m.start,m.goal)
            assert np.array_equal(actual.mask,unpack(r['mask'],len(m.cells))) and actual.status==r['status']
            assert (actual.steps,actual.spatial_reads,actual.dispatches)==(r['steps'],r['reads'],r['dispatches'])
            replay_keys.add((r['arm'],r['replicate']));replayed+=1
    for r in lines(out/'paired_holdout.jsonl.gz'):
        if 'baseline' in r:check_output(r['baseline']);paired_outputs+=1;continue
        cases=r['cases'];scores=[]
        for a,b in zip(cases[::2],cases[1::2]):
            pair=pairs[(a['case'],b['case'])];assert pair.first.maze.split=='test_pairs'
            masks=[unpack(v['probe_mask'],len(pair.first.maze.cells)) for v in (a,b)]
            removed=[unpack(v['source_removed_mask'],len(pair.first.maze.cells)) for v in (a,b)]
            expected=goal_metrics(masks,removed,pair)
            if not(a['signal']['aligned'] and b['signal']['aligned']):
                for v in expected:v['score']=0.;v['pair_both']=False
            if pair.first.maze.family=='perfect' and not pair.mixed:
                pa,pb=pair.first.path,pair.second.path;k=0
                while k+1<min(len(pa),len(pb)) and pa[k+1]==pb[k+1]:k+=1
                assert k+1<min(len(pa),len(pb))
                junction=pa[k];choices=[pa[k+1],pb[k+1]];assert choices[0]!=choices[1]
                local=[];correct=[];connected=[]
                for i,mask in enumerate(masks):
                    _,component=source_component(mask,pair.first.maze)
                    local.append([bool(mask[p]) for p in (junction,choices[0],choices[1])])
                    connected.append(junction in component)
                    correct.append(junction in component and choices[i] in component and not bool(mask[choices[1-i]]))
                junctions.append(dict(arm=r['arm'],replicate=r['replicate'],first=a['case'],second=b['case'],
                    junction=junction,choice_a=choices[0],choice_b=choices[1],source_to_junction_edges=k,
                    junction_to_goals=[len(pa)-1-k,len(pb)-1-k],local_output_bits=local,
                    aligned=bool(a['signal']['aligned'] and b['signal']['aligned']),
                    junction_source_connected=connected,correct_goal_choice=correct,both_correct=all(correct),
                    same_local_output=local[0]==local[1],
                    scope='Diagnostic added during training before final evaluation; saved tick16 rasters on perfect-tree pairs only; no selection or route claim'))
            for actual,want in zip((a,b),expected):
                check_output(actual,True);paired_outputs+=1;goal_checks+=1;scores.append(want['score'])
                oracle=oracles[actual['case']]
                saved_probes[(r['arm'],r['replicate'],actual['case'])]=unpack(actual['probe_mask'],len(oracle.maze.cells))
                probe_result=Reaction(unpack(actual['probe_mask'],len(oracle.maze.cells)),'emitted',16,0,0,0)
                probe_assessment=assess(probe_result,oracle)
                probe_routes.append(dict(arm=r['arm'],replicate=r['replicate'],case=actual['case'],
                    reachable=bool(oracle.path),aligned=actual['goal']['aligned'],
                    probe_valid=probe_assessment.valid_path,probe_shortest=probe_assessment.optimal,
                    normal_valid=actual['valid'],normal_shortest=actual['optimal'],normal_status=actual['status'],
                    diagnostic='Tick16 raster assessed with assumed emitted status; no actual halt is asserted'))
                for k,v in want.items():
                    assert abs(actual['goal'][k]-v)<1e-9,(actual['case'],k)
        assert abs(r['goal']-np.mean(scores))<1e-9
        check_balanced(r);check_junction(r,'junction');check_priority(r,'choice')
    switch_checks=timecourse_checks=turned_outputs=0
    if (out/'goal_timecourse.json').exists():
        for r in json.loads((out/'goal_timecourse.json').read_text()):
            assert oracles[r['first']].maze.split==oracles[r['second']].maze.split=='test_pairs'
            assert len(oracles[r['first']].path)-1>=8 and len(oracles[r['second']].path)-1>=8
            channels=set(r['changed_channels']);assert channels<=set(range(8))
            snapshots=np.asarray(r['source_states']);assert snapshots.shape==(2,8)
            label=decision(pairs[(r['first'],r['second'])]);assert r['junction_vertex']==label['vertex']
            junction_snapshots=np.asarray(r['junction_states']);assert junction_snapshots.shape==(2,8)
            assert r['junction_changed_channels']==np.flatnonzero(junction_snapshots[0]!=junction_snapshots[1]).tolist()
            assert r['junction_exits']==label['exits']
            if r['horizon']==16:
                for i,case in enumerate((r['first'],r['second'])):
                    raster=saved_probes[(r['arm'],r['replicate'],case)]
                    assert bool(junction_snapshots[i,2])==bool(raster[label['vertex']])
                    assert [bool(v) for v in r['junction_exit_states'][i]]==[bool(raster[v]) for v in label['exits']]
            assert np.all((snapshots>=0)&(snapshots<=65535))
            assert channels==set(np.flatnonzero(snapshots[0]!=snapshots[1]).tolist())
            assert r['any_source_state']==bool(channels)
            assert r['hidden_source_state']==bool(channels-{2,7})
            assert r['output_source_state']==(2 in channels) and r['stop_source_state']==(7 in channels)
            assert r['aligned']==(r['steps'][0]==r['steps'][1]==r['horizon'])
            if r['horizon']==16:
                a,b=[saved_probes[(r['arm'],r['replicate'],case)] for case in (r['first'],r['second'])]
                assert int(np.sum(a!=b))==r['probe_raster_changes'];switch_checks+=1
            timecourse_checks+=1
    if (out/'opportunity_diagnostics.json').exists():
        for r in json.loads((out/'opportunity_diagnostics.json').read_text()):
            pair=next(p for p in pairs.values() if p.first.maze.case_id==r['first']);label=decision(pair)
            region=[label['vertex']]+label['exits']
            expected=[min(o.to_goal[v] for v in region) for o in pair.cases]
            assert r['goal_to_decision_region']==expected and r['local_goal_inputs_both_outside_16_cones']==all(d>16 for d in expected)
    cross_outputs=cross_goals=0
    if (out/'cross_input.jsonl.gz').exists():
        for r in lines(out/'cross_input.jsonl.gz'):
            cases=r['cases']
            for a,b in zip(cases[::2],cases[1::2]):
                pair=pairs[(a['case'],b['case'])];n=len(pair.first.maze.cells)
                expected=goal_metrics([unpack(v['probe_mask'],n) for v in (a,b)],
                    [unpack(v['source_removed_mask'],n) for v in (a,b)],pair)
                if not (a['signal']['aligned'] and b['signal']['aligned']):
                    for v in expected:v['score']=0.;v['pair_both']=False
                for actual,want in zip((a,b),expected):
                    check_output(actual,True);cross_outputs+=1
                    for k,v in want.items():assert abs(actual['goal'][k]-v)<1e-9
                    cross_goals+=1
            check_balanced(r,'mean');check_junction({**r,'assay':'goal_pulse_removed'})
    ablation_outputs=ablation_goals=0
    if (out/'nonlocal_ablation.jsonl.gz').exists():
        grouped=defaultdict(dict)
        for r in lines(out/'nonlocal_ablation.jsonl.gz'):
            check_output(r);ablation_outputs+=1
            grouped[(r['arm'],r['replicate'])][r['case_id']]=r
        for (arm,rep),rows in grouped.items():
            for (first,second),pair in pairs.items():
                if first not in rows:continue
                a,b=rows[first],rows[second];n=len(pair.first.maze.cells)
                check_junction(dict(arm=arm,replicate=rep,cases=[a,b],assay='nonlocal_removed'),case_key='case_id')
                expected=goal_metrics([unpack(r['probe_mask'],n) for r in (a,b)],
                    [unpack(r['source_removed_mask'],n) for r in (a,b)],pair)
                if not(a['signal']['aligned'] and b['signal']['aligned']):
                    for r in expected:r['score']=0.;r['pair_both']=False
                for actual,want in zip((a,b),expected):
                    for k,v in want.items():assert abs(actual['goal'][k]-v)<1e-9
                    ablation_goals+=1
    junction_factors=defaultdict(Counter);curriculum_training=defaultdict(Counter);capacity_factors=defaultdict(Counter)
    costs=defaultdict(Counter);factors=defaultdict(Counter);phases=defaultdict(Counter);evaluations=responses=work=0
    mutation_counts=defaultdict(Counter);mutation_generations=[];training_groups={}
    def compare_coeval(group,condition,generation):
        if not group:return
        c=mutation_counts[condition];same=changed=children=0
        for identity,(fingerprint,fitness,child_work,child_steps) in group.items():
            parent,birth=ancestry[identity]
            if birth!=generation or parent not in group:continue
            children+=1;c['coeval_new_children']+=1
            different=known[identity]!=known[parent];changed+=different;c['changed_genome']+=different
            unchanged=fingerprint==group[parent][0];same+=unchanged;c['same_recorded_behavior']+=unchanged
            c['changed_genome_same_behavior']+=bool(different and unchanged)
            grew=lengths[identity]>lengths[parent]
            c['coeval_grew']+=grew;c['grew_same_recorded_behavior']+=bool(grew and unchanged)
            c['grew_more_work']+=bool(grew and child_work>group[parent][2]);c['grew_fewer_completed_ticks']+=bool(grew and child_steps<group[parent][3])
            c['crossed128']+=bool(lengths[parent]<=128<lengths[identity]);c['grew_higher_fitness']+=bool(grew and fitness>group[parent][1])

            c['higher_training_fitness']+=fitness>group[parent][1]
            c['lower_training_fitness']+=fitness<group[parent][1]
            c['equal_training_fitness']+=fitness==group[parent][1]
        mutation_generations.append(dict(condition=condition,generation=generation,population=len(group),
            recorded_phenotypes=len({v[0] for v in group.values()}),coeval_children=children,
            changed_genome=changed,same_recorded_behavior=same))
    phase_pools=defaultdict(dict)
    valid_claims=0;valid_shapes={};balanced={};junction_archives={};strict_maxima={};task_maxima={}
    for p in sorted((out/'logs').glob('*/*.evaluations.jsonl.gz')):
        log_path=p;coeval={};coeval_generation=None;coeval_condition=None
        for r in lines(p):
            assert r['id'] in known and r['work']==r['inference_work']+r['probe_work']
            c=costs[r['condition']];c[r['split']+'_responses']+=len(r['cases'])
            c['inference_work']+=r['inference_work'];c['probe_work']+=r['probe_work']
            evaluations+=1;responses+=len(r['cases']);work+=r['work']
            if r['split']=='train':
                if r['generation'] in (15,31,47):phase_pools[(r['condition'],r['generation'])][r['id']]=r
                assert all(oracles[case['case']].maze.split=='train_goal' for case in r['cases'])
                genes=lengths[r['id']];gf=capacity_factors[(r['condition'],'above128' if genes>128 else 'at_most128')]
                gf['organism_evaluations']+=1;gf['sum_genes']+=genes;gf['max_genes']=max(gf['max_genes'],genes)
                gf['valid_normals']+=r['normal_fitness'][0];gf['optimal_normals']+=r['normal_fitness'][1];gf['strict_pairs']+=r['strict_pairs']
                gf['work']+=r['work'];gf['inference_work']+=r['inference_work'];gf['probe_work']+=r['probe_work']
                for row in r['cases']:
                    gf['normal_calls']+=1;gf['normal_steps']+=row['steps'];gf['normal_dispatches']+=row['dispatches'];gf['normal_active']+=row['active']
                    gf['normal_budget_exhaustions']+='budget' in row['status']
                    gf['aligned_probes']+=row['signal']['aligned']
                    gf['regular_goal_inputs']+=row['junction']['eligible']
                training_groups.setdefault((r['condition'],r['generation']),{})[r['id']]=r['strict_pairs']
                if r['generation']!=coeval_generation:
                    compare_coeval(coeval,coeval_condition,coeval_generation);coeval={}
                    coeval_generation=r['generation'];coeval_condition=r['condition']
                phenotype=[(c['status'],c['steps'],c['mask'],c['probe_mask'],c['source_removed_mask'],
                    c['partial'],c['signal']['score'],c['goal']['score'],c['goal']['quality'],c['goal']['specificity']) for c in r['cases']]
                fingerprint=hashlib.sha256(json.dumps(phenotype,separators=(',',':')).encode()).hexdigest()
                coeval[r['id']]=(fingerprint,tuple(r['fitness'][:-1]),r['work'],sum(c['steps'] for c in r['cases']))
            if r['split']=='validation':
                task_candidate=dict(id=r['id'],rank=r['normal_fitness'])
                if r['condition'] not in task_maxima or task_candidate['rank']>task_maxima[r['condition']]['rank']:task_maxima[r['condition']]=task_candidate
                rank=[r['junction'],r['junction_both'],r['balanced'],*r['fitness'][:2]]
                candidate=dict(id=r['id'],rank=rank,generation=r['generation'])
                if r['condition'] not in junction_archives or rank>junction_archives[r['condition']]['rank']:junction_archives[r['condition']]=candidate
                strict_rank=[r['junction_both'],r['junction'],r['balanced'],r['goal'],*r['normal_fitness'][:2]]
                candidate=dict(id=r['id'],rank=strict_rank)
                if r['condition'] not in strict_maxima or strict_rank>strict_maxima[r['condition']]['rank']:strict_maxima[r['condition']]=candidate
                minima=[];family_minima=defaultdict(list);both=[]
                for a,b in zip(r['cases'][::2],r['cases'][1::2]):
                    pair=pairs[(a['case'],b['case'])]
                    if pair.mixed:continue
                    value=min(a['goal']['score'],b['goal']['score']);minima.append(value)
                    family_minima[pair.first.maze.family].append(value);both.append(a['goal']['pair_both'])
                rank=[float(np.mean(minima)),float(np.mean(both)),r['quality'],r['goal']]
                candidate=dict(condition=r['condition'],id=r['id'],generation=r['generation'],rank=rank,
                    balanced_goal=rank[0],both=rank[1],quality=r['quality'],goal=r['goal'],
                    family_balanced={k:float(np.mean(v)) for k,v in family_minima.items()},
                    regular_pair_minima=minima,source_log=str(log_path.relative_to(out)))
                rank.extend(r['fitness'][:2]);candidate['rank']=rank
                assert abs(r['balanced']-rank[0])<1e-12
                if r['condition'] not in balanced or rank>balanced[r['condition']]['rank']:balanced[r['condition']]=candidate
            inference=sum(c['dispatches']+sum(c['reads']) for c in r['cases'])
            probe=sum(sum(c['signal']['dispatches'])+sum(c['signal']['reads']) for c in r['cases'])
            assert r['inference_work']==inference and r['probe_work']==probe
            goals=[c['goal'] for c in r['cases']]
            assert abs(r['goal']-np.mean([g['score'] for g in goals]))<1e-12
            eligible=[bool(oracles[c['case']].path) and c['goal']['aligned'] for c in r['cases']]
            assert abs(r['quality']-np.mean([g['quality'] if e else 0. for g,e in zip(goals,eligible)]))<1e-12
            assert abs(r['specificity']-np.mean([g['specificity'] if e else 0. for g,e in zip(goals,eligible)]))<1e-12
            for c,e in zip(r['cases'],eligible):
                g=c['goal'];quality=g['progress']*g['connected_fraction']*g['source_fraction']/(1+2*g['branches'])
                assert abs(g['quality']-quality)<1e-12
                assert abs(g['specificity']-max(0.,g['progress']-g['cross_progress']))<1e-12
                expected=math.sqrt(g['quality']*g['specificity']) if e else 0.
                assert abs(g['score']-expected)<1e-12
            check_balanced(r);check_junction(r,'junction');check_priority(r,r['objective'])
            jf=junction_factors[r['condition']+'/'+r['split']]
            for a,b in zip(r['cases'][::2],r['cases'][1::2]):
                if not a['junction']['eligible']:continue
                jf['regular_pairs']+=1;jf['strict_both_pairs']+=a['junction']['pair_both']
                jf['sum_pair_min']+=min(a['junction']['score'],b['junction']['score'])
                for row in (a,b):
                    j=row['junction'];jf['eligible_cases']+=1
                    for key in ('prefix','choice','score'):jf['sum_'+key]+=j[key];jf['max_'+key]=max(jf['max_'+key],j[key])
                    for key,positive in (('source_connected_junction',j['connected']),('positive_prefix',j['prefix']>0),
                        ('desired_exit_on',bool(j['desired_on'])),('wrong_exits_suppressed',not j['wrong_on']),
                        ('positive_choice',j['choice']>0),('source_dependent_exit',j['causal']>0),('strict_choice',j['strict'])):
                        jf[key]+=bool(positive)
            if r['split']=='train':
                phase='near1' if r['generation']<16 else 'near2' if r['generation']<32 else 'far'
                condition=r['condition'].split('/');pc=curriculum_training[(condition[1],condition[2],phase)]
                pc['valid']+=sum(c['valid'] for c in r['cases']);pc['normal_cases']+=len(r['cases'])
                for a,b in zip(r['cases'][::2],r['cases'][1::2]):
                    if not a['junction']['eligible']:continue
                    pc['pairs']+=1;pc['strict_both']+=a['junction']['pair_both']
                    pc['normal_both_valid']+=bool(a['valid'] and b['valid'])
                    pc['normal_both_shortest']+=bool(a['optimal'] and b['optimal'])
                    pc['sum_min_j']+=min(a['junction']['score'],b['junction']['score'])
                    pair=pairs[(a['case'],b['case'])];label=decision(pair)
                    pc['sum_goal_distance']+=sum(o.to_goal[label['vertex']] for o in pair.cases)
                    pc['deceptive_pairs']+=any(label['detours'])
            assert r['objective']=='choice'
            partial=source=bonus=0.;valid=optimal=no_path=0
            pressure=r['condition'].split('/')[2]
            alpha=1.
            assert r['alpha']==alpha
            phase='early' if r['generation']<16 else 'middle' if r['generation']<32 else 'late'
            for case in r['cases']:
                oracle=oracles[case['case']];assert oracle.maze.split in ('train_goal','train_near1_goal','train_near2_goal','validation_goal')
                if case['valid']:
                    from cellular_maze_lab import neighbors
                    check_output(case,True);valid_claims+=1
                    mask=unpack(case['mask'],len(oracle.maze.cells));m=oracle.maze;p=m.start;previous=-1;directions=[]
                    while p!=m.goal:
                        q=next(q for q in neighbors(p,m.w,m.h) if mask[q] and q!=previous)
                        directions.append(q-p);previous,p=p,q
                    valid_shapes.setdefault((r['id'],case['case']),dict(condition=r['condition'],id=r['id'],generation=r['generation'],
                        split=r['split'],case=case['case'],edges=len(directions),turns=sum(a!=b for a,b in zip(directions,directions[1:])),
                        optimal=case['optimal'],family=m.family))
                if oracle.path:
                    f=factors[r['condition']+'/'+r['split']];g=case['goal'];f['reachable_responses']+=1
                    if r['split']=='train':
                        phase_counts=phases[r['condition']+'/'+phase];phase_counts['reachable_responses']+=1
                        for label,positive in (('quality',g['quality']>0),('specificity',g['specificity']>0),('joint',g['score']>0)):
                            phase_counts[label]+=int(positive)
                        phase_counts['sum_goal']+=g['score'];phase_counts['sum_quality']+=g['quality'];phase_counts['sum_specificity']+=g['specificity']
                    for label,positive in (('nonempty',g['selected']>0),('connected_growth',g['component']>=3),
                        ('source_dependent_output',g['source_fraction']>0),('positive_quality',g['quality']>0),
                        ('positive_specificity',g['specificity']>0),('positive_goal_score',g['score']>0)):
                        f[label]+=int(positive)
                    for field in ('quality','specificity','score','source_fraction'):
                        f['sum_'+field]+=g[field];f['max_'+field]=max(f['max_'+field],g[field])
                s=case['signal'];expected=max(0.,float(np.mean(list(s['bands'].values())))-s['leakage']) if s['bands'] and s['aligned'] else 0.
                assert abs(expected-s['score'])<1e-9
                assert s['pair_array_bytes']<=80*len(oracle.maze.cells)+65536
                signal_checks+=1;partial+=case['partial'];source+=s['score']
                g=case['goal'];minimum=case['pair_min_goal']
                expected_bonus=case['factor_bonus']  # independently checked pair-wise above
                assert abs(case['factor_bonus']-expected_bonus)<1e-12
                bonus+=expected_bonus
                valid+=case['valid'];optimal+=case['optimal']
                no_path+=case['no_path']-bool(oracle.path and case['status']=='no_path')
            assert r['fitness'][:3]==r['normal_fitness'][:3]==[valid,optimal,no_path]
            assert abs(r['normal_fitness'][3]-round(partial,8))<1e-12
            complete=all(c['valid'] or c['no_path'] for c in r['cases'])
            assert r['fitness'][-1]==r['normal_fitness'][-1]==(-r['inference_work'] if complete else 0)
            assert abs(r['fitness'][4]-(round(partial,8)+source+bonus))<2e-8
        compare_coeval(coeval,coeval_condition,coeval_generation)
    assert work==sum(v['work'] for v in champions.values())
    assert responses==sum(v['maze_evaluations'] for v in champions.values())
    for key,record in balanced.items():
        selected=champions[key]['archives']['balanced']
        assert record['id']==selected['individual']['id'] and record['rank']==selected['rank']
    for key,record in junction_archives.items():
        selected=champions[key]['archives']['junction']
        assert record['id']==selected['individual']['id'] and record['rank']==selected['rank']
    for key,r in strict_maxima.items():
        selected=champions[key]['archives']['choice']
        assert r['id']==selected['individual']['id'] and r['rank']==selected['rank']
    for key,r in task_maxima.items():
        selected=champions[key]['archives']['task']
        assert r['id']==selected['individual']['id'] and r['rank']==selected['rank']
    for condition,saved in champions.items():
        assert set(saved['phase_leaders'])=={'15','31','47'}
        for generation,record in saved['phase_leaders'].items():
            pool=phase_pools[(condition,int(generation))];selected=record['individual']
            assert Genome.from_dict(selected['genome']).digest==known[selected['id']]
            r=pool[selected['id']]
            assert record['fitness']==r['fitness']==max(v['fitness'] for v in pool.values())
            assert record['strict_pairs']==r['strict_pairs'] and record['junction']==r['junction']
            assert record['cases']==[c['case'] for c in r['cases'][::2]]
    phase_outputs=phase_work=0
    if (out/'phase_transfer.jsonl.gz').exists():
        for r in lines(out/'phase_transfer.jsonl.gz'):
            selected=champions[r['condition']]['phase_leaders'][str(r['generation'])]['individual']
            assert r['id']==selected['id'] and r['split'] in ('validation_goal','test_pairs')
            for case in r['cases']:check_output(case,True);phase_outputs+=1
            check_junction(r);check_priority(r,'choice')
            expected=sum(c['dispatches']+sum(c['reads'])+sum(c['signal']['dispatches'])+sum(c['signal']['reads']) for c in r['cases'])
            assert r['work']==expected;phase_work+=expected
        for r in lines(out/'phase_training_control.jsonl.gz'):
            saved=champions[r['condition']]
            if r['selection']=='phase_leader':
                selected=saved['phase_leaders'][str(r['generation'])]['individual']
                original=phase_pools[(r['condition'],r['generation'])][r['id']]
                assert r['fitness']==original['fitness'] and r['cases']==original['cases'] and r['work']==original['work']
            else:selected=saved['frozen' if r['selection']=='frozen_choice' else 'archives']['choice']['individual']
            assert r['id']==selected['id']
            for case in r['cases']:check_output(case,True);phase_outputs+=1
            check_junction(r,'junction');check_priority(r,'choice')
            expected=sum(c['dispatches']+sum(c['reads'])+sum(c['signal']['dispatches'])+sum(c['signal']['reads']) for c in r['cases'])
            assert r['work']==expected;phase_work+=expected
        d=json.loads((out/'diagnostics.json').read_text())
        assert d['phase_work']==phase_work and d['phase_responses']==phase_outputs
    write_json(out/'choice_archive_audit.json',strict_maxima)
    write_json(out/'task_archive_audit.json',task_maxima)
    ancestry_outputs=ancestry_nodes=0;ancestry_work=0
    if (out/'strict_validation_archive.json').exists():
        strict=json.loads((out/'strict_validation_archive.json').read_text())['records']
        for key,r in strict.items():
            assert r['id']==strict_maxima[key]['id'] and r['rank']==strict_maxima[key]['rank']
            assert Genome.from_dict(r['individual']['genome']).digest==known[r['id']]
        for record in json.loads(gzip.open(out/'choice_ancestry.json.gz','rt').read()):
            pair=pairs[(record['first'],record['second'])];assert pair.first.maze.split=='validation_goal'
            assert record['decision']==decision(pair)
            previous=None;parent=None
            for node in record['nodes']:
                item=node['individual'];assert Genome.from_dict(item['genome']).digest==known[item['id']]
                if parent is not None:assert item['parent']==parent
                genes=item['genome']['genes'];changes=[] if previous is None else [dict(index=i,before=previous[i] if i<len(previous) else None,
                    after=genes[i] if i<len(genes) else None) for i in range(max(len(previous),len(genes)))
                    if (previous[i] if i<len(previous) else None)!=(genes[i] if i<len(genes) else None)]
                assert changes==node['gene_row_changes'];previous=genes;parent=item['id'];ancestry_nodes+=1
                check_junction(node,'balanced')
                assert node['strict_both']==node['cases'][0]['junction']['pair_both']
                for case in node['cases']:check_output(case,True);ancestry_outputs+=1
                expected=sum(r['dispatches']+sum(r['reads'])+sum(r['signal']['dispatches'])+sum(r['signal']['reads']) for r in node['cases'])
                assert expected==node['work'];ancestry_work+=expected
            assert record['nodes'][-1]['strict_both']==1
            for result in record['interventions']:
                check_junction(result)
                for case in result['cases']:check_output(case,True);ancestry_outputs+=1
                expected=sum(r['dispatches']+sum(r['reads'])+sum(r['signal']['dispatches'])+sum(r['signal']['reads']) for r in result['cases'])
                assert expected==result['work'];ancestry_work+=expected
        if (out/'diagnostics.json').exists():
            d=json.loads((out/'diagnostics.json').read_text())
            assert d['ancestry_work']==ancestry_work and d['ancestry_responses']==ancestry_outputs
    write_json(out/'junction_archive_audit.json',junction_archives)
    write_json(out/'choice_diagnostics.json',choice_records)
    write_json(out/'entry_diagnostics.json',dict(scope='Additional diagnostic specified during V11 training before final inspection, using saved rasters only. Remove desired exits and check source can still reach the junction, and whether that incoming path is shortest. Does not alter registered strict fitness or primary results.',records=entry_choices))
    write_json(out/'balanced_archive_audit.json',dict(
        scope='Verifies the preregistered common balanced archive against every validation nomination.',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),records=balanced))
    result=dict(all_checks_passed=True,mutation_trace_checks=trace_checks,audit_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,phase_reassessed_outputs=phase_outputs,phase_work=phase_work,verified_priority_records=priority_checks,verified_choice_archives=len(strict_maxima),verified_task_archives=len(task_maxima),ancestry_reassessed_outputs=ancestry_outputs,ancestry_nodes=ancestry_nodes,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),junction_raster_checks=junction_checks,verified_junction_archives=len(junction_archives),elapsed_seconds=time.perf_counter()-started,source_files=len(env['source_sha256']),verified_packed_files=packed_files,external_random_ancestors=len(ancestors),
        new_individuals=len(ancestry),max_genes=maximum_genes,unique_inputs=len(digests),unique_layouts=len(layouts),
        previous_layouts=len(previous_layouts),primary_test_layouts=sum(oracles[v[0]].maze.split=='test_goal' for v in layouts.values()),
        paired_final_layouts=sum(oracles[v[0]].maze.split=='test_pairs' for v in layouts.values()),
        verified_balanced_archives=len(balanced),junction_diagnostic_pairs=len(junctions),
        reassessed_primary_outputs=primary,replayed_selected_outputs=replayed,reassessed_paired_outputs=paired_outputs,raster_goal_checks=goal_checks,
        reassessed_ablation_outputs=ablation_outputs,ablation_goal_checks=ablation_goals,
        reassessed_cross_input_outputs=cross_outputs,cross_input_goal_checks=cross_goals,
        training_signal_arithmetic_checks=signal_checks,training_fitness_checks=evaluations,
        reassessed_training_valid_claims=valid_claims,
        goal_switch_arithmetic_checks=switch_checks,validation_timecourse_checks=timecourse_checks,
        reassessed_ancestry_rotation_outputs=turned_outputs,
        normal_maze_evaluations=responses,developmental_probe_runs=2*responses,charged_work=work,
        inference_work=sum(v['inference_work'] for v in costs.values()),probe_work=sum(v['probe_work'] for v in costs.values()))
    # Specified during V11 training, before final inspection: count actual
    # reproductive use of strict-choice genotypes on their coeval batch.
    births=defaultdict(list)
    for identity,(parent,birth) in ancestry.items():
        births[('/'.join(identity.split('/')[:-1]),birth)].append((identity,parent))
    reproduction=[]
    for (condition,generation),group in sorted(training_groups.items()):
        saved=champions[condition];protected_digests={Genome.from_dict(r['genome']).digest for r in saved['protected']}
        positive={identity for identity,K in group.items() if K>0}
        novel={identity for identity in positive if known[identity] not in protected_digests}
        if (condition,generation+1) in training_groups:next_ids=set(training_groups[(condition,generation+1)])
        else:
            checkpoint=json.loads((out/'checkpoints'/(condition.replace('/','_')+'.json')).read_text())
            assert checkpoint['next_generation']==generation+1;next_ids={r['id'] for r in checkpoint['population']}
        children=births[(condition,generation+1)]
        mutant_parents=[parent for _,parent in children if parent in group]
        reproduction.append(dict(condition=condition,generation=generation,population=len(group),
            strict_pair_responses=sum(group.values()),positive_individuals=len(positive),positive_genotypes=len({known[i] for i in positive}),
            positive_unprotected_genotype_individuals=len(novel),retained_positive=len(positive&next_ids),retained_unprotected_positive=len(novel&next_ids),
            mutated_offspring=len(mutant_parents),offspring_from_positive=sum(i in positive for i in mutant_parents),
            offspring_from_unprotected_positive=sum(i in novel for i in mutant_parents),
            distinct_positive_breeding_parents=len(set(mutant_parents)&positive),distinct_unprotected_positive_breeding_parents=len(set(mutant_parents)&novel)))
    trajectories=[]
    for topology in ('local','evolved'):
        for rep in range(3):
            a=f'growth/{topology}/cap128/{rep}';b=f'growth/{topology}/cap256/{rep}'
            first_active=first_different=None;records=[]
            generations=sorted(g for condition,g in training_groups if condition==a and (b,g) in training_groups)
            for generation in generations:
                left=training_groups[(a,generation)];right=training_groups[(b,generation)]
                same=[known[i] for i in left]==[known[i] for i in right]
                active=any(left.values()) or any(right.values())
                if first_different is None and not same:first_different=generation
                if first_active is None:
                    if active:first_active=generation
                records.append(dict(generation=generation,same_ordered_population=same,
                    cap128_strict_responses=sum(left.values()),cap256_strict_responses=sum(right.values())))
            left_checkpoint=json.loads((out/'checkpoints'/(a.replace('/','_')+'.json')).read_text())
            right_checkpoint=json.loads((out/'checkpoints'/(b.replace('/','_')+'.json')).read_text())
            final_rng_equal=left_checkpoint['rng_state']==right_checkpoint['rng_state']
            final_population_equal=[known[r['id']] for r in left_checkpoint['population']]==[known[r['id']] for r in right_checkpoint['population']]
            trajectories.append(dict(topology=topology,replicate=rep,identical_final_rng=final_rng_equal,
                identical_final_population=final_population_equal,first_strict_opportunity=first_active,
                first_population_divergence=first_different,records=records))
    write_json(out/'priority_trajectories.json',trajectories)
    write_json(out/'reproductive_priority.json',dict(
        scope='Diagnostic specified during training, before final inspection. Coeval strict-both K on each rotating training batch, followed by actual next-population/parent use. Protected means genotype matches a fixed protected variant. Counts are repeated opportunities, not independent discoveries.',
        records=reproduction,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    write_json(out/'mutation_behavior.json',dict(
        scope='Diagnostic specified during training, before final inspection; newly born children whose parent is evaluated on the same rotating training batch only.',
        definition='Recorded phenotype fingerprint includes normal/probe binary rasters, normal status/steps, partial/source/goal metrics. Junction scores are deterministic from those rasters on a fixed batch. Work/active counters and hidden trajectories can differ. Fitness comparisons omit the final cost tie-break.',
        counts=mutation_counts,generations=mutation_generations,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    write_json(out/'junction_factors.json',junction_factors)
    write_json(out/'mutation_events.json',mutation_events)
    write_json(out/'capacity_training.json',[dict(condition=c,size_group=g,**v) for (c,g),v in sorted(capacity_factors.items())])
    write_json(out/'growth_training_phases.json',[dict(topology=t,arm=a,phase=p,**v) for (t,a,p),v in sorted(curriculum_training.items())])
    write_json(out/'training_cost.json',costs);write_json(out/'training_factors.json',factors);write_json(out/'training_phases.json',phases)
    write_json(out/'training_valid_shapes.json',list(valid_shapes.values()))
    write_json(out/'probe_route_diagnostics.json',probe_routes)
    write_json(out/'junction_diagnostics.json',junctions)
    write_json(out/'verification.json',result)
    print(json.dumps(result,indent=2));return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/capacity_growth')
    parser.add_argument('--repack',action='store_true');args=parser.parse_args()
    if args.repack:repack(args.out)
    audit(args.out)
