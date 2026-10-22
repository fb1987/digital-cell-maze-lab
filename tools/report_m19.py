"""Draft actual M19 report once; requires human-readable agent review before seal."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.connected_evolution import OUT,check


def main():
    check();assert not (OUT/'report.md').exists()
    def read(n):return json.loads((OUT/n).read_text())
    s=read('summary.json');d=read('saved_diagnostics.json');a=read('allocation_persistence.json');p=read('preservation.json')
    sessions={k:read(n) for k,n in [('search','session.json'),('final','final_session.json')]};audits={k:read(k+'_audit.json') for k in sessions}
    assert all(x['status']=='PASS' for x in audits.values());policy=s['policy_comparison'];validation=read('software_validation.json')
    primary=[c for c in s['conditions'] if c['rank']==0]
    lines=['# M19: sustained connected-duplication evolution','',
        f"Search completed {sessions['search']['new_rounds']} matched rounds across nine populations for `{sessions['search']['stop']['reason']}`. Descriptive support for both registered contrasts: **{policy['descriptive_support_both']}**. Integrated-role deeper/long acquisition passes: {sum(c['upstream_acquisition'] for c in primary)}/{len(primary)} and {sum(c['long_ordinary_acquisition'] for c in primary)}/{len(primary)}. These are the fixed primary roles; secondary outcomes are shown separately.",'',
        f"Registration `{read('launch.json')['registration_commit']}` was pushed before scientific generation; exact choices `{read('choices_freeze.json')['commit']}` were pushed before the fresh1,680-input confirmation. Both audits passed. No final-data reselection.",'',
        '## Fixed primary comparison','',policy['primary']+'.',
        'Retention requires positive M19 mutation count, zero false reachable no-path,90% of every nonempty exact-root AND phase-entry skill set, and90% of a NONEMPTY A0 correct-disconnection set. Novelty excludes root, phase-entry and ALL13 protected references. Each descriptive contrast needs positive differences in2/3trios and a positive sum; both must pass for combined support. This is not statistical significance.','',
        '| Trio | Generic | Disconnected | Connected | Connected − generic | Connected − disconnected |',
        '|---|---:|---:|---:|---:|---:|']
    for q in policy['pairs']:lines.append(f"| {q['replicate']} | {q['generic']} | {q['disconnected']} | {q['connected']} | {q['connected_minus_generic']} | {q['connected_minus_disconnected']} |")
    lines+=['',f"Connected versus generic: `{json.dumps(policy['connected_vs_generic'])}`. Attachment versus disconnected: `{json.dumps(policy['attachment_vs_disconnected'])}`.",'',
        '| Fixed primary | M19 / inherited study mutations | Pairs /400 | Corridors /200 | Ordinary both poses /256 | Correct no-path /168 | False no-path | New upstream | Gate |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for c in primary:
        m=c['metrics'];lines.append(f"| {c['condition']} | {c['mutations']} / {c['inherited_mutations']} | {m['paired']} | {m['by_domain']['corridor']['optimal']} | {m['ordinary_bases_both_poses']} | {m['correct_no_path']} | {m['false_no_path']} | {c['beyond_root_and_protected_union']['new_upstream_pairs']} | {c['retention_and_disconnection_gate']} |")
    lines+=['','## Material, variation and limits','',
        'Three matched trios share the exact ordered initial genomes and RNG per trio: ordinary generic mutation, initialized disconnected duplication and initialized connected duplication. Nine96-slot populations have13protected sources: the twelve previous random-origin references plus exactM15g320/b48. The other83slots alternate clones of that specialist and its actual parent. These are new matched forks for a changed variation operator; whole old populations are not continued or erased. Original M15 edit/root/parent records remain. Source-study inherited depth is not an all-time count from the first random genome.','',
        'All arms use the SAME unchanged M18 inference runtime, hard limits and common generic grammar including spare last-node deletion/seed reset. Copy arms use25% prospective eligible initialized-copy opportunities, with common-mutation fallback when no edge is eligible. Eligible edges are current structural reads, not M18-final winners. Both copy arms copy/rebind the writer and inherit initialization; only connected redirects the reader. Original stimulus conventions remain fixed. Genomes have ten state channels,256instructions/ticks,31nodes/block,4096reads/site and32768dispatches/site. Added work and premature budget stops are charged. No known solver, oracle, arbitrary code or sexual recombination enters candidate inference.','',
        'Selection is common:13protected+8merit+up to12quality-profile explorers, then coverage/finite-panel neutral/lexicase within44survivors;7random M1-body immigrants neutrally embedded and45one-opportunity mutants each round. The first12mutants cycle available explorers. Banks and selector are common, so this experiment does not isolate or establish their benefits.','',
        'All arms see48common fresh rotating+48fixed ordinary bank inputs. Assessment every16rounds plus initial/final uses115×392nominal queries including nonselectable A0padding. Frozen M11 bank panels are explicitly reused development data, conditioned on an old parent; they are not independent confirmation. New layouts, including rejected/unqueried draws, are excluded. Equal nominal evaluations are not equal CPU. Familiar grammar poses and related origins limit generalization claims.','',
        '## All frozen nominee roles and attribution','',
        '| Condition/role | Identity | M19 births | Phase-entry retained | New upstream | Deeper / long / combined | Strict integration |',
        '|---|---|---:|---|---:|---|---|']
    for c in s['conditions']:lines.append(f"| {c['condition']}/{c['role']} | {c['child']} | {c['mutations']} | {json.dumps(c['phase_entry_retention'])} | {c['beyond_root_and_protected_union']['new_upstream_pairs']} | {c['upstream_acquisition']} / {c['long_ordinary_acquisition']} / {c['combined_transfer']} | {c['integration']['integration_pass']} |")
    lines+=['',f"{d['nominee_aliases']} nominee roles represent {d['nominee_identities']} identities and {d['nominee_genotypes']} genotypes. Aliases are not independent discoveries. Exact root, immediate parent, phase entry, initial frozen and all protected references receive the SAME final inputs. summary.json retains every comparison, disconnection loss/gain and length stratum.",'',
        '| Nominee | Phase edit kinds | Spare channels in static output/halt cone | Correct16+ / available | New ordinary beyond union+entry (family,size,edges) | New individual inputs beyond union |',
        '|---|---|---|---:|---|---:|']
    for identity,x in d['nominees'].items():
        md=d['model_details'][identity]
        lines.append(f"| {identity} | {json.dumps(x['phase_edit_kinds'])} | {x['spares_in_conservative_output_halt_cone']} | {md['length16plus_successes']} / {md['length16plus_bases']} | {[(z['family'],z['size'],z['edges']) for z in x['new_ordinary_details']]} | {len(x['new_individual_inputs_beyond_protected'])} |")
    lines+=['','Deeper acquisition needs8new nonforkprefix2+pairs in2contexts. Long acquisition needs4new8+edge ordinary bases in both poses, including16+and both perfect/random families. Both need the retention/disconnection/phase gates. Strict integration separately requires all quota-parent skills and specialist-only pairs, with an entry not already integrated. Useful specialists and their losses are reported even if gates fail. Static cones are only potential dependencies; no new causal trace or inference was added for reporting.','',
        '## Actual variation, survival and persistence','',
        '| Population | Initialized connected copies | Initialized disconnected copies | Deactivations | Generic fallback | Copy kinds next-train survival | Max M19 depth | Copy descendants remaining live/archive |',
        '|---|---:|---:|---:|---:|---|---:|---:|']
    for name,v in sorted(a['variation_counts'].items()):
        f=a['final_persistence'][name];survival=a['immediate_birth_survival'].get(name,{})
        subset={k:n for k,n in survival.items() if k.startswith('initialized_')}
        lines.append(f"| {name} | {v.get('kind/initialized_connected_copy',0)} | {v.get('kind/initialized_disconnected_copy',0)} | {v.get('kind/deactivate_spare',0)} | {v.get('ordinary_fallback',0)} | {json.dumps(subset)} | {f['max_M19_mutation_depth']} | {f['live_and_archive_copy_descendants']} |")
    lines+=['',f"Total births: {d['birth_counts']['mutation']:,} mutants and {d['birth_counts']['immigrant']:,} immigrants. Copy opportunity counts, eligibility, capacity/no-op/fallback counts, newborn spare occupancy and final lineage persistence are retained in allocation_persistence.json and the search audit. Immediate survival counts exclude last-round children without a next training exposure. Survival or copy ancestry is not proof of acquired algorithmic capability.",'',
        '## Compute, controls and preservation','',
        'Registered search target70min/hard90min,1024rounds/120Mcalls/1e15work; ten workers,8GiBRSS,12GiBtotal phase including backups,16GiBfree. Separate final900s/1Mcalls/1e14work; each audit3600s. Any resource stop takes precedence over the scientific target.','',
        '| Phase | Calls | Candidate seconds | Worker CPU seconds | Wall seconds | Work | Sampled RSS GiB |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for k,x in sessions.items():
        u=x['usage'];lines.append(f"| {k} | {u['calls']:,} | {u['candidate_seconds']:.2f} | {u['cpu_seconds']:.2f} | {x['wall_seconds']:.2f} | {u['work']:,} | {x['rss_peak_bytes']/2**30:.3f} |")
    lines+=['',f"Nominal per-population allocations: `{json.dumps(next(iter(audits['search']['logical_query_counts'].values())))}`. All nine match. Actual physical search cost is partitioned by all sharing arm labels in allocation_persistence.json, avoiding double-counting deduplicated references. Timing is accounting including cold compilation when incurred, not a repeated warm speed benchmark. Uncertain attempts: {sessions['search']['usage']['uncertain_attempts']} search / {sessions['final']['usage']['uncertain_attempts']} final.",'',
        f"Search audit PASS: ALL{audits['search']['independent_grades']:,} independent grades,{audits['search']['native_replays']:,} fixed native replays,{audits['search']['births_replayed']:,} births and {audits['search']['stages']} complete corpus/task/selection/mutation/RNG/freeze stages;{audits['search']['wall_seconds']:.2f}s. Final audit PASS: ALL{audits['final']['native_replays']:,} native outputs/grades/summary plus{audits['final']['conventional_calls']:,} conventional controls;{audits['final']['wall_seconds']:.2f}s. Intact flat/M1/M18 and BFS/A*/bitwave controls solve all1680inputs. Shared production VM/reproduction, independent raster grader; not an independent second VM.",'',
        f"Preparation:8focused tests passed in65.20s, not the full historical suite;328832discarded rehearsal calls/140.36candidate seconds/1404births replayed, plus5040intact control calls. The complete artificial pipeline reuses search receipts and adds{validation['discarded_pipeline']['final_session']['usage']['calls']:,} final evaluations,{validation['discarded_pipeline']['search_audit']['native_replays']:,} search native samples and{validation['discarded_pipeline']['final_audit']['native_replays']:,} final native replays, plus5040conventional controls. Other unit native costs were not separately instrumented. Initial test-assumption and setup-helper failures are preserved; no scientific source repair followed registration.",'',
        f"All {len(read('registration.json')['files'])} registration hashes and390M18completion hashes/14local records verified. Preserved storage before report/seal:{p['storage_bytes']/2**30:.3f}GiB;free{p['disk_free_bytes']/2**30:.2f}GiB. SQLite-API backups under locks: "+', '.join(k+'='+v['backup']['status'] for k,v in p['stages'].items())+'. Originals remain intact.',
        f"Whole-layout exclusions:{p['whole_layouts']:,} (initial{p['initial_layouts']:,}+search{p['search_new_layouts']:,}+final{p['final_new_layouts']:,}). Use verified recursive referenced_campaign_store.load_layouts; raw layouts tables are deltas. Restores depend on immutable base manifests and parts. Raw journals remain outside Git; compact evidence and copied logs are preserved. Earlier S3 migration authorization is separate; no old history was removed or rerun by M19.",'',
        'No general-solver, speed, significance or independent-origin claim follows from this bounded study. A negative result does not close random-origin discovery. Add reviewed interpretation and a recommendation based on actual outcomes before completion sealing.','']
    (OUT/'report.md').write_text('\n'.join(lines));print('M19 actual report drafted; review and add interpretation before seal.')

if __name__=='__main__':main()
