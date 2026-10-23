"""Recover complete ordinary-event metadata from frozen seeds, without inference.

M28's common event wrapper uses 'donor' for the matched second genome. In the
ordinary copy_block suboperator that name originally means a channel index.
Keep both meanings in this additive record; frozen pool/events remain untouched.
"""
import random,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.integration_accessibility import OUT,check,readz,writez,Genome
from maze_evolution.connected_evolution_genome import ordinary
from maze_evolution.deep_campaign_store import hashed,packed


def main():
    check();path=OUT/'ordinary_event_details.json.gz';assert not path.exists()
    pool=readz(OUT/'pool.json.gz');items={x['id']:x for x in pool['items']};records=[]
    for c in pool['conditions']:
        if c['arm']!='mutation':continue
        rng=random.Random(c['seed']);a=Genome.from_dict(items[c['recipient']]['model']['genome']);child,event=ordinary(a,rng)
        assert child.to_dict()==items[c['id']]['model']['genome'] and event['after']==c['event']['after']
        assert hashed(packed(rng.getstate()))==c['rng_after']
        records.append(dict(id=c['id'],recipient=c['recipient'],matched_partner_not_genetic_parent=c['donor'],raw_ordinary_event=event))
    assert len(records)==608
    writez(path,dict(status='PASS',records=records,scientific_evaluations=0,source_genomes_unchanged=True,
        scope='Additive raw metadata reconstruction, not changed science. The control has ONE genetic parent; both matched sources remain comparison targets.'))


if __name__=='__main__':main()
