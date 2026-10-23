"""Create the M30 report once from audited evidence; no inference or reselection."""
import json,sys,zlib
from pathlib import Path
from collections import Counter
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.information_flow_m30 import ROOT,OUT,RUN,readz,read_records,writej,check

def main():
    check();assert not (OUT/'report.md').exists();assert not (OUT/'termination_note.json').exists()
    summary=json.loads((OUT/'summary.json').read_text());interp=json.loads((OUT/'interpretation.json').read_text());wave=json.loads((OUT/'wave_arrival_note.json').read_text())
    session=json.loads((OUT/'session.json').read_text());audit=json.loads((OUT/'audit.json').read_text());pres=json.loads((OUT/'preservation.json').read_text());status=json.loads((RUN/'workflow_status.json').read_text())
    assert audit['status']==wave['status']=='PASS';data=readz(OUT/'cases.json.gz');sources=readz(OUT/'sources.json.gz');models={x['case_id']:x for x in data['mazes']}
    counts=Counter();steps=Counter()
    for spec,r,blob in read_records():
        if spec['phase']!='native' or r['role']=='control' or r['case'] not in data['queries']['new']:continue
        if not r['row']['reachable']:continue
        h=np.frombuffer(zlib.decompress(blob),dtype='<u2').reshape(r['history_shape']);m=models[r['case']]
        explicit=bool(h[-1,7,m['start']]>0 and h[-1,2,m['start']]>0 and h[-1,2,m['goal']]>0)
        quiet4=len(h)>=5 and all(np.array_equal(h[-1],h[-k]) for k in range(2,6))
        counts['reachable_focal_presentations']+=1;counts['final_explicit_endpoint_halt_condition']+=explicit;counts['four_quiet_ticks_at_end']+=quiet4
        steps[r['row']['steps']]+=1
    assert counts['reachable_focal_presentations']==720 and counts['final_explicit_endpoint_halt_condition']==720 and counts['four_quiet_ticks_at_end']==0
    writej(OUT/'termination_note.json',dict(saved_only=True,new_inference=0,counts=dict(counts),terminal_steps=dict(steps),
        interpretation='All reachable focal runs emitted via the native endpoint/C7 halt condition, with no four-tick quiet ending. That condition certifies neither raster connectivity nor shortestness; independent grades remain failures. No forced continuation or new stopping policy was tested.'))
    unique_stimuli=len({models[c]['sha256'] for c in data['queries']['new']})
    unique_swaps=len({tuple(sorted((models[c['a']]['sha256'],models[c['b']]['sha256']))) for c in data['contrasts'] if c['kind']=='route_swap'})
    lines=[]
    for role,label in (('recipient','Recipient'),('donor','Donor'),('regulated','Regulated'),('control','Intact control')):
        r=summary['by_role'][role];i=interp['by_role'][role]
        lines.append(f"| {label} | {r['contrasts']['route_swap']['C2_observer_signal']}/48 | {r['contrasts']['route_swap']['complete_both']}/48 | {sum(x['optimal'] for x in r['new_by_variant'].values())}/240 | {r['new_by_variant']['neither']['correct_no_path']}/48 | {i['cases_ever_off_any_shortest_path']}/240 |")
    report=f'''# M30: signals arrive; complete route selection still fails

The three fixed random-origin genomes contain functioning source and goal
reachability waves. Changing distant gates changes their branch-point signals.
They still fail every reachable controlled maze in this study. The failure is
therefore more specific than an inability to receive remote maze information:
the current readout lights incomplete/branching rasters, locks in wrong pixels
after the goal signal arrives, and stops when its endpoints are lit.

This is a mechanism result on USED development diagnostics, **not an evolved
improvement or independent confirmation**. All genomes and earlier histories
are unchanged. The user authorized M29's proposed information-flow audit.
Registration **fae1fed**, all 391 source/material hashes and exact job list were
pushed before any scientific execution. Both the run and ALL-job audit passed
on their first scientific attempt. No further phase has been launched.

## Fixed material and fair contrasts

Use the exact M29 recipient `{sources['focal']['recipient']}`, donor
`{sources['focal']['donor']}`, and regulated child
`{sources['focal']['regulated']}`. An intact M18 local solver is an external
positive control; it contributes no genetic material, selection or output switch.
These are related random-origin descendants, not independent random origins.

All 69 M29 inputs were rerun on the three focal genomes; **207/207 saved rows
reproduced**. The new corpus contains 288 presentations from six fixed geometries
and all eight symmetries, with paths of 18, 26 or 34 edges. There are
**{unique_stimuli} distinct full stimuli and 138 whole-layout hashes**; duplicate
presentations were actually executed and charged. The 48 route-swap contrasts
contain {unique_swaps} distinct unordered stimulus pairs. They are not 48 independent
random trials, and no significance test is claimed.

Two distant gate pixels determine whether the left or right arm reaches the
same goal. Their swap preserves open count, path length and every observer's
radius-one input patch. Separate both-open/neither-open contrasts test a cycle
versus disconnection; those counts differ by two open cells and stopping differs.
Irrelevant isolated-pixel swaps preserve counts and the reachable maze component.
All changes are at least three Manhattan steps from the observed branch sites.
There was no maze search, favorable filtering or result-based model selection.

## The executed mechanism

Independent vector equations matched **24,738,750 completed-tick open-site channel
values**, plus every patched writer result. Arbitrary zero, saturated and random
state tests checked the algebra against all ten original writers. These equations
describe values, not native execution cost: unused SSA instructions still run
and consume reads/dispatches.

The source-seeded loop is `C0 ← sat(C0 + max(0,C5−source))`, with
`C5 ← min-positive(neighbor C0)`. The goal-seeded loop is
`C7 ← sat(C7+C1)`, with `C1 ← min-positive(neighbor C7)`.
On these exact genomes, first positivity propagates at **two ticks per graph
edge**, in either loop. Saved-state verification checked 73,563 observed arrivals
exactly, 10,551 unreachable site-histories never activating, and 12,384 site-histories
censored before their expected arrival. No later state was inferred or executed.
This is topology-respecting communication, not a purely fixed geometric pattern.
Positive numeric values subsequently accumulate; they are not canonical BFS
distance labels or a stored predecessor map. The mechanism is inherited; this
audit does not date when it originally evolved.

The six propagation channels C0/C1/C3/C4/C5/C7 match across all three focal models
in every one of the 357 common native windows. C2/C6 have no functional return
edge into this core. Different scratch instructions and unused ports still cost
work, but they do not create different effective propagation cores here.

At a non-source open site, the path channel obeys:

```
if C1 == 0: C2_next = 0
else:       C2_next = sat(C2 + (bool(C0) XOR bool(C6) if C4 else 0))
```

At the source, positive C1 replaces C2. C4 is `bool(C3 or goal)`.
The recipient C6 copies C3 from the east when C0 is positive and a neighboring
C1 is positive; otherwise it copies from the north. The donor copies C3 from the
west. The regulated child chooses between these two inherited directional reads
using C5, the western C7 value and the goal flag. These are absolute grid
directions, not a comparison of all possible exits by distance to the goal.
The full ten-channel equations and gates are frozen in `equations.json`.

## What the remote changes actually do

| Fixed model | C2 signal changes at branch | Solves both gate alternatives | Correct reachable outputs | Correct disconnection | Ever lights off-shortest pixels |
|---|---:|---:|---:|---:|---:|
{chr(10).join(lines)}

All three focal C2 signals change in all 48 swaps. C1 first distinguishes them
at ticks **30/46/62**, and C2 at **33/49/65**, with the corresponding size groups.
The source/goal transport mechanism therefore reaches the decision area before
normal emission. C6 differs in 24/48 swaps for each focal model. Neither the
recipient nor donor chooses the correct exclusive arm in both alternatives in
any swap; the regulated child lights **both arm entrances in all 240 reachable
presentations**. Every model leaves the irrelevant-control observer histories
and final rasters unchanged in all 48 comparisons.

There are 352 first-difference intervention events, with 3,872 full-grid writer
calls. Each single channel is borrowed in turn, then the full common open state.
Full-state restoration reproduces the counterpart's observer output in every
event. For example, replacing C3 alone reproduces all 48 donor C6 contrasts;
first C2 differences sometimes require C1 or C4 rather than C6 alone. Some events
have no single-channel exact restoration. This supports local causal input
effects, not a claim that C6 alone mediates every routing failure, or that any
full trajectory/path has been rescued. All raw events remain available.

The both-open/neither-open common windows show some absent signals, especially
on larger fixtures. Their different stop times censor observation. Do not turn
those absences into proof that the genomes cannot sense disconnection.

## Why a wave still fails to become a path

The saved-only secondary analysis used the **union of all shortest paths**,
so it does not penalize an alternative equally short route chosen by the VM.
Recipient and donor each light wrong pixels in 144/240 reachable presentations;
the regulated model does so in 192/240. Across the three, **480/720 presentations
contain 912 distinct wrong pixel presentations, with zero erasures**. A separate
scalar recount confirms those numbers. All 720 focal reachable outputs fail:
recipient/donor each have 192 disconnected rasters and 48 branch/cycle rasters;
regulated has 132 disconnected and 108 branch/cycle rasters.

After C1 has become persistently positive at an ordinary site, this C2 recurrence
can add a pixel or retain it, but cannot remove it. It can reset before a stable
goal signal; the claim is not that the VM lacks subtraction or negative feedback.
Those primitives already exist. Nor must every general solver erase pixels:
one can delay commitment until it has enough information. What the observed
readout cannot do is repair the premature wrong commitments documented here.

All 720 focal reachable runs terminate with the explicit C7-at-source plus both
C2 endpoints condition true, and none has four quiet ticks at its end. That native
condition does not establish that the raster between the endpoints is connected.
All new reachable runs are `emitted`, not budget-exhausted. Simply allowing more
native execution was not tested and would not, by itself, add an erasure term
to this established recurrence. The control correctly returns all 240 reachable
paths and all 48 disconnections under the same existing M18 limits. Expressing a
solver on this domain fits the current VM; evolutionary accessibility remains open.

## Validation, resources and preservation

Science ran 1,359 native calls plus 1,359 passive traces and 3,872 writer calls:
**6,590 mixed units**, **1,064,163,764 reads+dispatches**. Native+passive accounts for
1,060,011,692 work; state interventions add 4,152,072. Formula arithmetic and
saved-history processing have CPU cost but are not invented VM work units.
Science wall was {session['wall_seconds']:.3f}s; summed job wall {session['totals']['seconds']:.3f}s,
summed job CPU {session['totals']['cpu_seconds']:.3f}s, sampled tree RSS
{session['rss_peak_bytes']/2**30:.3f} GiB. Full workflow wall was
{status['ended_epoch']-status['started_epoch']:.3f}s. These are short diagnostic costs,
not a speed comparison; job CPU excludes worker initialization, scheduling and
parent process storage/analysis costs. Tests' VM work was not instrumented.

The first ALL-job audit replayed **all 1,935 jobs**, every history byte, native
field, work count, grade, equation check, intervention, source/corpus/job definition
and summary. It passed in {audit['wall_seconds']:.3f}s, with
{audit['totals']['cpu_seconds']:.3f}s summed job CPU and
{audit['rss_peak_bytes']/2**30:.3f} GiB sampled RSS. Native/passive share the M18 VM;
vector algebra and raster grading are independent checks, not a second complete
interpreter proof. Seven focused tests pass, not the full repository suite.
One pre-registration contrast indexing failure is preserved with source/test
copies; the corrected seven-test run passes. A separate three-job durable
preflight used only old inputs. Zero scientific failures, uncertain attempts,
guard bypasses, repairs or failed-workflow resumes occurred.

Both science/audit stayed within the separate 1,200s/100K-unit/1e12-work limits,
10 workers, 8 GiB RSS, 2 GiB total storage and 16 GiB free-disk floor.
All **431 prior completion hashes and 18 local records** verify unchanged.
The original journal and SQLite-API backup are {pres['journal']['source']['bytes']:,} bytes
each; integrity and ALL 1,935 job rows plus settings match under writer locks.
Whole-layout exclusion now contains **{pres['whole_layouts']:,} hashes**: 3,998,785
inherited plus 138 generated layouts and one conservative algebra fixture.
All source/goal poses, aliases and initial/rejected records remain preserved;
the corpus had no rejection search. Reference manifests require their immutable
bases. Raw SQLite remains local and outside Git.

## Recommended next step — not launched

Keep the random-origin lineages and their propagation machinery. Defer memory
expansion, another blind C6/recombination campaign and another long unchanged run.
The evidence now points to **how local evidence controls output commitment and
stopping**, rather than an absence of communication or a demonstrated need for
twice the state. M29's wrong-context C6 hypothesis remains unsupported.

A useful next phase would be a separately registered, finite **output-interface
accessibility assay**: generic existing-grammar edits of C2's write/gate/feedback
and matched ordinary/C6 controls, fixed parent pool and equal opportunities,
with complete paths, wrong-pixel retention, no-path and old-skill losses all
reported. Test whether a small heritable edit can defer/reverse incorrect output
while retaining the inherited waves; do not insert a hand-written solver or
reward an empty raster as progress. Freeze any candidates before separate fresh
confirmation, and consider sustained evolution only after that accessibility
question has a promising answer. This recommendation is a hypothesis, not proof
that an output edit will suffice; C3/C6 spatial computation may also need to change.
No next experiment or evolution is authorized or running from this report.
'''
    (OUT/'report.md').write_text(report)

if __name__=='__main__':main()
