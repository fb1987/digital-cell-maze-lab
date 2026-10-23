"""Postprocessing only: saved source, lineage allocation and final responses."""
import json,sys
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.repair_evolution_m32 import *

def main():
    check();assert not (OUT/'saved_diagnostics.json').exists()
    for name in ('source','search','final'):assert json.loads((OUT/(name+'_audit.json')).read_text())['status']=='PASS'
    s=readz(OUT/'sources.json.gz');data,rows,_,_,_=load_finite('source');caps=caps_rows(rows,data)
    source_details={}
    for identity in s['entries']:
        c=caps[identity];pairs,success=controlled(c,data)
        other=[i for i in s['historical_references'] if i!=identity]
        union=set().union(*(caps[i]['success'] for i in other))
        by_length=Counter(len(data['metadata'][cid]['path'])-1 for cid in success)
        source_details[identity]=dict(metrics=c['summary'],controlled_complete_pairs=pairs,controlled_correct_individuals=len(success),controlled_correct_by_edges=dict(by_length),individuals_beyond_other_fixed_references=sorted(c['success']-union),correct_no_path=len(c['correct_no_path']),false_no_path=len(c['false']),status_counts=dict(Counter(r['status'] for r in rows[identity])))
    j=readonly('search');registry=collect_registry(j,s);allocation={};first_survived=set();first_trained=set()
    for n,blob,decision in j.db.execute('select n,input,decision from stages where complete=1 order by n'):
        d=unpacked(blob)
        if d['kind']!='train':continue
        g=d['generation']
        for dec in unpacked(decision):
            a=allocation.setdefault(dec['name'],dict(births=Counter(),operators=Counter(),writer=Counter(),entry_births=Counter(),changed=0,noops=0,niche_profiles=[],mutants=0,immigrants=0))
            a['niche_profiles'].append(dec['distinct_niche_profiles'])
            for identity in dec['survivors']:
                if identity in registry and registry[identity]['item']['birth']==g and g>0:first_survived.add(identity)
            for b in dec['births']:
                item=b['item'];e=b['event'];a['births'][b['parent_policy']]+=1;a['entry_births'][item['entry']]+=1
                if e is None:a['immigrants']+=1
                else:
                    a['mutants']+=1;a['operators'][e['kind']]+=1;a['writer'][str(e['block'])]+=1
                    changed=e['before']!=e['after'];a['changed']+=changed;a['noops']+=not changed
        # Query coverage includes fixed references; count actual birth identities
        # when first trained, separately from assessment-only last-generation births.
        for _,spec,_ in j.tasks(n):
            for e in spec:
                for identity in e['aliases']:
                    if identity in registry and registry[identity]['item']['birth']==g and g>0:first_trained.add(identity)
    final_states=j.state();chain=j.verify_chain();j.close()
    for st in final_states:
        a=allocation[st['name']];live=st['population'];by_entry=defaultdict(Counter)
        for i in live:
            by_entry[i['entry']]['live']+=1;by_entry[i['entry']]['positive_M32_changed_depth']+=i['changed_depth']>0
        births=[v['item'] for v in registry.values() if v['item']['id'].startswith('m32/'+st['name']+'/g')]
        a.update(final_live_by_entry={k:dict(v) for k,v in by_entry.items()},maximum_final_depth=max(i['depth'] for i in live),maximum_final_changed_depth=max(i['changed_depth'] for i in live),
            final_unique_genotypes=len({hashed(packed(i['model'])) for i in live}),first_trained_births=sum(i['id'] in first_trained for i in births),first_train_survived=sum(i['id'] in first_survived for i in births),
            final_live_mutant_identities=sum(i['depth']>0 for i in live),final_rare_lineage=[dict(id=i['id'],depth=i['depth'],changed_depth=i['changed_depth']) for i in live if i['entry']==RARE])
        for k in ('births','operators','writer','entry_births'):a[k]=dict(a[k])
    d,rr,_,_,_=load_finite('final');choices=readz(OUT/'choices.json.gz');cc=caps_rows(rr,d);portfolio=set().union(*(cc[i]['success'] for i in s['historical_references']));profiles={}
    # The frozen fresh builder retains rejected/unqueried proposals in metadata.
    # Correct interpretation denominators/strata use queries.all. Endpoint sets
    # already intersect only actually graded successes; verify invariance below.
    queried_meta={cid:d['metadata'][cid] for cid in d['queries']['all']}
    all_ordinary={m['base']:m for m in d['metadata'].values() if m['family'] in ('ordinary_perfect','ordinary_random')}
    queried_ordinary={m['base']:m for m in queried_meta.values() if m['family'] in ('ordinary_perfect','ordinary_random')}
    corrected_strata={};portfolio_cap={k:set().union(*(cc[i][k] for i in s['historical_references'])) for k in (*FIELDS,'success','false')}
    for identity,cap in cc.items():
        bins=defaultdict(lambda:dict(bases=0,complete=0))
        for base,meta in queried_ordinary.items():
            edges=len(meta['path'])-1;key=f'{meta["family"]}/{meta.get("size")}/'+('0-7' if edges<8 else '8-15' if edges<16 else '16plus')
            bins[key]['bases']+=1;bins[key]['complete']+=base in cap['ordinary_bases']
        corrected_strata[identity]=dict(bins)
    for i in s['historical_references']:profiles.setdefault(hashed(packed([(r['status'],r['mask']) for r in rr[i]])),[]).append(i)
    final_details=[]
    for c in choices['choices']:
        i=c['item']['id'];parent=c['item']['parent'];cap=cc[i];new=sorted(cap['success']-portfolio);examples=[]
        for cid in new[:12]:
            meta=d['metadata'][cid];base=meta.get('base');partners=[x for x,m in d['metadata'].items() if base is not None and m.get('base')==base and x!=cid]
            examples.append(dict(case=cid,family=meta['family'],edges=len(meta['path'])-1,partners=[dict(case=x,status=next(r['status'] for r in rr[i] if r['case']==x),optimal=next(r['optimal'] for r in rr[i] if r['case']==x)) for x in partners]))
        final_details.append(dict(population=c['population'],role=c['role'],id=i,entry=c['item']['entry'],parent=parent,phase_depth=c['item']['depth'],phase_changed_depth=c['item']['changed_depth'],
            known_profile_matches=profiles.get(hashed(packed([(r['status'],r['mask']) for r in rr[i]])),[]),new_individual_inputs=len(new),new_individual_examples=examples,
            actual_parent_individual_gains=len(cap['success']-cc[parent]['success']) if parent else None,actual_parent_individual_losses=len(cc[parent]['success']-cap['success']) if parent else None,
            entry_individual_gains=len(cap['success']-cc[c['item']['entry']]['success']),entry_individual_losses=len(cc[c['item']['entry']]['success']-cap['success']),correct_no_path=len(cap['correct_no_path']),false_no_path=len(cap['false'])))
        comparators=list(dict.fromkeys(s['strict_roots'].get(c['item']['entry'],[c['item']['entry']])+[x for x in (c['item']['entry'],parent) if x]))
        filtered=endpoint(cap,[cc[p] for p in comparators],portfolio_cap,cc[A0],queried_meta,c['item']['changed_depth']>0)
        unfiltered=endpoint(cap,[cc[p] for p in comparators],portfolio_cap,cc[A0],d['metadata'],c['item']['changed_depth']>0)
        assert filtered==unfiltered,'Query filtering must not alter any registered endpoint or gate'
    writej(OUT/'saved_diagnostics.json',canonical(dict(status='PASS',no_new_inference=True,source_measurement=source_details,allocation=allocation,final_details=final_details,search_chain=chain,total_M32_registry_records=len(registry),all_original_sources_unchanged=prior_check(),
        queried_ordinary_bases=len(queried_ordinary),queried_ordinary8_bases=sum(len(m['path'])-1>=8 for m in queried_ordinary.values()),queried_ordinary16_bases=sum(len(m['path'])-1>=16 for m in queried_ordinary.values()),queried_ordinary_length_strata=corrected_strata,
        query_filter_note=dict(raw_summary_ordinary_denominator_includes_unqueried_generated_proposals=len(all_ordinary)!=len(queried_ordinary),raw_generated_ordinary_bases=len(all_ordinary),actually_queried_ordinary_bases=len(queried_ordinary),all_primary_endpoints_and_gates_exactly_invariant=True,correction='Use this queried-only interpretation for ordinary denominators and length strata. Original sealed raw summary unchanged; no inference, source, selection or nomination repair.'),
        limitations='Same-case source/descendant comparisons required. Source sizes differ from final; raw totals are not acquisition. No source-driven reselection. Phase-only depths exclude inherited M31 and earlier mutations.')))
if __name__=='__main__':main()
