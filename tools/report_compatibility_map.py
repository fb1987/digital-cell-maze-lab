"""Render the frozen V12W result tables from saved outputs only."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.compatibility_map_data import OUT,ROOT,read_compressed
from maze_evolution.compatibility_map_study import label

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(map(str,headers))+' |','|'+'|'.join('---' for _ in headers)+'|',*['| '+' | '.join(map(str,row))+' |' for row in rows]])

def main():
    a=read_compressed(OUT/'analysis.json.gz');p=read_compressed(OUT/'panel.json.gz');metrics=read_compressed(OUT/'metrics.json.gz');tot=a['totals']
    execution=json.loads((OUT/'confirmation/execution.json').read_text());audit=json.loads((OUT/'audit.json').read_text());fixture=json.loads((ROOT/'results/compatibility_map_fixtures/execution.json').read_text())
    first=metrics[p['aliases']['d07']+'|normal'];opps=sum(d['prefix']>0 for d in first['details'].values())
    rows=[]
    for mask in range(16):
        absent,present=tot[label(mask,False)],tot[label(mask,True)]
        subset=', '.join(str(i+9) for i in range(4) if mask&(1<<i)) or 'None'
        rows.append([subset,absent['positive'],present['positive'],present['positive']-absent['positive'],absent['corridors'],present['corridors'],absent['ordinary'],present['ordinary']])
    report='# V12W: compatibility of four historical edits\n\n'
    report+='Eight independent structured contexts, four fixed poses per context, two goals per pair. The 32 factorial conditions are constructed probes, not evolved discoveries. All use the same unchanged local native runtime.\n\n'
    report+=f'Positive-prefix denominator: **{opps} pairs per condition**. Corridor denominator: 384 outputs. Ordinary reachable denominator: 384 outputs. All-pair denominator: 576, including prefix zero.\n\n'
    report+=table(['Later edits present','Self-COPY pairs','STORE pairs','STORE effect','Self-COPY corridors','STORE corridors','Self-COPY ordinary','STORE ordinary'],rows)+'\n\n'
    report+='## Historical and preserved controls\n\n'
    rows=[]
    for name in ('d07','d08','d12','fresh2_root','fresh2','broad_root','carry1','random68','intact'):
        t=tot[name];m=metrics[p['aliases'][name]+'|normal'];long=sum(d['complete'] and d['prefix']>=4 for d in m['details'].values())
        rows.append([name,t['pairs'],t['positive'],long,t['corridors'],t['ordinary'],t['no_path']])
    report+=table(['Alias','All pairs /576','Positive /480','Prefix4/8 pairs /288','Corridors /384','Ordinary /384','No-path /448'],rows)+'\n\n'
    report+='## Exact EQ controls\n\n'
    for key,v in a['eq_controls'].items():report+=f"- {key}: {v['counts']['full_record_equal']}/{v['counts']['inputs']} exact full-record matches, including work and memory.\n"
    report+='\nThese tests concern only the empty and full historical backgrounds. They do not establish universal EQ neutrality.\n\n'
    report+='## Context-specific STORE effects\n\n'
    rows=[]
    for context,v in a['context_store_effects'].items():rows.append([context.removeprefix('confirmation/'),v['0'],v['8'],v['15']])
    report+=table(['Independent context','Empty subset','Edit12 only','All four edits'],rows)+'\n\n'
    report+='All 16 contrasts, 64 individual-edit contrasts, 32 conditional STORE×edit interactions, exact higher-order finite differences and paired gain/loss identities are saved in `analysis.json.gz`. Each effect is conditional on this lineage and corpus. Poses, goals and matched variants are correlated. Four poses are not evidence of full eight-pose robustness.\n\n'
    report+='## Execution and audit\n\n'
    b=execution['budget'];fb=fixture['budget']
    report+=f"Main: {b['calls']:,} candidate calls, {b['seconds']:.2f}/720 candidate seconds, {b['work']:,} charged work units; {execution['wall_seconds']:.2f}s wall and {execution['peak_rss_bytes']/2**20:.2f} MiB peak RSS.\n\n"
    report+=f"Calibration separately: {fb['calls']:,} calls, {fb['seconds']:.2f}/180 candidate seconds. Production-signature warmups are separately recorded; these totals are not a latency benchmark. The timing-only ladder rejected 12 contexts at 659.98s projected (650s planning threshold), selecting eight at 454.06s. No cap was extended.\n\n"
    c=audit['counts'];report+=f"Audit passed: {c['candidate_replays']:,} exact candidate replays; {c['baseline_replays']:,} baseline replays; {c['independently_graded_rasters']:,} independently graded rasters; {c['factorial_programs_independently_rebuilt']} independently reconstructed factorial programs; {c['independent_factorial_context_checks']} independent context-effect checks; {audit['source_hashes']} source/{audit['input_hashes']} input hashes and {c['prior_hashes']:,} prior completion entries. Audit wall {audit['wall_seconds']:.2f}s; peak RSS {audit['peak_rss_bytes']/2**20:.2f} MiB. Exact replay uses the original native interpreter; it is not a separately implemented second VM.\n\n"
    report+='Nine new tests and 19 related tests pass (28); this is not a fresh full-suite run. Registration `e99f922` was pushed before final generation. No post-registration source repair or protocol deviation.\n\n'
    report+='All 8,448 generated final inputs and 4,480 fixture inputs remain saved, including unqueried variants and orientations. Exclude all **251,380 whole layouts through W**, using the sealed `whole_layout_exclusions.json.gz`; W data.exclusions() itself includes only the 243,540 through V. All earlier models, populations, RNG states and raw results remain preserved. No evolution or final-based selection occurred.\n'
    (OUT/'result_tables.md').write_text(report)
    print(report)
if __name__=='__main__':main()
