"""Posthoc M25 append-bound accounting from saved events; no inference."""
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from maze_evolution.deep_campaign_store import unpacked
from maze_evolution.skill_integration import OUT, RUN, readz
from maze_evolution.connected_genome import Genome
from tools.m25_export_recovery_a1 import ready_status


def main():
    ready_status()
    target = OUT / 'append_headroom_diagnostics.json'
    assert not target.exists()
    inherited = readz(OUT / 'inherited_registry.json.gz')
    def instructions(item):
        # The VM includes one writer dispatch per nonempty block, not only nodes.
        return Genome.from_dict(item['genome']).instructions
    counts = {i:instructions(e['item']) for i,e in inherited.items()}
    hist, parents = defaultdict(Counter), defaultdict(Counter)
    con = sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro', uri=True)
    con.execute('BEGIN')
    for blob, in con.execute("select decision from stages where kind='train' and complete=1 order by n"):
        for event in unpacked(blob):
            for birth in event['births']:
                item = birth['item']
                identity = item['id']
                assert identity not in counts
                for edit in birth['events']:
                    if edit['opportunity'] != 0:
                        continue
                    parent_count = counts[item['parent']]
                    writer = edit['activation_index'] + 3 > 31
                    total = parent_count + 3 > 128
                    assert (edit['kind'] == 'bounded_noop') == (writer or total)
                    reason = ('both_bounds' if writer and total else 'writer31_only' if writer
                              else 'total128_only' if total else 'admitted')
                    hist[event['name']][reason] += 1
                    parents[event['name']][str(parent_count)] += 1
                counts[identity] = instructions(item)
    con.close()
    audit = json.loads((OUT / 'search_audit.json').read_text())
    for name, values in hist.items():
        expected = audit['variation_counts'][name]
        assert sum(values.values()) == expected['bucket/0']
        assert sum(n for k,n in values.items() if k != 'admitted') == expected.get('kind/bounded_noop', 0)
    result = dict(scope='Posthoc saved operator-event/parent-genome classification; zero inference/case generation. Two independent append bounds; related-history exposures are not causal policy tests.',
        instruction_count_convention='Production Genome.instructions includes nodes plus one dispatch per active writer',
        reason_counts={k:dict(v) for k,v in hist.items()},
        prospective_parent_instruction_histograms={k:dict(v) for k,v in parents.items()},
        all_opportunities_reconcile_to_audit=True,
        previous_failed_count_assumption='postprocessing_failures/headroom_001; nodes-only count excluded writer dispatches, no output created')
    with target.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps(result['reason_counts'], indent=2))


if __name__ == '__main__':
    main()
