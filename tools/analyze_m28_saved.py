"""Read-only posthoc interpretation of M28 saved records; zero new inference."""
import json,platform,subprocess,sys,time,traceback
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.integration_accessibility import ROOT,OUT,RUN,check,readz,writej,load,ARMS,Genome,capabilities


def main():
    check();assert not (OUT/'saved_diagnostics.json').exists();pool=readz(OUT/'pool.json.gz');dev=readz(OUT/'development_summary.json.gz')
    summary=json.loads((OUT/'summary.json').read_text());conditions={c['id']:c for c in pool['conditions']};items={x['id']:x for x in pool['items']}
    arms={}
    for arm in ARMS:
        cc=[c for c in dev['conditions'] if c['arm']==arm]
        fields=('positive_mutation_ancestry','domain_retention90','a0_disconnection90','zero_false_no_path','passes')
        arms[arm]=dict(proposals=len(cc),changed=sum(c['positive_variation'] for c in cc),
            kinds=dict(Counter(c['event']['kind'] for c in cc)),rejection_reasons=dict(Counter(c['event'].get('reason','') for c in cc if c['event']['kind']=='bounded_noop')),
            distinct_genotypes=len({Genome.from_dict(items[c['id']]['model']['genome']).digest for c in cc}),
            complete_complementary_distribution=dict(Counter(c['known_complementary_complete'] for c in cc)),
            gated_known_positive=sum(c['known_complementary_complete']>0 and c['endpoint']['gate']['passes'] for c in cc),
            max_complementary=max(c['known_complementary_complete'] for c in cc),
            gates={k:sum(c['endpoint']['gate'][k] for c in cc) for k in fields},
            raw_development_complete8_positive=sum(c['endpoint']['raw_novel_complete8']>0 for c in cc),
            integrated_known_identities=[c['id'] for c in cc if c['known_complementary_complete'] and c['endpoint']['gate']['passes']],
            max_instructions=max(Genome.from_dict(items[c['id']]['model']['genome']).instructions for c in cc),
            no_evolution_or_survival=True)
    costs={};novel_inputs={};old_aliases=pool['historical_references'];profiles={};source_matches=0
    for name in ('development','final'):
        data,rows,models,usage,chain=load(name);meta,caps=capabilities(data,rows);buckets=defaultdict(lambda:dict(physical_models=0,calls=0,work=0,candidate_seconds=0.))
        for e,r in models:
            aa=sorted({conditions[i]['arm'] for i in e['aliases'] if i in conditions});reference=any(i not in conditions for i in e['aliases'])
            key='+'.join(aa+(['reference'] if reference else []));b=buckets[key];b['physical_models']+=1
            for k in ('calls','work','candidate_seconds'):b[k]+=r[k]
        costs[name]=dict(physical_buckets=dict(buckets),total=usage,nominal_by_arm={a:dict(aliases=sum(i in rows and c['arm']==a for i,c in conditions.items()),
            calls=sum(len(rows[i]) for i,c in conditions.items() if i in rows and c['arm']==a),
            work_including_duplicate_aliases=sum(sum(r['reads']+r['dispatches']+r['exposure_checks'] for r in rows[i]) for i,c in conditions.items() if i in rows and c['arm']==a)) for a in ARMS})
        old=set().union(*(caps[i]['success'] for i in old_aliases));novel_inputs[name]={}
        if name=='development':
            from maze_evolution.transfer_retention import load as oldload
            _,oldrows,_,_,_=oldload()
            for i in pool['historical_references']+pool['control_ids']:
                expected={r['case']:r for phase in ('replay','fresh') for r in oldrows[phase][i]}
                for r in rows[i]:assert expected[r['case']]==r;source_matches+=1
        for i,c in conditions.items():
            if i not in rows:continue
            new=caps[i]['success']-old
            if new:novel_inputs[name][i]=[dict(case=cid,family=meta[cid]['family'],edges=len(meta[cid]['path'])-1,base=meta[cid]['base'],pose=meta[cid]['pose']) for cid in sorted(new)]
        if name=='final':
            from maze_evolution.deep_campaign_store import hashed,packed
            # Terminal signature deliberately excludes cost; work is separately reported.
            keys=('case','mask','status','steps')
            signatures={i:hashed(packed([{k:r[k] for k in keys} for r in rs])) for i,rs in rows.items()}
            for i in sorted(set(x['id'] for x in summary['choices'])):
                g=Genome.from_dict(items[i]['model']['genome'])
                matches=[j for j in old_aliases if items[j]['model']['representation']=='connected' and Genome.from_dict(items[j]['model']['genome']).digest==g.digest]
                ordinary={m['base']:m for m in meta.values() if m['family'] in ('ordinary_perfect','ordinary_random')}
                lengths=[len(ordinary[b]['path'])-1 for b in caps[i]['ordinary_bases']]
                profiles[i]=dict(genotype_matches=matches,terminal_mask_status_steps_matches=[j for j in old_aliases if signatures[i]==signatures[j]],instructions=g.instructions,
                    ordinary_complete8=sum(n>=8 for n in lengths),ordinary_complete16=sum(n>=16 for n in lengths),max_correct_ordinary_edges=max(lengths,default=None))
    writej(OUT/'saved_diagnostics.json',dict(status='PASS',scope='Posthoc saved-response interpretation, zero new inference/cases.',arms=arms,costs=costs,
        novel_single_inputs=novel_inputs,final_profiles=profiles,old_saved_source_row_matches=source_matches,
        primary=summary['primary'],all_source_ancestry_retained_in=pool['source_ancestry_sha256'],
        limitation='Different grammar edit sizes; fixed neighborhoods, no breeding/survival or sustained generations. Development gains may overfit reused cases. Deduplication prevents attributing shared physical CPU uniquely to an arm.'))
    writej(OUT/'environment.json',dict(platform=platform.platform(),python=platform.python_version(),machine=platform.machine(),
        cpu=subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),cores=subprocess.check_output(['sysctl','-n','hw.ncpu'],text=True).strip(),
        ram_bytes=int(subprocess.check_output(['sysctl','-n','hw.memsize'],text=True).strip()),workers=10))
    print(json.dumps(arms,indent=2),flush=True)


if __name__=='__main__':
    try:main()
    except BaseException:
        with (OUT/f'saved_diagnostics_failure_{time.time_ns()}.json').open('x') as f:json.dump(dict(traceback=traceback.format_exc()),f,indent=2)
        raise
