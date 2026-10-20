"""Post-registration descriptive summaries only; never used for selection."""
import sys,json,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.family_evolution_study import *

def main():
    ex=json.loads((OUT/'search_execution.json').read_text());assert ex['complete']
    states=read_compressed(OUT/'next_states.json.gz');choices=read_compressed(OUT/'choices.json.gz')
    metrics=read_compressed(OUT/'confirmation/metrics.json.gz');a=read_compressed(OUT/'analysis.json.gz')
    families={}
    for pool in read_compressed(OUT/'pools.json.gz').values():families.update(pool['families'])
    parents={};series={k:[] for k in states};mutations=0;births=0
    for e in lines(OUT/'reproduction.jsonl.gz'):
        series[e['key']].append(dict(generation=e['generation']+1,reserved_variants=e.get('retention',{}).get('family_reserved',0),**e['families']))
        for b in e['births']:
            families[b['item']['id']]=b['family']
            parents[b['item']['id']]=b['parents'][0] if b['parents'] else None
            mutations+=b['mutation'] is not None;births+=1
    def ancestry(identity):
        depth=0;chain=[]
        while identity in parents:
            chain.append(identity)
            if parents[identity] is None:break
            depth+=1;identity=parents[identity]
        return dict(z_mutation_steps=depth,z_root=identity,z_chain=chain)
    counts={}
    for key,s in states.items():
        p=s['archives']['primary'];pid=choices['aliases'][key+'/primary'];m=metrics[pid]
        counts[key]=dict(identity=p['item']['id'],genes=len(p['item']['genome']['genes']),birth=p['item']['birth'],nomination=p['generation'],metrics=m,**ancestry(p['item']['id']))
    diversity={}
    from itertools import combinations
    from maze_evolution.family_reservoir import distance
    for key,state in states.items():
        protected={r['id'] for r in state['protected']};groups={}
        for raw in state['population'][:44 if state['arm']!='frozen' else 96]:
            if raw['id'] in protected:continue
            i=Individual.load(raw);rec=dict(genotype=i.genome.digest,gene_ids=state['gene_ids'][i.identity],genes=raw['genome']['genes'])
            groups.setdefault(state['families'][i.identity],[]).append(rec)
        ds=[distance(x,y) for members in groups.values() for x,y in combinations(members,2) if x['genotype']!=y['genotype']]
        diversity[key]=dict(retained_nonprotected=sum(map(len,groups.values())),related_distinct_pairs=len(ds),mean_inherited_locus_distance=sum(ds)/len(ds) if ds else None,largest_retained_family=max(map(len,groups.values())))
    nominations={k:dict(identities=[],families=[]) for k in states}
    stages={n:dict(records=0,calls=0,seconds=0.,work=0) for n in ('train','validation')}
    pattern=re.compile(r'"stage":"([^"]+)".*?"seconds":([0-9.eE+\-]+),"work":([0-9]+)')
    for path in sorted((OUT/'train').glob('g*/responses.jsonl.gz')):
        with gzip.open(path,'rt') as f:
            for line in f:
                match=pattern.search(line[:700]);assert match
                stage,secs,work=match.groups()
                if stage=='validation':
                    key=re.search(r'"key":"([^"]+)"',line[:700]).group(1);identity=re.search(r'"id":"([^"]+)"',line[:700]).group(1)
                    nominations[key]['identities'].append(identity);nominations[key]['families'].append(families[identity])
                v=stages[stage];v['records']+=1;v['calls']+=12 if stage=='train' else 3872;v['seconds']+=float(secs);v['work']+=int(work)
    assert sum(v['calls'] for v in stages.values())+ex['initial_budget']['calls']==ex['budget']['calls']
    assert abs(sum(v['seconds'] for v in stages.values())+ex['initial_budget']['seconds']-ex['budget']['seconds'])<1e-5
    packet=dict(nomination_coverage={k:dict(nominations=len(v['identities']),distinct_identities=len(set(v['identities'])),distinct_families=len(set(v['families'])),**v) for k,v in nominations.items()},search_stages=stages,retained_diversity=diversity,search=ex,confirmation=json.loads((OUT/'confirmation/execution.json').read_text()),primaries=counts,family_trajectories=series,total_births=births,total_mutations=mutations,replicated=a['replicated'])
    compressed_json(OUT/'descriptive_summary.json.gz',packet)
    for origin in ('carry','fresh'):
        for arm in ARMS:
            mm=[counts[f'{origin}/{r}/{arm}']['metrics'] for r in range(3)]
            print(origin,arm,{n:[m[n] for m in mm] for n in ('prefix4','prefix8','cycle','positive','pairs','ordinary','corridors','no_path','false_no_path')})
    print('search',ex['generations'],ex['wall_seconds'],'births',births,'mutations',mutations)

if __name__=='__main__':main()
