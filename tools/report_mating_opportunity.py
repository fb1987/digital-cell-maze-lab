"""Render audited V12Y tables and a static research figure; no candidate calls."""
from pathlib import Path
import json
from collections import defaultdict
import gzip
import statistics

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/mating_opportunity'


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join('---' for _ in headers)+'|',
                      *['| '+' | '.join(map(str,row))+' |' for row in rows]])


def main():
    analysis=json.loads((OUT/'analysis.json').read_text())
    run=json.loads((OUT/'execution.json').read_text())
    audit=json.loads((OUT/'audit.json').read_text())
    assert audit['passed'] and run['candidate_calls']==audit['candidate_calls']==0
    rows=analysis['by_condition']
    pooled={}
    for origin in ('carry','fresh'):
        for view in ('actual','shortlist','other8','union'):
            for cap in (16,32):
                for rule in ('transitive','gate','sham_transitive','sham_gate','unlinked'):
                    ss=[rows[f'historical/{origin}/{rep}/{arm}/{view}/{cap}/{rule}']
                        for rep in range(3) for arm in ('linked','unlinked','sham')]
                    pooled[f'{origin}/{view}/{cap}/{rule}']=dict(
                        attempts=sum(s['attempts'] for s in ss),
                        expected_percent=100*sum(s['expected_multi'] for s in ss)/sum(s['attempts'] for s in ss),
                        realized=sum(s['multi'] for s in ss),
                        any_available=sum(s['any_multi_donor_segment'] for s in ss),
                        eligible_donor=sum(s['eligible_donor'] for s in ss))
    with gzip.open(OUT/'families.jsonl.gz','rt') as f:
        families=[json.loads(line) for line in f]
    metrics={}
    for origin in ('carry','fresh'):
        for generation in (0,32):
            fs=[s for s in families if s['generation']==generation and s['key'].startswith(origin+'/')
                and s['key'].split('/')[-1] in ('linked','unlinked','sham')]
            metrics[f'{origin}/{generation}']=dict(effective_mutable_roots=statistics.mean(s['effective_mutable_roots'] for s in fs),
                unique_genotypes=statistics.mean(s['unique_genotypes'] for s in fs))
    (OUT/'report_data.json').write_text(json.dumps(dict(pooled=pooled,family_means=metrics),indent=2)+'\n')
    text='## Complete donor-view comparison\n\n'
    text+='Expected percentage of PRE-MUTATION multi-change exchanges, pooled over nine saved arm/replicate histories per origin (9,216 attempts per cell). This is a design assay, not an evolved activation result. Historical arms are correlated descendants of shared initial pools.\n\n'
    records=[]
    for origin in ('carry','fresh'):
        for view in ('actual','shortlist','other8','union'):
            for cap in (16,32):
                records.append([origin,view,cap,*[f"{pooled[f'{origin}/{view}/{cap}/{rule}']['expected_percent']:.3f}%" for rule in ('transitive','gate','sham_transitive','sham_gate','unlinked')]])
    text+=table(['Origin','Donor view','Max length','Full closure','Gate linkage','Full sham','Gate sham','Unlinked'],records)+'\n\n'
    text+='## Frozen design-screen decisions\n\n'
    text+='Each rate averages the three prior sexual-arm populations within that original replicate. All three listed rates must reach12% in2/3replicates of BOTHorigins. Neither cap qualifies. This does not replace the future actual post-mutation10% activation gate.\n\n'
    text+=table(['Origin/rep/cap','Gate','Gate sham','Unlinked','Pass'],[
        [key,*[f"{100*values[k]:.3f}%" for k in ('gate','sham_gate','unlinked')],min(values.values())>=.12]
        for key,values in analysis['decision']['expected_fraction_by_origin_rep_cap'].items()])+'\n\n'
    text+='## Family and genotype diversity\n\n'
    text+='Effective family count is inverse concentration of fractional ancestry-root membership among nonprotected members. It is not a functional diversity score. All final snapshots include the last unevaluated newborn generation.\n\n'
    records=[]
    for origin in ('carry','fresh'):
        for arm in ('linked','unlinked','sham','mutation','resample','frozen'):
            for g in (0,32):
                fs=[s for s in families if s['key'].startswith(origin+'/') and s['key'].endswith('/'+arm) and s['generation']==g]
                records.append([origin,arm,g,f"{statistics.mean(s['mutable_roots'] for s in fs):.2f}",
                    f"{statistics.mean(s['effective_mutable_roots'] for s in fs):.2f}",
                    f"{statistics.mean(s['unique_genotypes'] for s in fs):.2f}"])
    text+=table(['Origin','Prior arm','Generation','Mutable roots','Effective mutable roots','Unique genotypes /96'],records)+'\n\n'
    text+='## Verification and cost\n\n'
    text+=f"Main assay: {run['opportunities']:,} probes, {run['pair_occurrences']:,} directed pair occurrences, {run['unique_homology_aware_pairs']:,} unique genotype-plus-homology pairs, {run['family_snapshots']} family snapshots; {run['wall_seconds']:.2f}s wall, {run['peak_rss_bytes']/2**20:.2f}MiB peak RSS. **Zero candidate inference calls and zero new mazes.** The layout exclusion count remains255,356.\n\n"
    text+=f"Independent audit passes on its first attempt in {audit['wall_seconds']:.2f}s, {audit['peak_rss_bytes']/2**20:.2f}MiB peak RSS. It reconstructs every segment pool using independent backward scans and set tests, then exactly replays virtual choices, raw records, aggregate decisions, family snapshots and final populations/gene maps. All {audit['prior_hash_entries']:,} prior entries, {audit['source_hashes']} source hashes and {audit['input_hashes']} inputs verify. Random selection and aggregation use replay of common functions, not a second independent implementation.\n\n"
    text+='Twelve new opportunity tests plus19related tests pass(31). Six separate tests cover the prepared family-reserve prototype; that prototype was not used in the Y assay and has not yet undergone end-to-end evolution preflight. No fresh full-suite claim. Protocol/source/input registrationf7b1244 was pushed before the assay. No frozen-source repair or post-registration rule change.\n'
    (OUT/'result_tables.md').write_text(text)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    rules=('transitive','gate','sham_gate','unlinked')
    labels=('Full closure','Immediate gate','Matched gate sham','Unlinked')
    colors=('#85939f','#228f80','#c49a5a','#567ab3')
    fig,axes=plt.subplots(1,2,figsize=(11,4.8),sharey=True)
    for ax,origin in zip(axes,('carry','fresh')):
        for j,(rule,label,color) in enumerate(zip(rules,labels,colors)):
            ys=[pooled[f'{origin}/union/{cap}/{rule}']['expected_percent'] for cap in (16,32)]
            x=np.arange(2)+(j-1.5)*.18
            ax.bar(x,ys,.17,label=label,color=color)
            for xx,y in zip(x,ys):ax.text(xx,y+.15,f'{y:.2f}',ha='center',fontsize=8)
        ax.axhline(12,color='#a44343',ls='--',lw=1)
        ax.set_xticks([0,1],['Up to 16 instructions','Up to 32 instructions'])
        ax.set_title('Carried random-origin histories' if origin=='carry' else 'Fresh random-origin histories')
        ax.set_ylim(0,13);ax.grid(axis='y',alpha=.15)
    axes[0].set_ylabel('Expected multi-change exchanges (% of attempts)')
    axes[1].legend(fontsize=8,loc='upper left')
    fig.suptitle('V12Y: lighter linkage helps, but transfer opportunities remain sparse')
    fig.text(.5,.02,'Recorded shortlist + 8 uniform other donors; matched parents and segment pools. Dashed line: 12% design screen.\nExact pre-mutation probabilities on saved histories; no new evolution or maze-solving evidence.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.12,1,.95))
    fig.savefig(OUT/'opportunities.png',dpi=180);fig.savefig(OUT/'opportunities.pdf');plt.close(fig)
    (OUT/'plot_manifest.json').write_text(json.dumps(dict(matplotlib=matplotlib.__version__,candidate_calls=0),indent=2)+'\n')


if __name__=='__main__':
    main()
