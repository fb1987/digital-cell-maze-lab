"""M25 common fresh cases plus fixed old-skill panel, identical queries across policies."""
import hashlib
from copy import deepcopy
from collections import defaultdict
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz
from .dormant_evolution_data import raw_training as previous_raw
from .restoration_data import observed_build,confirmation
OUT=ROOT/'results/skill_integration'
PRIOR=ROOT/'results/dormant_evolution'


def validation(seed,previous):
    d=deepcopy(readz(PRIOR/'validation.json.gz'));d.update(generation=0,new_layouts=[],reused_development=True)
    return d


def retention_panel(data=None):
    d=validation(None,None) if data is None else data;result={}
    key=lambda c:hashlib.sha256(('M25-retention/'+c).encode()).hexdigest()
    for rep in range(3):
        ids=d['queries'][f'{rep}/enabled'];meta=d['metadata']
        # Metadata-only round robin over length bins, never candidate success.
        groups=defaultdict(list)
        for c in ids:
            if meta[c]['family']=='corridor':groups[meta[c]['length_bin']].append(c)
        groups={k:sorted(v,key=key) for k,v in sorted(groups.items())};corr=[]
        while len(corr)<12:
            for k,v in groups.items():
                if v and len(corr)<12:corr.append(v.pop(0))
        pairgroups=defaultdict(list)
        for c in ids:
            m=meta[c]
            if m['family']=='paired':pairgroups[(m['base'],m['pose'])].append(c)
        strata=defaultdict(list)
        for pair,cs in pairgroups.items():
            assert len(cs)==2;m=meta[cs[0]];strata[(m['graph'],m['prefix'])].append(sorted(cs,key=key))
        strata={k:sorted(v,key=lambda cs:key(cs[0])) for k,v in sorted(strata.items())}
        # Different graph families first; four complete units, not four half routes.
        ordered=sorted(strata,key=lambda k:(k[1],k[0]));paired=[]
        for k in ordered:
            if len(paired)==8:break
            paired+=strata[k][0]
        disc=[]
        for family in ('disconnected','ordinary_disconnected'):
            cs=sorted([c for c in ids if meta[c]['family']==family],key=key);disc+=cs[:2]
        selected=corr+paired+disc;assert len(selected)==len(set(selected))==24
        result[str(rep)]=selected
    return result


def raw_training(seed,g,previous):
    d=previous_raw(seed,g,previous);panel=readz(OUT/'retention_panel.json.gz');old=validation(None,None)
    mazes={m['case_id']:m for m in d['mazes']};previous_mazes={m['case_id']:m for m in old['mazes']};d['retention_queries']={}
    for key,queries in d['queries'].items():
        extra=panel[key.split('/')[0]];assert len(queries)==96 and not set(extra)&set(queries)
        d['queries'][key]=queries+extra;d['retention_queries'][key]=extra
        for c in extra:mazes[c]=previous_mazes[c];d['metadata'][c]=old['metadata'][c]
    d['mazes']=list(mazes.values());assert all(len(q)==120 for q in d['queries'].values())
    return d


def training(seed,g,previous):
    return observed_build(lambda s,p:raw_training(s,g,p),seed,previous)
