"""M18 evaluator adapter; candidate VM never accesses oracle data."""
import time
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import record
from .exploration_continuation import organism as base_organism
from .connected_genome import Genome
from .connected_runtime import Organism
_cache={}
def organism(model):
    return Organism(Genome.from_dict(model['genome'])) if model['representation']=='connected' else base_organism(model)

def evaluate_task(spec,maze_rows,data_hash):
    global _cache
    start=time.process_time()
    if _cache.get('hash')!=data_hash:
        cases=cases_from_manifest(maze_rows);_cache=dict(hash=data_hash,cases=cases,checker=Checker(cases))
    entries=[];seconds=work=calls=0
    for e in spec:
        org=organism(e['model']);rows=[];entry_seconds=0.;entry_work=0
        for cid in e['queries']:
            o=_cache['cases'][cid];m=o.maze;t=time.perf_counter();response=org.react(m.cells,m.w,m.h,m.start,m.goal)
            elapsed=time.perf_counter()-t;seconds+=elapsed;entry_seconds+=elapsed;r=record(response,o);_cache['checker'].row(r);rows.append(r)
            charged=r['reads']+r['dispatches']+r['exposure_checks'];work+=charged;entry_work+=charged;calls+=1
        entries.append(dict(aliases=e['aliases'],rows=rows,candidate_seconds=entry_seconds,work=entry_work,calls=len(rows)))
    return dict(entries=entries,calls=calls,work=work,candidate_seconds=seconds,cpu_seconds=time.process_time()-start,independently_graded=calls)

