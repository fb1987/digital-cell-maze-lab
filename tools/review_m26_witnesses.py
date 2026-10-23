"""Independent finite-raster validation and explicit cohort review of M26 witnesses."""
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import resource
import shutil
import sys
import zlib
from collections import Counter,defaultdict

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/evolvability_audit_m26'


def main():
    start,cpu=time.monotonic(),time.process_time()
    assert not (OUT/'witness_review.json').exists()
    with gzip.open(OUT/'cohorts.jsonl.gz','rt') as f:co={r['id']:r for r in map(json.loads,f)}
    with gzip.open(OUT/'novel_complete_witnesses.json.gz','rt') as f:ws=json.load(f)
    interpretation=json.loads((OUT/'interpretation.json').read_text())
    byid=defaultdict(list)
    rasters=0
    con=sqlite3.connect(f'file:{ROOT}/runs/skill_integration_m25/campaign.sqlite?mode=ro',uri=True)
    con.execute('PRAGMA query_only=ON');con.execute('BEGIN')
    checked=set()
    for w in ws:
        assert time.monotonic()-start<1800 and shutil.disk_usage(OUT).free>=16*1024**3
        i=w['id'];byid[i].append(w)
        for identity,receipt in w['receipts'].items():
            key=(receipt['stage'],receipt['task'])
            if key not in checked:
                blob,h=con.execute('select result,result_hash from tasks where stage=? and n=?',key).fetchone()
                assert hashlib.sha256(blob).hexdigest()==h==receipt['result_hash']
                checked.add(key)
        # A saved optimal flag alone is not the raster validation below. Decode
        # actual bits and check free cells, endpoints, simple connected path and
        # length against the already-audited saved oracle, without running a VM.
        for m in w['saved_mazes']:
            cid=m['case_id'];row=next(r for r in w['saved_rows'][i] if r['case']==cid)
            assert row['optimal'] and row['status']=='emitted'
            raw=bytes.fromhex(row['mask']);cells=bytes.fromhex(m['cells_hex']);size=m['w']*m['h']
            bits={j for j in range(len(raw)*8) if raw[j//8] & (1<<(j%8))}
            assert not any(j>=size for j in bits)
            assert all(cells[j] for j in bits)
            assert m['start'] in bits and m['goal'] in bits
            assert len(bits)==m['oracle_length']==len(w['metadata'][cid]['path'])
            def neighbours(j):
                y,x=divmod(j,m['w'])
                return [a for a in (j-m['w'] if y else -1,j+m['w'] if y+1<m['h'] else -1,
                                    j-1 if x else -1,j+1 if x+1<m['w'] else -1) if a in bits]
            for j in bits:assert len(neighbours(j))==(1 if j in (m['start'],m['goal']) else 2)
            pending=[m['start']];visited=set()
            while pending:
                j=pending.pop()
                if j in visited:continue
                visited.add(j);pending.extend(neighbours(j))
            assert visited==bits
            rasters+=1
    con.close()
    mutant={i:v for i,v in interpretation['candidates'].items() if co[i]['mutant']}
    changed={i:v for i,v in mutant.items() if not co[i]['noop']}
    fresh={i:v for i,v in interpretation['candidates'].items() if not co[i]['mutant']}
    def stats(items):
        return dict(identities=len(items),survived_first_hit=sum(v['survived_first_novel_hit'] for v in items.values()),
                    bred_after_hit=sum(bool(v['after_hit_direct_offspring']) for v in items.values()),
                    direct_offspring_after_hit=sum(v['after_hit_direct_offspring'] for v in items.values()),
                    final_live=sum(v['final_live'] for v in items.values()),final_archive=sum(v['final_archive'] for v in items.values()),
                    with_final_live_descendants=sum(bool(v['final_live_descendants']) for v in items.values()),
                    first_exposure_hits=sum(not v['first_hit_after_initial_exposure'] for v in items.values()),
                    later_first_hits=sum(v['first_hit_after_initial_exposure'] for v in items.values()),
                    distinct_bases=len({b for v in items.values() for b in v['all_novel_units']}),
                    instruction_range=[min(v['instructions'] for v in items.values()),max(v['instructions'] for v in items.values())],
                    novel_lengths=dict(Counter(str(v['max_novel_edges']) for v in items.values())))
    sources=Counter()
    for i in mutant:
        for w in byid[i]:
            sources['mutant_witnesses']+=1
            sources['initial_source_queried']+=w['entry_queried']
            sources['initial_source_failed_when_queried']+=w['entry_queried'] and w['entry_solved'] is False
    assert sources['mutant_witnesses']==29
    assert sources['initial_source_queried']==sources['initial_source_failed_when_queried']==29
    assert not any(w['newly_correct_vs_same_panel_parent'] and w['all_parent_correct_inputs_retained'] for w in ws)
    # Every frozen witness is a unique identity presentation in this dataset.
    assert len(ws)==30 and rasters==60 and len(byid)==30
    proof={key:stats(value) for key,value in [('mutants_including_noop',mutant),('changed_mutants_only',changed),('random_immigrants',fresh)]}
    focal=next(i for i,v in changed.items() if v['max_novel_edges']==16)
    r=co[focal];w=byid[focal][0]
    assert r['first']['parent']['no_path']==dict(before=16,retained=0,gained=0,lost=16)
    result=dict(status='PASS',scope='Posthoc cohort clarification and independent saved-raster geometry/length checks. No new inference/cases.',
                groups=proof,all_saved_novel_child_rasters_validated=rasters,original_receipt_hashes_rechecked=len(checked),
                mutation_witness_initial_source_comparisons=dict(sources),
                all_actual_same_panel_parent_new_target_gainers_trade_other_correct_inputs=True,
                focal16=dict(id=focal,parent=r['parent'],root=r['root'],source=w['initial_live_ancestor'],
                             first_parent_comparison=r['first']['parent'],first_root_comparison=r['first']['root']),
                interpretation_clarifications=[
                  'interpretation.json complete8 counts pool ALL 30 M25 identities: 29 mutant identities (28 changed plus one no-op) and one random immigrant.',
                  'Its changed_complete_identities field is the count with noop=False, which includes the random immigrant. Use changed_mutants_only here for mutation-attributed denominators.',
                  'For the immigrant, initial_live_ancestor in the raw witness is itself; there is no pre-M25 phase-entry ancestor. Do not interpret that self comparison as retention.',
                  'Offspring after the first novel hit are counted separately from offspring before that hit. Later missing-parent comparisons remain unavailable.',
                  'All 12 population/stage/base episodes retained at least one matching solver. Losing a redundant mutant identity is not immediate loss of the capability.',
                  'No final live descendants of these identities does not establish when or whether other genotypes lost that exact case; the fresh cases were not repeatedly queried.'
                ],costs=dict(wall_seconds=time.monotonic()-start,cpu_seconds=time.process_time()-cpu,
                   peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),inference_calls=0,generated_layouts=0))
    assert result['costs']['peak_rss_bytes']<4*1024**3
    with (OUT/'witness_review.json').open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(dict(status='PASS',groups=proof,rasters=rasters,costs=result['costs']),indent=2))


if __name__=='__main__':
    try:main()
    except BaseException:
        import traceback
        with (OUT/('witness_review_failure_'+time.strftime('%Y%m%d_%H%M%S')+'.json')).open('x') as f:json.dump(dict(traceback=traceback.format_exc()),f,indent=2)
        raise
