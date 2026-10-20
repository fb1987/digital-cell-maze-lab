"""Post-hoc static and mating-log diagnostics; zero additional inference calls."""
from pathlib import Path
import sys,json
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.linkage_restart_data import OUT,ROOT,read_compressed
from maze_evolution.linkage_restart_operator import dependencies,candidates,rows
from maze_evolution.linkage_restart_audit import independent_groups
from maze_evolution.exposure_genome import Individual
from maze_evolution.foundation_calibration import write_json
from maze_evolution.routing_transfer import lines

def main():
    p=read_compressed(OUT/'pools.json.gz')['carry/0'];w=read_compressed(ROOT/'results/compatibility_map/panel.json.gz');a=Individual.load(w['items']['d07']);b=Individual.load(w['items']['d12']);ids=p['gene_ids']
    opts=candidates(rows(a.genome.program),rows(b.genome.program),tuple(ids[a.identity]),tuple(ids[b.identity]));groups=dependencies(rows(a.genome.program));assert groups==independent_groups(rows(a.genome.program));target=next(g for g in groups if max(g)==222)
    packet=dict(post_hoc=True,candidate_calls=0,scope='Initial known historical d07/d12 structural diagnostic only; not an activation gate or functional intervention',group_for_store222=dict(members=list(target),size=len(target),span=max(target)-min(target)+1,contains207=207 in target),common_by_length=dict(Counter(y-x for x,y,u,v,n,ok in opts)),closed_by_length=dict(Counter(y-x for x,y,u,v,n,ok in opts if ok)),multi_by_length=dict(Counter(y-x for x,y,u,v,n,ok in opts if n>=2)),closed_multi_by_length=dict(Counter(y-x for x,y,u,v,n,ok in opts if ok and n>=2)))
    direct={};program=a.genome.genes
    for reg in (18,58):
        writers=[]
        for i in range(221,-1,-1):
            g=program[i]
            if g.op!=13 and g.dst==reg:
                writers.append(dict(index=i,row=g.row()))
                if g.gate==64:break
        direct[str(reg)]=dict(writers=writers,store_inclusive_span=223-min(v['index'] for v in writers))
    packet['immediate_possible_writers']=direct;write_json(OUT/'static_diagnostic.json',packet)
    by={};ancestry={}
    initial=read_compressed(OUT/'initial_states.json.gz')
    populations={key:{r['id']:(Individual.load(r),s['gene_ids'][r['id']]) for r in s['population']} for key,s in initial.items()}
    for e in lines(OUT/'reproduction.jsonl.gz'):
        population=populations[e['key']]
        for birth in e.get('births',[]):
            multi=birth['retained_donor_changes']>=2
            ancestry[birth['item']['id']]=multi or any(ancestry.get(parent,False) for parent in birth['parents'])
            x=birth['crossover'];m=birth['mating']
            if m is None:continue
            s=by.setdefault(e['key'],Counter());s['scheduled']+=1
            if x is None:s['no_homologous_variant']+=1;continue
            s['donor_found']+=1;s['zero_closed_at_length']+=x['linked']==0;s['common_segments_total']+=x['common'];s['closed_segments_total']+=x['linked']
            recipient,ri=population[birth['parents'][0]];donor,di=population[birth['proposed_donor']]
            pool=[v for v in candidates(rows(recipient.genome.program),rows(donor.genome.program),tuple(ri),tuple(di)) if v[1]-v[0]==x['length']]
            assert len(pool)==x['common'] and sum(v[5] for v in pool)==x['linked']
            common_multi=sum(v[4]>=2 for v in pool);closed_multi=sum(v[4]>=2 and v[5] for v in pool)
            s['common_multi_segments_total']+=common_multi;s['closed_multi_segments_total']+=closed_multi
            s['proposals_with_common_multi_option']+=common_multi>0;s['proposals_with_closed_multi_option']+=closed_multi>0
            if x['accepted']:
                s['accepted']+=1;s['multi_retained']+=multi;s['dependency_cut']+=not x['dependency_closed']
                s['multi_dependency_cut']+=multi and not x['dependency_closed']
                s['multi_erased_to_single_or_zero']+=x['changed_instructions']>=2 and not multi
        if not e.get('frozen'):
            populations[e['key']]={**{identity:population[identity] for identity in e['elite']},**{b['item']['id']:(Individual.load(b['item']),b['gene_ids']) for b in e['births']}}
            assert len(populations[e['key']])==96
    states=read_compressed(OUT/'next_states.json.gz')
    final={key:sum(ancestry.get(i['id'],False) for i in s['population']) for key,s in states.items()}
    costs={}
    for path in sorted((OUT/'train').glob('g*/responses.jsonl.gz')):
        for e in lines(path):
            c=costs.setdefault(e['key'],Counter());c['calls']+=len(e['rows']);c['seconds']+=e['seconds'];c['work']+=e['work']
    assert len({v['calls'] for v in costs.values()})==1
    write_json(OUT/'diagnostics.json',dict(post_hoc=True,candidate_calls=0,by_condition=by,training_costs=costs,final_members_with_X_multi_transfer_in_ancestry=final,
        limitations='Counters summarize recorded training reproduction; repeated parents/segments are correlated. Ancestry includes retained transfers in X only and does not demonstrate functional composition. Last newborn population remains unevaluated.'))
if __name__=='__main__':main()
