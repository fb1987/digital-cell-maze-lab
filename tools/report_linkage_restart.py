"""Saved activation and execution tables; no new candidate calls."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/linkage_restart'
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join('---' for _ in headers)+'|',*['| '+' | '.join(map(str,r))+' |' for r in rows]])
def main():
    a=json.loads((OUT/'analysis.json').read_text());ex=json.loads((OUT/'execution.json').read_text());audit=json.loads((OUT/'audit.json').read_text());profile=json.loads((ROOT/'results/linkage_restart_fixtures/profile.json').read_text());b=ex['budget']
    text='## Complete activation results\n\n'
    text+='Gate: at least 10% of all scheduled attempts retain two changed donor instructions after mutation, with such transfers in at least eight generations. Each origin needs at least two passing replicates for each of linked, unlinked and matched-sham crossover.\n\n'
    records=[]
    for origin in ('carry','fresh'):
        for arm in ('linked','unlinked','sham'):
            for rep in range(3):
                s=a['by_condition'][f'{origin}/{rep}/{arm}'];records.append([origin,arm,rep,s['scheduled'],s['donor_available'],s['accepted'],s['multi_before_mutation'],s['multi_retained'],f"{100*s['multi_fraction']:.2f}%",s['multi_generation_count'],s['passed']])
    text+=table(['Origin','Policy','Rep','Attempts','Donor available','Accepted','Multi before mutation','Multi retained','Retained / attempts','Active generations','Pass'],records)+'\n\n'
    text+='## Proposed and accepted segment lengths\n\n'
    records=[]
    for origin in ('carry','fresh'):
        for arm in ('linked','unlinked','sham'):
            for length in (2,4,8,16):
                totals={k:sum(a['lengths'].get(f'{origin}/{r}/{arm}',{}).get(k,{}).get(str(length),0) for r in range(3)) for k in ('proposed','accepted','multi_retained')}
                records.append([origin,arm,length,totals['proposed'],totals['accepted'],totals['multi_retained']])
    text+=table(['Origin','Policy','Length','Proposed with donor','Accepted','Multi retained'],records)+'\n\n'
    text+='Linked/sham length and feasibility matching is exact for the same parents and RNG snapshot. Evolving populations diverge, so these marginal distributions are not forced to match. The unlinked policy retains all common-pool segments. Genetic transfer counts do not demonstrate combined solving abilities.\n\n'
    text+='## Cost, reproducibility and scope\n\n'
    text+=f"The pilot completed **{ex['generations']} matched generations** of {ex['planned_generations']} planned, stopping with `{ex['stop']}`. Main inference: {b['calls']:,} calls, {b['seconds']:.2f}/{b['cap']:.2f} candidate seconds, {b['work']:,} charged work units. Total main wall: {ex['wall_seconds']:.2f}/720 seconds, including {ex['reproduction_seconds']:.2f}s in reproduction; peak RSS {ex['peak_rss_bytes']/2**20:.2f} MiB.\n\n"
    text+=f"Calibration separately: {profile['budget']['calls']:,} native calls, {profile['budget']['seconds']:.3f} candidate seconds and {profile['wall_seconds']:.2f}s wall. Its 2,160 discarded births were not seeded into search. Warmups are separately recorded. The restart held the original 32-generation target fixed; its timing-only projection was {profile['projections']['32']:.2f}s, below the 600s planning threshold and remaining candidate allowance. No fitness-based sizing or cap extension.\n\n"
    text+=f"Audit passes **{audit['logical_candidate_responses']:,} logical candidate responses**, checked against **{audit['exact_distinct_native_replays']:,} newly executed distinct genotype/case replays**; exact duplicates are reused only within each generation (and within calibration). Every logical candidate raster is independently graded: {audit['independently_graded_candidate_rasters']:,}. Baselines add {audit['baseline_replays']:,} exact replays and independent grades.\n\n"
    old_profile=json.loads((ROOT/'results/linkage_fixtures/profile.json').read_text())
    text+=f"Original invalid attempt separately: 297.71 candidate seconds and 512.71 wall seconds, plus {old_profile['budget']['calls']:,} calibration calls in {old_profile['budget']['seconds']:.3f} candidate seconds and {old_profile['wall_seconds']:.2f}s wall. Combined main candidate time is {297.712951528898+b['seconds']:.2f}/720 seconds; combined main wall {512.7068764159922+ex['wall_seconds']:.2f}s. Including both calibrations adds {old_profile['budget']['seconds']+profile['budget']['seconds']:.3f} candidate seconds. This extra wall cost is a disclosed software restart, not an extension based on scientific results. Audit replay costs are additional and reported below.\n\n"
    c=audit['counts'];text+=f"Full selection/RNG/population replay includes {c.get('random_births',0):,} random births, {c.get('mutations',0):,} concrete mutations, {c.get('independent_splices',0):,} independently reconstructed accepted splices and {c.get('independent_gene_maps',0):,} independently checked gene identity maps. Accepted dependency groups are independently scanned backwards. All {c['prior_hashes']:,} prior completion entries and {audit['source_hashes']} source/{audit['input_hashes']} input hashes verify. Audit wall {audit['wall_seconds']:.2f}s; peak RSS {audit['peak_rss_bytes']/2**20:.2f} MiB.\n\n"
    text+='Nineteen restart tests and19related tests pass (38), including the historical-namespace collision regression. This is not a fresh full-suite run. The restart protocol and all inputs were pushed before training generation. Its source and gate were not changed after registration. The original aedb017 attempt was invalidated by the disclosed identity bug and is preserved separately.\n\n'
    text+=f"Exclude **{ex['whole_layouts']:,} whole layouts through X-R1**, including every unqueried generated orientation and software fixture, using the sealed exclusion hash set. The data.exclusions() helper returns only 253,316 through the invalid original attempt. All populations, complete reproduction records, RNG checkpoints and final next populations are preserved; the last newborn population has not yet been evaluated.\n\n"
    text+='All outcomes concern a training activation pilot. There is no independent efficacy holdout, final champion selection, general-solver claim, multirange comparison or latency benchmark. Frozen founder controls were evaluated on the same batches; differing training tasks across generations prohibit interpreting raw score changes as generalization.\n'
    (OUT/'result_tables.md').write_text(text);print(text)
if __name__=='__main__':main()
