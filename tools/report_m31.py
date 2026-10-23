"""One-shot M31 report draft from closed audited records, then human-style review."""
import json,sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.output_access_m31 import ROOT,OUT,RUN,readz,writej,check

def main():
    check();assert not (OUT/'report.md').exists();summary=json.loads((OUT/'summary.json').read_text());diagnostic=json.loads((OUT/'saved_diagnostics.json').read_text())
    dev=readz(OUT/'development_summary.json.gz');trace=json.loads((OUT/'trace_summary.json').read_text());pres=json.loads((OUT/'preservation.json').read_text())
    sessions={k:json.loads((OUT/(k+'_session.json')).read_text()) for k in ('development','trace','final')};audits={k:json.loads((OUT/(k+'_audit.json')).read_text()) for k in sessions}
    assert all(a['status']=='PASS' for a in audits.values());status=json.loads((RUN/'workflow_status.json').read_text());freeze=json.loads((OUT/'choice_freeze.json').read_text())
    launch=json.loads((OUT/'launch.json').read_text());prep=json.loads((OUT/'preparation.json').read_text());sources=readz(OUT/'sources.json.gz')
    primary=[c for c in summary['choices'] if c['role']=='INTEGRATED'];nominations=readz(OUT/'choices.json.gz')['choices'];devlookup={c['id']:c for c in dev['conditions']}
    rows=[]
    for c in primary:
        d=devlookup[c['id']];f=c['final'];e=f['endpoint']
        rows.append(f'| {c["source"]} | {c["arm"]} | {c["id"].split("/")[-1]} | {d["controlled_route_pairs"]}/48 | {e["raw_novel_complete8"]} | {e["primary_score"]} | {e["gate"]["passes"]} | {f["correct_no_path"]} | {f["false_no_path"]} |')
    devrows=[]
    for arm,d in dev['by_arm'].items():devrows.append(f'| {arm} | {d["opportunities"]} | {d["changed"]} | {d["controlled_pair_positive"]} | {d["raw_ordinary8_positive"]} | {d["gate_passes"]} |')
    costs=[]
    for name,s in sessions.items():
        a=audits[name];u=s['usage'];costs.append(f'| {name} | {u["calls"]:,} | {u["work"]:,} | {u["candidate_seconds"]:.2f} | {u["cpu_seconds"]:.2f} | {s["wall_seconds"]:.2f} | {s["rss_peak_bytes"]/2**30:.3f} | {a["wall_seconds"]:.2f} |')
    support=summary['combined_descriptive_support'];score={c['source']+'/'+c['arm']:c['final']['endpoint']['primary_score'] for c in primary}
    nominee_ids={c['id'] for c in nominations};traced_nominees={i:d for i,d in trace['details'].items() if i in nominee_ids}
    changed={i:d for i,d in traced_nominees.items() if next(c for c in nominations if c['id']==i)['development']['positive_M31_genotype_change']}
    erased={i:d for i,d in changed.items() if d['counts'].get('erases_wrong_pixel',0)>0};complete={i:d for i,d in changed.items() if d['counts'].get('correct_reachable',0)>0}
    novel={c['id'] for c in summary['choices'] if c['final']['endpoint']['raw_novel_complete8']>0};gated={c['id'] for c in primary if c['final']['endpoint']['primary_score']>0}
    report=f'''# M31: output-interface accessibility

The finite assay is complete and all three audits PASS. Fixed INTEGRATED-role
scores are **{score}**. Combined descriptive support for targeting C2 is
**{support}**. There are {len(novel)} distinct frozen nominee identities with raw new
complete ordinary8+ bases and {len(gated)} fixed PRIMARY identities with positive
gated scores. Raw capability, retention and final confirmation are reported
separately below. These finite related neighborhoods do not establish a general
solver, a speed advantage or a significant policy effect.

The user authorized M30's proposed finite assay. Source, exact pool, used panel,
selection rules and protocol were published at **{launch['registration_commit'][:7]}**
before scientific execution. Exact27 role choices and development evidence were
committed/pushed at **{freeze['commit'][:7]}** before fresh generation. No final
re-selection or additional evolution was run. All older histories remain intact.

## What changed and what was controlled

The parents are the exact M30 recipient, donor and regulated random-origin
genomes. They share inherited propagation dynamics; these are related forks,
not three fresh origins. Each has512 matched seeded opportunities per arm.
Ordinary uses the unmodified M19 grammar; output and C6 consume its initial
writer draw then constrain that writer to C2 or C6. The seven old mutation modes,
bounded fallbacks, existing ten-channel M18 VM, caps and stopping rules remain.
No BFS, oracle or hand-written solver enters variation/inference. Writer copies
can change multiple nodes; one opportunity is not one scalar edit. No M31 mating,
larger state space or sustained generation sequence was introduced.

There are4,608 proposals plus211 reference aliases,2959 physical development
models after genotype/query deduplication. ALL208 noncontrol historical aliases
are the declared portfolio; three intact controls are external checks only.
The offspring have one M31 variation opportunity, separated from all inherited
M25/M28 ancestry. Exact ancestry identifiers/hashes and roots/entries are retained.

Each arm receives **1,536 opportunities ×811 cases =1,245,696 nominal queries**.
Physical inference is deduplicated, including across arms and references.
Different scopes/lengths change random consumption, kinds, dead-code exposure
and cost. Equal opportunities/nominal cases do not imply equal CPU or isolated
causality of a particular primitive. All capacity fallbacks/no-ops are counted.

Development reuses ALL454 M28 development inputs and ALL357 M30 inputs, namespaced
by panel, with no new development mazes. This includes all288 controlled poses
and69 older mechanism cases. The controlled48 swaps contain repeated symmetries;
they are not48 independent random maze samples. Retention compares same-case
parent/root/entry complete paired tasks, corridors, ordinary bases and no-path.
Gate-pass also requires changed genotype, nonempty A0-disconnection90% and zero
false reachable no-path. No reward for making a reachable raster empty.

## Every proposal in development

| Scope arm | Opportunities | Changed genotypes | Any complete controlled swap | Any raw novel ordinary8+ | Gate passes |
|---|---:|---:|---:|---:|---:|
{chr(10).join(devrows)}

These are proposal identities, including repeated genotypes and related parents.
Novelty is against the208 declared reference aliases on the SAME cases, before
retention gates. Development totals cannot be subtracted from fresh totals to
infer acquisition. Full event/kind/writer/allocation distributions are retained
in `saved_diagnostics.json`; the complete pool and RNG hashes reconstruct exactly.

## Independent confirmation of the fixed primary choices

Fresh confirmation contains2128 queried inputs:1680 standard plus448 externally
stratified ordinary inputs, perfect/tree and cyclic random, with whole-layout
exclusion of all prior and generated/rejected/unqueried inputs. It has
{summary['ordinary_bases']} ordinary bases, {summary['ordinary8_bases']} eight-plus
and {summary['ordinary16_bases']} sixteen-plus bases. Ordinary capability requires
both fixed poses of a base. All27 frozen roles and211 reference aliases receive
the same cases; actual distinct model/query counts are disclosed below.

PRIMARY is the fixed INTEGRATED role in each source/arm. Its score is new complete
ordinary8+ bases beyond the declared historical portfolio and genetic parent/
root/entry, zero if any gate fails. The exploratory/retention roles cannot replace
it. New individual poses and recombined known portfolio skills are separate.

| Source | Scope | Frozen draw | Dev complete swaps | Fresh raw novel8+ | Gated PRIMARY | Gate | Correct no-path | False no-path |
|---|---|---|---:|---:|---:|---|---:|---:|
{chr(10).join(rows)}

The prespecified descriptive comparisons are:

```json
{json.dumps(summary['policy_comparison'],indent=2)}
```

Each comparison requires positive differences in2/3 source backgrounds AND a
positive sum; both comparisons are required for combined support. This is a
descriptive pilot rule, not a significance test. Raw novel bases, collective
single-input novelty, losses, exact parent/root/entry comparisons, every secondary
role, ordinary family/length strata and no-path outcomes remain in `summary.json`
and `saved_diagnostics.json`. Historical genotype and final mask/status profile
matches are explicit; a different genotype with the same output profile is not
automatically a new solving mechanism. Profile equality does not imply equal work.

## Does output reversibility actually appear?

All distinct frozen nominees plus exact three parents and intact connected
control were traced on all288 controlled development presentations AFTER choice
freeze. {trace['physical_models']} physical models/{trace['aliases']} identities,
{sessions['trace']['usage']['calls']:,} passive calls. Every native response/work
field matches the corresponding development call; all stored history bytes replay.
There was no trace-based re-selection or forced continuation.

Of {len(changed)} changed nominee identities, **{len(erased)} erase at least one wrong
pixel**, while **{len(complete)} produce any correct controlled reachable output**.
These counts alone cannot demonstrate acquisition or robust retention. The full
trace summary distinguishes wrong-pixel removal, silence, actual correctness and
common-window preservation of the inherited propagation core. Wrong pixels mean
outside the UNION of all shortest paths, so an equally short alternative is not
penalized. Common windows end at the earlier normal stop. Absence later is censored.
The trace panel is USED development, not independent evidence of generalization.

## Verification, costs and preservation

| Stage | Actual calls | Reads+dispatches | Candidate seconds | Worker CPU seconds | Stage wall seconds | Peak sampled GiB RSS | ALL-replay audit wall seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(costs)}

All-native development and final audits replay every call/grade/work count,
pool/operator/RNG and task; development also replays exact nomination and old
source rows. The trace audit replays ALL histories and matches every passive row
to development native fields. Fresh generation reproduces exactly, including
all rejected/unqueried observed layouts. Conventional BFS/A*/bitwave control
checks total {sum(a['conventional_calls'] for a in audits.values()):,}; all intact
and conventional controls are correct. Shared production VM/passive tracing plus
independent raster grading is not a second independent full VM proof.

Native timing includes decoding, updates and final raster emission, excluding
construction/grading/serialization. Trace timings also pay for history storage.
Worker CPU excludes some parent scheduling/storage work and is not complete
end-to-end host CPU. These are measured research costs, not warmed repeated
latency benchmarks. Incorrect outputs earn no speed comparison. Workflow calendar
wall was {status['ended_epoch']-status['started_epoch']:.2f}s, with phase logs retained.

Seven focused tests PASS on their first run (and final repeat), not a full-suite
claim. Durable discarded-case preflight ran840 native calls plus16 traces on four
already excluded inputs, matching native/passive rows and replaying nomination.
Every scientific stage has zero uncertain attempts. All three audit packets PASS.
Registered local limits are10 workers,1800s development/900s final/1200s trace,
2400s per audit,5M calls/1e14 work per stage,8GiB sampled RSS,6GiB TOTAL storage
including preparation/logs/backups,16GiB free disk. No bound was extended.

All428 M30 completion hashes and18 local records verify unchanged. Original
development, trace and final journals remain local. SQLite-API backups under
writer locks have status **{pres['status']}**, with integrity and ALL-table checks
including settings, tasks, stages, states and the single-column layout table.
The ledger contains {pres['whole_layouts']:,} hashes: {pres['initial_layouts']:,}
inherited plus {pres['new_layouts']:,} new generated/rejected/unqueried hashes.
Reference manifests still require immutable bases. Raw SQLite is never in Git.
At preservation: {pres['storage_bytes']/2**30:.3f} GiB phase storage and
{pres['disk_free_bytes']/2**30:.2f} GiB disk free. Report review and completion seal
are written once, with compact evidence/copied logs published and mutable AGENTS
handoff updated. No later phase is running.

## Interpretation and next recommendation

Review the observed mechanism, raw gains and retention losses together. The
registered endpoint cannot be replaced by a promising secondary nominee or lower
wrong-pixel count. A finite negative neighborhood does not close random-origin
discovery or establish a hard capacity limit. Any next intervention must be
separately registered, preserve these random-origin sources and freeze choices
before additional fresh confirmation. No M32 or sustained run is authorized here.
'''
    (OUT/'report.md').write_text(report)

if __name__=='__main__':main()
