"""V12G independent graph/raster arithmetic plus deterministic lineage/RNG replay."""
import gzip,json,time,resource,random
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from io import StringIO
from collections import defaultdict
import numpy as np
from maze_evolution.foundation_calibration import ROOT,write_json
from maze_evolution.foundation_study import read_compressed
from maze_evolution.foundation_study_verify_core import Checker
from maze_evolution.foundation_data import layout_hash,transform_maze
from maze_evolution.fork_data import OUT,FIXTURES,load,exclusions
from maze_evolution.fork_study import sha,lines
from maze_evolution.fork_search import Search,digest
from maze_evolution.fork_confirm import evaluate_model
from maze_evolution.growth import Individual,replay_mutation
from maze_evolution.regulatory_search import Evaluation
from maze_evolution.route_confirmation_audit import graph_distances,adjacent
from maze_evolution.evaluator import Maze


def independent_branch(mask,o,side,partial):
    lab=o._foundation_label
    if lab is None:return dict(prefix=0.,desired=False,wrong=0.,strict=False,score=partial)
    selected=mask.copy();selected[lab['exits']]=0
    ds=graph_distances(selected,o.maze.w,o.maze.start)
    reached=ds[lab['vertex']]==lab['distance'];prefix=0
    for v in lab['prefix']:
        if ds[v]<0:break
        prefix+=1
    p=max(0.,(prefix-1)/lab['distance'])
    if not reached:p=min(p,.999)
    good=lab['allowed'][side];bad=[v for v in lab['exits'] if v not in good]
    desired=sum(int(mask[v]) for v in good)==1;leak=sum(int(mask[v]) for v in bad)/max(1,len(bad))
    return dict(prefix=p,desired=desired,wrong=leak,strict=bool(reached and desired and not leak),score=.2*p+.4*p*desired+.35*p*desired*(1-leak)+.05*partial)


def verify_rows(checker,rows):
    checker.rows(rows)
    for k,r in enumerate(rows):
        o=checker.cases[r['case']];mask=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),np.uint8),bitorder='little')[:len(o.maze.cells)]
        expected=independent_branch(mask,o,k%2,r['partial'])
        for field,value in expected.items():
            assert abs(r['branch'][field]-value)<1e-10,(r['case'],field)
        assert r['fork']==(o._foundation_label is not None)
    for i in range(0,len(rows),2):
        a,b=rows[i:i+2];strict=a['fork'] and b['fork'] and a['branch']['strict'] and b['branch']['strict']
        for r in (a,b):
            assert r['pair_strict']==strict
            assert r['paired_branch']==min(a['branch']['score'],b['branch']['score'])


def independent_fitness(rows,policy):
    v=sum(r['valid'] for r in rows);o=sum(r['optimal'] for r in rows)
    n=sum(r['no_path']-int(r['reachable'] and r['status']=='no_path') for r in rows)
    p=sum(r['fork'] and r['pair_optimal'] for r in rows)//2
    k=sum(r['pair_strict'] for r in rows)//2 if policy=='branch' else 0
    shaping=round(sum((r['branch']['score']+r['paired_branch']) if policy=='branch' else r['partial']+r['paired_partial'] for r in rows),8)
    w=-sum(r['reads']+r['dispatches'] for r in rows) if all(r['valid'] or r['no_path'] for r in rows) else 0
    return [v,o,n,p,k,shaping,w]


def run():
    assert sha(ROOT/'maze_evolution/fork_audit.py')=='4a1366d9ec8f76a13ea315bf5e857f431dddb1b49f645503b6f5453f9941eaf5'
    t=time.perf_counter();summary=json.loads((OUT/'search_summary.json').read_text());counts=defaultdict(int)
    for kind in ('source_sha256','input_sha256'):
        for p,h in summary[kind].items():assert sha(ROOT/p)==h,p;counts[kind]+=1
    assert sha(OUT/'frozen_selections.json.gz')==summary['frozen_sha256']
    previous={layout_hash(Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'])) for r in exclusions()}
    assert len(previous)==125008
    allcases={};allgroups=[]
    for path in (FIXTURES,OUT,OUT/'confirmation'):
        cases,groups=load(path);layouts={layout_hash(o.maze) for o in cases.values()}
        assert not previous&layouts;previous|=layouts;allcases.update(cases);allgroups+=groups
        for g in groups:
            for sym,pair in enumerate(g.pairs):
                for o,base in zip(pair.cases,g.pairs[0].cases):
                    m=transform_maze(base.maze,sym)
                    assert (m.cells,m.start,m.goal)==(o.maze.cells,o.maze.start,o.maze.goal)
                    ds=graph_distances(o.maze.cells,o.maze.w,o.maze.start)
                    dg=graph_distances(o.maze.cells,o.maze.w,o.maze.goal)
                    assert ds==o._from_start and dg==o.to_goal
                    assert len(o.path)==(ds[o.maze.goal]+1 if ds[o.maze.goal]>=0 else 0)
                    counts['graph_cases']+=1
                a,b=pair.cases;lab=a._foundation_label
                if lab:
                    assert a.maze.cells==b.maze.cells and a.maze.start==b.maze.start
                    assert lab['prefix'][0]==a.maze.start and lab['prefix'][-1]==lab['vertex']
                    assert len(lab['prefix'])-1==lab['distance']==a._from_start[lab['vertex']]
                    assert all(q in list(adjacent(p,a.maze.w,len(a.maze.cells))) for p,q in zip(lab['prefix'],lab['prefix'][1:]))
                    exits={q for q in adjacent(lab['vertex'],a.maze.w,len(a.maze.cells)) if a.maze.cells[q] and q!=lab['incoming']}
                    assert exits==set(lab['exits']) and not set(lab['allowed'][0])&set(lab['allowed'][1])
                    for side,o in enumerate(pair.cases):assert set(lab['allowed'][side])=={q for q in exits if o.to_goal[q]==o.to_goal[lab['vertex']]-1}
                    counts['decision_labels']+=1
    checker=Checker(allcases);states=read_compressed(OUT/'initial_states.json.gz');final=read_compressed(OUT/'checkpoint.latest.json.gz')
    from maze_evolution.fork_study import parents
    from maze_evolution.fork_data import SEED
    from maze_evolution.datasets import seed_for
    from maze_evolution.growth import random_genome
    source_states,c,d=parents()
    for state in states:
        cfg=state['config'];rep=cfg['replicate'];topology=cfg['topology']
        if cfg['origin']=='fresh':
            rng=random.Random(seed_for(SEED,'founders',rep,0))
            for item in state['population']:
                assert random_genome(rng,True)==Individual.load(item).genome
                assert item['parent'] is None
                counts['fresh_founders_reproduced']+=1
            assert json.loads(json.dumps(rng.getstate()))==state['rng_state']
            assert not state['protected']
        else:
            parent=next(x for x in source_states if x['config']['study']=='foundation_pair_current' and x['config']['method']=='evolution' and x['config']['topology']==topology and x['config']['replicate']==rep)
            allowed=[c[f'foundation_study/{topology}/fresh/evolution/{rep}'],d[f'foundation_study/{topology}/fresh/evolution/{rep}']]+[x for x in source_states if x['config']['method']=='evolution' and x['config']['topology']==topology and x['config']['replicate']==rep]
            anchors=[];seen=set()
            for old in allowed:
                for item in [old['champion']]+[a['item'] for a in old['skills'].values()]+[a['item'] for a in old.get('common_archives',{}).values()]:
                    dna=Individual.load(item).genome.digest
                    if dna not in seen:seen.add(dna);anchors.append(item)
            assert anchors==state['protected']
            lookup={i['id']:i for i in parent['population']+anchors}
            assert all(lookup[i['id']]==i for i in state['population'])
            assert parent['rng_state']==state['rng_state'] and parent['next_generation']==1365
            counts['carry_populations_verified']+=1
    individuals={i['id']:Individual.load(i) for s in states for i in s['population']+s['protected']}
    for s in states:
        for i in s['protected']:assert 'positive_control' not in i['id']
    searches={s['key']:Search(s,StringIO(),StringIO()) for s in states}
    aliases={}
    for s in searches.values():
        k=(s.config['origin'],s.config['topology'],s.config['replicate']);aliases.setdefault(k,[]).append(s)
    for rec in lines(OUT/'initial_evaluations.jsonl.gz'):
        verify_rows(checker,rec['cases']);s=searches[rec['condition']]
        assert rec['fitness']==independent_fitness(rec['cases'],s.config['policy'])
        s.responses+=len(rec['cases']);s.work+=rec['work'];s.archive(individuals[rec['id']],Evaluation(tuple(rec['fitness']),[],(),rec['cases'],rec['work']))
        counts['fitness_records']+=1
    from copy import deepcopy
    for group in aliases.values():
        for s in group:s.archives=deepcopy(group[0].archives);s.frozen=deepcopy(s.archives)
    for segment in final['segments']:
        generation=segment['generation'];registry=list(lines(OUT/segment['files'][0]));evaluations=list(lines(OUT/segment['files'][1]))
        newborn={r['id']:r for r in registry};bycondition=defaultdict(list)
        for rec in evaluations:
            bycondition[rec['condition']].append(rec);verify_rows(checker,rec['cases'])
            assert rec['fitness']==independent_fitness(rec['cases'],searches[rec['condition']].config['policy'])
            assert rec['work']==sum(r['dispatches']+r['reads'] for r in rec['cases']);counts['fitness_records']+=1
        for r in registry:
            item=Individual.load(r)
            if item.parent:
                assert replay_mutation(individuals[item.parent].genome,r['events'],256)==item.genome;counts['mutations']+=1
            individuals[item.identity]=item
        # Deterministically replay every elite/parent choice, fresh draw, mutation and
        # RNG transition using verified saved fitness, without new candidate inference.
        for key,s in searches.items():
            expected=iter(bycondition[key]);written=StringIO();s.registry=written
            def replay_eval(item,pairs,split):
                rec=next(expected);assert (rec['id'],rec['split'],rec['generation'])==(item.identity,split,generation)
                rows=rec['cases'];s.responses+=len(rows);s.work+=rec['work']
                values=[(int(r['valid'] or r['no_path']),int(r['optimal'] or r['no_path']),int(r['pair_optimal'] and r['fork']),int(r['pair_strict']) if s.config['policy']=='branch' else 0,(r['branch']['score']+r['paired_branch']) if s.config['policy']=='branch' else (r['partial']+r['paired_partial'])) for r in rows]
                return Evaluation(tuple(rec['fitness']),values,tuple_tree(rec['descriptor']),rows,rec['work'])
            from maze_evolution.regulatory_search import tuple_tree
            s.evaluate=replay_eval;s.step(None,None)
            assert next(expected,None) is None
            for line in written.getvalue().splitlines():
                r=json.loads(line);assert r==newborn[r['id']];counts['births_replayed']+=1
        # Only the next population, protected anchors and archives can be future
        # parents. Release historical program objects after their mutations were
        # checked; all raw records remain on disk. No audit coverage is removed.
        individuals={i.identity:i for state in searches.values() for i in
            state.population+state.protected+[Individual.load(a['item']) for a in state.archives.values()]}
        if generation%8==0:print(json.dumps(dict(audited_generation=generation,rasters=checker.rasters,seconds=round(time.perf_counter()-t,1))),flush=True)
    for state in final['states']:
        assert json.loads(json.dumps(searches[state['key']].state()))==state,state['key']
        counts['final_states_replayed']+=1
    counts['graded_search_rasters']=checker.rasters
    # Complete final output replays, including success-conditioned interventions.
    models=read_compressed(OUT/'confirmation/models.json.gz')['models'];case_to_pair={p.first.maze.case_id:p for g in allgroups for p in g.pairs}
    for filename in ('outputs.jsonl.gz','ablations.jsonl.gz'):
        for rec in lines(OUT/'confirmation'/filename):
            rows=rec['rows'];verify_rows(checker,rows)
            pairs=[case_to_pair[rows[i]['case']] for i in range(0,len(rows),2)]
            model=models[rec['model']];ev=evaluate_model(Individual.load(model['item']),pairs,model['topology'],rec.get('mode','normal'))
            assert json.loads(json.dumps(ev.rows))==rows;counts['final_candidate_replays']+=len(rows)
    for rec in lines(OUT/'confirmation/baselines.jsonl.gz'):
        for r in rec['rows']:checker.row(r);counts['baseline_rasters']+=1
    for rec in lines(FIXTURES/'calibration.jsonl.gz'):
        verify_rows(checker,rec['rows']);counts['calibration_rasters']+=len(rec['rows'])
    from maze_evolution.foundation_study_verify_core import grade
    from maze_evolution.runtime import STATUSES
    for r in json.loads((FIXTURES/'bfs.json').read_text()):
        o=allcases[r['case']];m=o.maze
        mask=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),np.uint8),bitorder='little')[:len(m.cells)]
        graded=grade(np.frombuffer(m.cells,np.uint8),m.w,m.start,m.goal,np.array(o.to_goal,np.int32),np.array(o._from_start,np.int32),len(o.path),mask,STATUSES.index(r['status']))
        assert graded[1] or graded[2];counts['calibration_bfs_rasters']+=1
    for record in json.loads((FIXTURES/'synthetic.json').read_text()):
        o=allcases[record['case']];lab=o._foundation_label
        side=0 if '/a/d4-' in o.maze.case_id else 1
        for name,vertices in (('blank',[]),('prefix',lab['prefix']),('leaking',lab['prefix']+lab['exits']),('choice',lab['prefix']+lab['allowed'][side]),('route',o.path)):
            mask=np.zeros(len(o.maze.cells),np.uint8);mask[vertices]=1;m=o.maze
            graded=grade(np.frombuffer(m.cells,np.uint8),m.w,m.start,m.goal,np.array(o.to_goal,np.int32),np.array(o._from_start,np.int32),len(o.path),mask,0)
            expected=independent_branch(mask,o,side,graded[4])
            assert all(abs(record['values'][name][field]-value)<1e-10 for field,value in expected.items())
            counts['synthetic_scores']+=1
    assert sum(s.responses for s in searches.values())==summary['responses']
    assert sum(s.work for s in searches.values())==summary['work']
    # Matched pressure outcomes: genealogy IDs differ by namespace; compare DNA and RNG.
    differences=[]
    for origin in ('carry','fresh'):
        for topology in ('local','evolved'):
            for rep in range(3):
                a=searches[f'fork/{origin}/{topology}/current/evolution/{rep}'];b=searches[f'fork/{origin}/{topology}/branch/evolution/{rep}']
                different=[i for i,(x,y) in enumerate(zip(a.history,b.history)) if x['population_sha256']!=y['population_sha256']]
                differences.append(dict(origin=origin,topology=topology,replicate=rep,different_generations=len(different),first_difference=different[0] if different else None,current_top_sets_differ=sum(h['top_sets_differ'] for h in a.history),branch_top_sets_differ=sum(h['top_sets_differ'] for h in b.history)))
    result=dict(audit_variant='bounded parent-object retention; identical grading and replay coverage',audit_source_sha256=sha(Path(__file__)),all_checks_passed=True,counts=dict(counts),layout_total=len(previous),pressure_differences=differences,search_summary_sha256=sha(OUT/'search_summary.json'),confirmation_summary_sha256=sha(OUT/'confirmation/summary.json'),seconds=time.perf_counter()-t,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(OUT/'verification.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':run()
