"""M13 explicit reuse of M11 development panels; no old confirmation reuse."""
from copy import deepcopy
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz
from .retention_pressure_data import training as fresh_training, confirmation

OUT=ROOT/'results/mutation_scope'

def panels():
    result=deepcopy(readz(OUT/'source_panels.json.gz')['panels'])
    # Independent M11 panels used local case names. Namespace ONLY identities
    # when combining them; preserve cells/endpoints/seeds/layout hashes exactly.
    for rep,p in enumerate(result):
        prefix=f'm13/reused/{rep}/'
        for m in p['mazes']:m['case_id']=prefix+m['case_id']
        for m in p['metadata'].values():
            m['base']=prefix+m['base'];m['template']=prefix+m['template']
        p['metadata']={prefix+c:m for c,m in p['metadata'].items()}
        p['queries']=[prefix+c for c in p['queries']]
        p['methods']={a:[prefix+c for c in q] for a,q in p['methods'].items()}
    return result

def validation(seed,previous):
    # Seed is recorded for provenance only: these exact development panels were
    # generated and frozen in M11, before its confirmation. No case regeneration.
    ps=panels();mazes={};meta={};queries={}
    for rep,p in enumerate(ps):
        mazes.update({m['case_id']:m for m in p['mazes']});meta.update(p['metadata'])
        for arm in ('focused','broad'):queries[f'{rep}/{arm}']=p['methods']['bank']
    return dict(kind='assessment',generation=0,mazes=list(mazes.values()),metadata=meta,
        queries=queries,new_layouts=[],reused_development=True,source='M11 frozen paired panels')

def training(seed,g,previous):
    base=fresh_training(seed,g,previous)
    common=base['queries']['rotating'];assert len(common)==48
    persistent=validation(None,None);maze_map={m['case_id']:m for m in base['mazes']}
    maze_map.update({m['case_id']:m for m in persistent['mazes']})
    meta=dict(base['metadata']);meta.update(persistent['metadata']);queries={};fixed={}
    for key,ids in persistent['queries'].items():
        fixed[key]=[c for c in ids if meta[c]['family'] in ('ordinary_perfect','ordinary_random')]
        assert len(fixed[key])==48 and not set(common)&set(fixed[key])
        queries[key]=common+fixed[key]
    queried=set().union(*(set(q) for q in queries.values()))
    # Only queried rasters are materialized; every generated/rejected layout stays
    # in new_layouts, including the unused M10-control draws.
    base.update(queries=queries,mazes=[m for c,m in maze_map.items() if c in queried],
        metadata={c:meta[c] for c in queried},common_queries=common,persistent_queries=fixed,
        reused_development=True)
    return base
