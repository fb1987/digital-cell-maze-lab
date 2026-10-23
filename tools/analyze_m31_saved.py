"""M31 descriptive saved-record supplement; no inference, new cases or selection."""
import json,sys
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.output_access_m31 import ROOT,OUT,RUN,check,readz,writej,load,sha,hashed,packed,panel_stream,entries
from maze_evolution.output_access_genome_m31 import ARMS,Genome
from maze_evolution.connected_evolution_genome import graph
from maze_evolution.breeding_allocation_metrics import capabilities_plus
from maze_evolution.transfer_retention_metrics import gate

def main():
    check();assert not (OUT/'saved_diagnostics.json').exists();assert json.loads((OUT/'final_audit.json').read_text())['status']=='PASS'
    pool=readz(OUT/'pool.json.gz');choices=readz(OUT/'choices.json.gz');dev=readz(OUT/'development_summary.json.gz');models={i['id']:i['model'] for i in pool['items']}
    operators={};groups={}
    for source in pool['parents']:
        for arm in ARMS:
            cc=[c for c in pool['conditions'] if c['source']==source and c['arm']==arm];stats=Counter();genotypes=set()
            for c in cc:
                e=c['event'];g=Genome.from_dict(models[c['id']]['genome']);parent=Genome.from_dict(models[c['parent']]['genome']);genotypes.add(g.digest)
                stats['opportunities']+=1;stats['genotype_changed']+=not e['genotype_noop'];stats['genotype_noop']+=e['genotype_noop'];stats['kind/'+e['kind']]+=1;stats['mode/'+str(e['mode'])]+=1
                stats['writer/'+str(e['block'])]+=1
                if e['mode'] in (1,3) and e['kind']=='operand' and (len(parent.body.blocks[e['block']])>=31 or parent.instructions>=256):stats['capacity_operand_fallback']+=1
                stats['C2_static_direct_self_dependency']+=2 in graph(g)[2]
            operators[source+'/'+arm]=dict(counts=dict(stats),distinct_genotypes=len(genotypes))
    data,rows,_,usage,chain=load('final');meta={c:data['metadata'][c] for c in data['queries']['all']};refs=pool['historical_references']
    caps={i:capabilities_plus(rs,meta) for i,rs in rows.items()};portfolio_inputs=set().union(*(caps[i]['success'] for i in refs));portfolio_bases=set().union(*(caps[i]['ordinary_bases'] for i in refs))
    fingerprints={i:hashed(packed([(r['case'],r['status'],r['mask']) for r in rs])) for i,rs in rows.items()}
    selected=[];nominated={c['id'] for c in choices['choices']}
    for identity in sorted(nominated):
        condition=next(c for c in pool['conditions'] if c['id']==identity);correct={r['case'] for r in rows[identity] if r['optimal']}
        new=correct-portfolio_inputs;ordinary=[cid for cid in new if meta[cid]['family'] in ('ordinary_perfect','ordinary_random')]
        newlong=[cid for cid in ordinary if len(meta[cid]['path'])-1>=8]
        g=Genome.from_dict(models[identity]['genome']);parent=condition['parent'];cp=caps[parent];c=caps[identity]
        selected.append(dict(id=identity,source=condition['source'],arm=condition['arm'],event=condition['event'],
            M31_genotype_changes=int(not condition['event']['genotype_noop']),M31_opportunities=1,parent=parent,comparators=condition['comparators'],
            new_individual_reachable_inputs=len(new),new_individual_ordinary8=len(newlong),new_individual_ordinary_cases=newlong,
            new_individual_lengths=dict(Counter(len(meta[cid]['path'])-1 for cid in ordinary)),
            exact_historical_genotype_matches=[i for i in refs if models[i]==models[identity]],
            exact_control_genotype_matches=[i for i in pool['control_ids'] if models[i]==models[identity]],
            final_terminal_mask_status_profile_matches=[i for i in refs if fingerprints[i]==fingerprints[identity]],
            max_correct_ordinary_edges=max((len(meta[cid]['path'])-1 for cid in correct if meta[cid]['family'] in ('ordinary_perfect','ordinary_random')),default=None),
            correct_ordinary16_bases=sum(len(next(m for m in meta.values() if m.get('base')==b)['path'])-1>=16 for b in c['ordinary_bases']),
            parent_input_gains=sorted(c['success']-cp['success']),parent_input_losses=sorted(cp['success']-c['success']),
            correct_no_path=len(c['correct_no_path']),no_path_gains=sorted(c['correct_no_path']-cp['correct_no_path']),no_path_losses=sorted(cp['correct_no_path']-c['correct_no_path']),
            false_no_path=sorted(c['false']),instructions=g.instructions,C2_direct_static_dependencies=sorted(graph(g)[2]),
            actual_parent_only_gate=gate(c,[cp],caps['m14/reference/anchor/0'],not condition['event']['genotype_noop']),
            final_status_counts=dict(Counter(r['status'] for r in rows[identity]))))
    byarm={a:dict(opportunities=sum(c['arm']==a for c in pool['conditions']),
        distinct_child_genotypes=len({hashed(packed(models[c['id']])) for c in pool['conditions'] if c['arm']==a}),
        physical_native_query_equivalent=sum(c['arm']==a for c in pool['conditions'])*811) for a in ARMS}
    con,development,_,_=panel_stream('development');dm={c:development['metadata'][c] for c in development['queries']['all']}
    controlled={c for c,m in dm.items() if m['family'].startswith('controlled_')};old_controlled=set();all_pool_stats={a:Counter() for a in ARMS};rare=[]
    for e,r in entries(con):
        if set(e['aliases'])&set(refs):old_controlled.update(x['case'] for x in r['rows'] if x['optimal'] and x['case'] in controlled)
    conditions={c['id']:c for c in pool['conditions']};ordinary={m['base']:m for m in dm.values() if m['family'] in ('ordinary_perfect','ordinary_random')}
    for e,r in entries(con):
        aliases=set(e['aliases'])&set(conditions)
        if not aliases:continue
        cap=capabilities_plus(r['rows'],dm);single={x['case'] for x in r['rows'] if x['optimal'] and x['case'] in controlled};complete8={b for b in cap['ordinary_bases'] if b in ordinary and len(ordinary[b]['path'])-1>=8}
        maximum=max((len(ordinary[b]['path'])-1 for b in complete8),default=0)
        for identity in sorted(aliases):
            cc=conditions[identity];stats=all_pool_stats[cc['arm']];stats['proposals']+=1;stats['any_controlled_individual_success']+=bool(single);stats['controlled_individual_success_presentations']+=len(single)
            stats['any_controlled_individual_beyond_portfolio']+=bool(single-old_controlled);stats['any_complete_ordinary8_including_known']+=bool(complete8)
            stats['complete_ordinary8_base_presentations_including_known']+=len(complete8);stats['max_complete_ordinary_edges']=max(stats['max_complete_ordinary_edges'],maximum)
            if single or maximum>=16:rare.append(dict(id=identity,source=cc['source'],arm=cc['arm'],nominated=identity in nominated,
                controlled_individual_cases=sorted(single),controlled_individual_beyond_portfolio=sorted(single-old_controlled),known_or_novel_complete_ordinary8_bases=sorted(complete8),max_complete_ordinary_edges=maximum))
    con.close();baseline={}
    for source,p in pool['parents'].items():
        noop=next(c for c in dev['conditions'] if c['source']==source and c['event']['genotype_noop']);assert models[noop['id']]==models[p['id']]
        baseline[source]=dict(parent=p['id'],development_noop_witness=noop['id'],development_gate_ignoring_attribution={k:v for k,v in noop['endpoint']['gate'].items() if k not in ('passes','positive_mutation_ancestry')},
            development_comparisons=noop['comparisons'],final_ancestral_gate_ignoring_attribution={k:v for k,v in gate(caps[p['id']],[caps[i] for i in p['comparators']],caps['m14/reference/anchor/0'],True).items() if k not in ('passes','positive_mutation_ancestry')})
    writej(OUT/'saved_diagnostics.json',dict(saved_only=True,no_new_inference=True,no_reselection=True,operators=operators,by_arm=byarm,
        parent_baseline_eligibility=baseline,development_gate_flag_counts={k:sum(c['endpoint']['gate'][k] for c in dev['conditions']) for k in dev['conditions'][0]['endpoint']['gate']},
        all_proposal_saved_development_stats={a:dict(v) for a,v in all_pool_stats.items()},all_controlled_or_sixteen_edge_hits=rare,
        controlled_inputs_covered_by_declared_portfolio=sorted(old_controlled),
        declared_historical_aliases=len(refs),nomination_roles=len(choices['choices']),distinct_nomination_identities=len(nominated),
        distinct_nominated_genotypes=len({hashed(packed(models[i])) for i in nominated}),nominees=selected,
        final_portfolio_correct_inputs=len(portfolio_inputs),final_portfolio_complete_bases=len(portfolio_bases),
        development_by_arm=dev['by_arm'],final_usage=usage,final_chain=chain,
        source_ancestry=readz(OUT/'sources.json.gz')['parents'],
        limitation='Static dependency is conservative, not a test of erasure or useful feedback. Terminal-profile identity ignores work/steps/other states. New individual poses are distinct from complete two-pose bases. All roles frozen before fresh data.'))

if __name__=='__main__':main()
