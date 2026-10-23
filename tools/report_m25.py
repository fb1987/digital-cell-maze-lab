"""Saved audited M25 report draft. No inference, nomination or new cases."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.skill_integration import OUT,check


def main():
    check();assert not (OUT/'report.md').exists()
    def r(name):return json.loads((OUT/name).read_text())
    s=r('summary.json');d=r('saved_diagnostics.json');allocation=r('allocation_persistence.json');p=r('preservation.json');policy=s['policy_comparison']
    sessions={k:r(n) for k,n in [('search','session.json'),('final','final_session.json')]};audits={k:r(k+'_audit.json') for k in sessions}
    assert all(v['status']=='PASS' for v in audits.values())
    lines=['# M25: continued evolution for combined skill retention','',
        f"Completed {sessions['search']['new_rounds']} new rounds, cumulative generation {sessions['search']['generation']}, across six96-slot populations. Registered descriptive policy support: **{policy['descriptive_support']}**. Normal stop `{sessions['search']['stop']['reason']}`; no final-data reselection.",'',
        f"Registration `{r('launch.json')['registration_commit']}` preceded science; choices `{r('choices_freeze.json')['commit']}` preceded fresh1,680-input confirmation. Search and ALL-native final audits pass.",'',
        '## Fixed primary endpoint','',policy['primary']+'.','',
        '| Pair | Current | Integrate | Difference |','|---|---:|---:|---:|']
    for q in policy['pairs']:lines.append(f"| {q['replicate']} | {q['current']} | {q['integrate']} | {q['difference']} |")
    lines += ['',f"Positive pairs {policy['positive_pairs']}/3; sum {policy['total_difference']}. Descriptive support requires positive2/3ANDpositive sum. No significance/general-solving claim or role switching.",'',
        '| Condition/role | Exact identity | M25/inherited mutation births | Paired /400 | Corridors /200 | Ordinary both poses /256 | Correct no-path /168 | False | Raw novel8+ | Gate |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for c in s['conditions']:
        v=c['metrics'];lines.append(f"| {c['condition']}/{c['role']} | {c['child']} | {c['mutations']}/{c['inherited_mutations']} | {v['paired']} | {v['by_domain']['corridor']['optimal']} | {v['ordinary_bases_both_poses']} | {v['correct_no_path']} | {v['false_no_path']} | {c['beyond_root_and_protected_union']['new_long_bases']} | {c['retention_and_disconnection_gate']} |")
    lines += ['', '## Material, comparison and limits','',
        'Three exact M23 enabled ending populations at cumulative243 were forked into current/integrate pairs with identical ordered live genomes, archives, reference objects, evolutionary RNG and cumulative depth. Administrative IDs/names and an entry assessment are new. Full inherited ancestor closure preserved; all nine original M23 states remain untouched. These are related paired continuations, not independent random origins. No M24 ablation or solver was injected into breeding.', '',
        'Same unchanged M18 VM and existing enabled25%append/25%activation-or-payload tuning/50%ordinary grammar;7immigrants+45one-opportunity mutants/round. Both arms receive the same120training inputs (old48fresh+48ordinary bank plus24fixed retention cases), and115×392nominal assessment queries. The added common corridor/disconnection/paired panel improves both curricula, so this tests policies under the common new curriculum, not curriculum causality. Equal logical budgets and opportunities do not imply equal physical work/CPU.', '',
        'Current retains old survival/archive/global-lexicase allocation. Integrate ranks merit/archive entries by worst then average nonempty reference-union domain retention, then complete-unit novelty and ordinary grading. Twelve nonexplorer mutant slots cycle balanced retained parents. Both keep the old imperfect-intermediate niche and explorer breeding. This is a rank/archive/breeding policy package, not isolated causality. Full training gates do not ban temporary losses; independent acceptance requires90%rootANDentryretention, nonempty90%A0disconnection, zero false no-path and positiveM25mutations.', '',
        'Novelty excludes all100unique preM25noncontrol comparison models from M23 final and M24 fixed causal tests, exact root/entry and protected union. This archive is not every historical mutant. Three common fixed development nomination roles; primary uses ONLY INTEGRATED. Secondary specialist/long/upstream/integration outcomes are reported with losses, never substituted for the primary. Parent quota_parent retention comparator differs from actual genetic parent. Fresh confirmation uses whole-layout exclusions including ALL prior/preparation/generated/rejected/unqueried rasters.', '',
        '## Ancestry and secondary responses','',
        f"{d['nominee_aliases']} roles represent {d['nominee_identities']} identities/{d['nominee_genotypes']} genotypes. Roles/aliases are not independent discoveries. Root/actualparent/entry/frozen/M23-ending/reference comparisons, length/family strata and all loss sets are preserved.",'',
        '| Nominee | New edit kinds | New individual inputs beyond archive | New complete ordinary routes (family,size,edges) | Correct16+ / available |',
        '|---|---|---:|---|---:|']
    for identity,x in d['nominees'].items():
        detail=d['model_details'][identity];routes=[(v['family'],v['size'],v['edges']) for v in x['new_ordinary_details']]
        lines.append(f"| {identity} | {json.dumps(x['phase_edit_kinds'])} | {len(x['new_individual_inputs_beyond_archive'])} | {routes} | {detail['length16plus_successes']}/{detail['length16plus_bases']} |")
    lines += ['', '## Allocation, persistence and costs','',
        '| Population | Maximum M25 depth | Extension births on chain | Extension descendants live/archive |',
        '|---|---:|---:|---:|']
    for name,v in allocation['final_persistence'].items():lines.append(f"| {name} | {v['max_M25_mutation_depth']} | {v['max_extension_births_on_chain']} | {v['extension_descendants']} |")
    lines += ['',f"Actual births {json.dumps(d['birth_counts'])}. Opportunity/no-op/fallback, explorer/balanced/lexicase parent allocations, source-root counts and next-train survival are in search_audit.json/allocation_persistence.json. Finite-panel behavioral diversity, wrappers and depth do not establish active routing or causal benefits.",'',
        '| Phase | Physical calls | Candidate seconds | Worker CPU seconds | Elapsed seconds | Counted work | Sampled peak RSS GiB |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for name,session in sessions.items():
        u=session['usage'];lines.append(f"| {name} | {u['calls']:,} | {u['candidate_seconds']:.2f} | {u['cpu_seconds']:.2f} | {session['wall_seconds']:.2f} | {u['work']:,} | {session['rss_peak_bytes']/2**30:.3f} |")
    lines += ['',
        f"Search audit PASS: ALL{audits['search']['independent_grades']:,}grades,{audits['search']['native_replays']:,}native samples,{audits['search']['births_replayed']:,}births,{audits['search']['stages']}corpus/task/selection/mutation/RNG/freeze transitions,{audits['search']['wall_seconds']:.2f}s. Final audit PASS: ALL{audits['final']['native_replays']:,}native outputs/grades/metrics plus{audits['final']['conventional_calls']:,}BFS/A*/bitwave controls,{audits['final']['wall_seconds']:.2f}s. Intact controls all correct. Same production VM/operator, independent raster grader, not a second full VM.", '',
        'Seven focused tests, not full historical suite. Discarded artificial rehearsal267336calls/75.83candidate seconds/936births on old excluded cases. Complete discarded pipeline reuses those search receipts without new inference;6164native search samples,21840old-fixture final calls/8.07candidate seconds andALL21840final-audit native replays plus5040conventional calls. The orchestration smoke reuses artificial receipts and addszero inference. Preparation timestamps/cost records retained; no scientific cases generated before registration.', '',
        'Ten local workers on Apple M4/16GiB. Search70minsoft/90minhard including final assessment/export,1024new rounds maximum,cumulative1267;100Mcalls/1e15work;8GiBsampledRSS/12GiBTOTALstorageincludingbackups/16GiBfreefloor. Final900s/1Mcalls/1e14work;eachaudit3600s. Epoch/monotonicmaxclock counts host sleep. Guards supersede targets; no automatic failed resume or bound extension. Accounting is not a repeated warm latency benchmark.', '',
        f"Preservation {p['status']}: {p['whole_layouts']:,}whole-layout exclusions ({p['initial_layouts']:,}initial+{p['search_new_layouts']:,}search+{p['final_new_layouts']:,}final). Recursive reference+delta ledgers require immutable bases; raw layouts tables are deltas. SQLite-API backups under locks/ALLtables compared; originals preserved. Storage {p['storage_bytes']/2**30:.3f}GiB,free{p['disk_free_bytes']/2**30:.2f}GiB before report/seal. Raw SQLite excluded from Git; compact evidence/logs sealed and pushed.", '',
        'No role reselection, general-solver, speed, significance or independent-origin claim. Review actual results and append thoughtful interpretation/next recommendation before seal; no phase beyondM25 is running. Random-origin capacity/time hypotheses remain open.','']
    (OUT/'report.md').write_text('\n'.join(lines))

if __name__=='__main__':main()
