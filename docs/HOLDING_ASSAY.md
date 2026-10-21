# M5: conditional-state holding accessibility assay

Authorized October21,2026 after M4. This bounded new phase tests an architectural
accessibility hypothesis, not a continued M3/M4 search. Preserve all sealed prior
sources, inputs, histories and outputs. No cloud or external model services.

## Hypothesis and representation

M1 already expresses conditional state holding through SELECT and a reference to
its previous channel value. However, an unexecuted last scratch node contains
zero and the unconditional block writer copies that zero into persistent state.
M5 adds explicit, generic regulation at the output writer. Each of eight blocks
has a bounded condition register and a false-condition fallback: write zero or
hold that block's OLD persistent state. On a true condition it writes the normal
computed value. Conditions can refer to any initialized local input/flag/scratch
register, or ALWAYS64. No new spatial read, distance, parent-pointer, route
cleanup or solver-specific instruction is added. Updates remain synchronous.

M5 embeds an exact M1 body with all conditions ALWAYS64 and all hold bits zero.
This MUST reproduce every old mask, status, stopping step and work count. The
additional two eight-entry int32 arrays add64 reported bytes; no memory-equality
claim. All-false fallback bits are data, not executable generated code. M1 body
still has <=256 instructions including eight writer instructions, <=31nodes per
block, eight persistent channels, 256ticks and the same read/dispatch limits.
The condition check is part of the already charged output-writer instruction;
new branch overhead is included in actual candidate timing. No speed benchmark
or fair-latency advantage is claimed. Test old/new embedding at budget boundaries
and on excluded software cases, including real anchors and intact controls.

## Material and fixed pool

Use the exact M3 A0 retained-skill and A1 junction descendants studied in M4,
with their original root/parent references. These remain explicitly M3/M4-informed
random-origin lineages. No engineered solver is inserted into them. M5 is an
architecture-informed extension; it is not an unchanged-M1 evolutionary discovery.

For EACH of the two anchors, make1024 fixed paired proposals:512 direct writer
changes and512 one-generic-M1-mutation-then-writer changes, alternating by draw.
Choose the output block uniformly; choose a condition uniformly from all its
available input/flag/scratch registers plus ALWAYS64. Conditions that are always
true or behaviorally ineffective remain in the sample. Keep exact mutation events,
block/condition, genomes and RNG states. Produce TWO versions of each proposal:
false condition writes zero, or false condition holds old state. These share the
same body and gate, differing only in one fallback bit.

A third arm gets1024 standard M1 mutation proposals per anchor, with512 one- and
512 two-opportunity draws, embedded with neutral M5 writer metadata. Also draw
1024 independent generic random M1 bodies as a common resampling reference pool,
embedded neutrally. This random pool is shared across the two anchor comparisons,
not two independent random replicates. The standard mutation comparison changes
the proposal distribution as well as writer accessibility; ONLY the paired
hold/zero comparison isolates the fallback bit.

Unchanged anchors, exact roots/parents, legacy-M1 versions of both anchors and
four separate intact controls (flat, M1 modular, neutral M5, ALWAYS/hold M5) stay
outside candidate lineages. No offspring population, repeated selection,
inter-lineage mating, extra temporal trace or adaptive second screen.
Poolseed2026102109; developmentseed2026102110; finalseed2026102111.
Publish registration before generating scientific variants, and the concrete
complete pool before generating fresh development cases.

## Development and frozen nomination

Use unchanged M2 screen builder:392 inputs, same cases for every physical model.
Exclude ALL1,367,931 M4-and-earlier whole layouts. Each anchor/arm receives exactly
1024x392=401408 logical proposal queries; random pool receives the same allocation.
Exact physical genotype deduplication saves work, with every alias retained.
Report physical calls, neutral/duplicate proposals and work separately; equal
logical allocation is not equal elapsed CPU or independent offspring.

Nominate two aliases per anchor/arm, plus one aggregate random reference:

- Retained: choose among proposals retaining >=90% of the unchanged anchor's
  successful pairs, corridors and both-pose ordinary bases, with zero false
  no-path on reachable inputs. Empty reference sets are N/A. Include the unchanged
  anchor as a fallback candidate. If none are eligible (possible for A1), freeze
  the unchanged anchor and explicitly flag no eligible nominee.
- Exploratory: same candidates without the retention filter; this can select a
  specialist that loses old skills. It must still pass the full final gate to
  count as a successful acquisition.

Within either set rank lexicographically by: new upstream pairs beyond exact
anchor, new hard pairs, ordinary both-pose successes, total pairs, corridors,
negative false no-path, unchanged M1 family-normalized correctness/validity/
partial scores, then negative measured work. Break ties by exact identity string.
Upstream means non-fork prefix>=1, or any graph prefix>=2; hard means non-fork or
prefix>=2. Random reference uses the unchanged M1 aggregate rank and identity tie.
Freeze all13 nomination aliases, references, and each selected hold/zero item's
EXACT opposite-fallback twin. Publish choices before final case generation.

## Fresh final assessment and success criterion

After the development audit passes, generate the unchanged M3 confirmation panel
with a new seed, excluding all prior plus ALL development generated/rejected/
unqueried layouts.1680inputs/model,400paired opportunities,200corridors,256ordinary
reachable bases inbothposes,168disconnected. Score all fixed nominees, opposite
fallback twins, unchanged ancestors and separate controls on identical cases.
Do not reselect, add a second confirmation or inspect final cases before freezing.

Primary gate: a changed nominee has >=8 new UPSTREAM complete pairs beyond its
own unchanged anchor across >=2 independent template contexts, retains >=90% of
that anchor's successful paired/corridor/ordinary-base sets, and has ZERO false
reachable no-path. The gate is identical across arms. Report new/lost successes,
empty denominators, domains and route lengths. A positive secondary specialist
that fails retention is not a primary success. If a hold nominee passes, compare
its exact zero twin before attributing the result to holding. If both pass, do
not claim holding was necessary. These are bounded same-grammar, correlated-pose
results, not arbitrary topology generalization or a replicated long-run policy
advantage. No longer run or recombination follows automatically.

## Bounds and reproducibility

Main scientific screen+final together: <=4M physical calls,3x10^12 charged work,
900wallseconds combined, ten local workers,8GiB sampled process-tree RSS,
6GiB phase storage INCLUDING backups,16GiB free disk floor. Running reservations
charge worst-case work, completed receipts charge actual work. Stop and preserve
on any failure/guard; no automatic restart, budget reset or source repair.
Development and final each use a separate durable SQLite FULL/WAL journal under
a writer lock, preserving all task receipts and inputs. Final allowance subtracts
actual development usage/time, so bounds are cumulative. Audits are additional,
<=1800seconds per audit under the same storage/memory safeguards.

Preflight uses only already excluded M2/M3 software cases, random stand-ins and
unchanged controls/anchor embedding. Its calls and timing are separate from
science. Exercise pool/RNG and nomination reproducibility before registration.
No performance-based anchor or protocol refinement on new scientific cases.

Every output is independently graded. Development audit regenerates all draws,
concrete mutations, writer choices, RNG, corpus, task allocations and nominations;
regrades all responses, fully replays unchanged anchors/legacy/control models,
and replays a fixed1/32 SHA256(model,case) sample otherwise. Final audit regenerates
corpus/tasks, regrades and natively replays ALL physical outputs and recomputes
canonical summaries. Both check legacy/embedded equality and intact controls.
The native replay shares production code; it is not a second independent VM.

Preserve hashes, logs, both journals and safe SQLite backups if guards permit;
export cumulative whole-layout exclusions including rejected draws and unqueried
poses. Seal report/compact evidence and push. Never overwrite an old seal or a
failed audit record. No general-solver, speed, sexual-transfer or unrestricted
random-origin discovery claim follows merely from adding a generic primitive.
