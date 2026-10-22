"""Post-audit M20 diagnostics from saved records only; no reselection."""
import sys,json,sqlite3,hashlib
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.copy_specialization import ROOT,OUT,RUN,check,readz,writej,load,references
from maze_evolution.deep_campaign_store import unpacked,packed,hashed
from maze_evolution.specialization_genome import Genome
from maze_evolution.breeding_allocation_metrics import capabilities_plus


def main():
    check();assert not (OUT/'interpretation.json').exists()
    for name in ('screen','final'):assert json.loads((OUT/f'{name}_audit.json').read_text())['status']=='PASS'
    pool=readz(OUT/'pool.json.gz');selection=readz(OUT/'selection.json.gz');choices=readz(OUT/'choices.json.gz')
    summary=json.loads((OUT/'summary.json').read_text());lookup={i['id']:i for i in pool['items']};allocation=defaultdict(Counter)
    instructions=defaultdict(list)
    for i in pool['items']:
        if i['kind']!='mutation':continue
        a=allocation[i['arm']];a['proposals']+=1;a['opportunities']+=len(i['steps'])
        base=Genome.from_dict(lookup[i['copy_base']]['model']['genome']);last=Genome.from_dict(i['model']['genome'])
        a['endpoint_equals_copy_base']+=last.digest==base.digest
        a['active_other_spare']+=bool(last.body.blocks[9 if i['target']==8 else 8])
        instructions[i['arm']].append(last.instructions)
        for step in i['steps']:
            e=step['event'];a['kind/'+e['kind']]+=1;a['block/'+str(e['block'])]+=1
            a['genotype_noops']+=e['before']==e['after']
            if i['arm']=='local':
                g=Genome.from_dict(step['genome'])
                for k in set(range(10))-set(i['scope']):
                    assert (g.body.blocks[k],g.body.ports[k],g.initialization[k])==(base.body.blocks[k],base.body.ports[k],base.initialization[k])
        f=selection['features'][i['id']]
        for label in ('additive_pass','combined_parent_child_pass','all_anchor_correct_retained'):
            a['screen/'+label]+=f[label]
        clean=f['all_anchor_correct_retained'] and not f['metrics']['false_no_path']
        a['screen/clean_retention']+=clean
        a['screen/addition_without_disconnection_gate']+=bool(clean and any(f['new_skill_units'].values()))
        a['screen/novel_upstream']+=bool(f['new_upstream_beyond_protected'])
        a['screen/novel_ordinary']+=bool(f['new_ordinary_beyond_protected'])
    assert all(v['proposals']==1024 and v['opportunities']==4096 for v in allocation.values())
    paired=defaultdict(Counter)
    for anchor in ('parent','child'):
        for draw in range(512):
            ids=[i for i in pool['items'] if i['kind']=='mutation' and i['anchor']==anchor and i['paired_draw']==draw]
            assert len(ids)==2
            ff={i['arm']:selection['features'][i['id']] for i in ids};depth=ids[0]['depth'];c=paired[anchor+'/d'+str(depth)]
            clean={arm:f['all_anchor_correct_retained'] and not f['metrics']['false_no_path'] for arm,f in ff.items()}
            c['pairs']+=1;c['both_clean']+=all(clean.values());c['neither_clean']+=not any(clean.values())
            c['local_only_clean']+=clean['local'] and not clean['generic'];c['generic_only_clean']+=clean['generic'] and not clean['local']
    data,rows,models=load(True);queried=set(data['queries']['all'])
    om={m['base']:m for cid,m in data['metadata'].items() if cid in queried and m['family'] in ('ordinary_perfect','ordinary_random')}
    assert len(om)==256
    long16={b for b,m in om.items() if len(m['path'])-1>=16};caps={i:capabilities_plus(rs,data['metadata']) for i,rs in rows.items()}
    protected=list(readz(OUT/'sources.json.gz')['protected'])
    protected_success=set().union(*(caps[i]['success'] for i in protected))
    protected_ordinary=set().union(*(caps[i]['ordinary_bases'] for i in protected))
    final_items={i['id']:i for i in choices['items']};nominees={}
    for n in choices['nominations']:
        identity=n['identity']
        if identity in nominees:continue
        item=final_items[identity];anchor='anchor/'+item['anchor'];base=item['copy_base']
        comparisons={}
        for label,other in [('anchor',anchor),('copy',base)]:
            comparisons[label]=dict(same_mask_status_steps=sum(all(a[k]==b[k] for k in ('mask','status','steps')) for a,b in zip(rows[identity],rows[other])),
                same_mask=sum(a['mask']==b['mask'] for a,b in zip(rows[identity],rows[other])),new_correct=len(caps[identity]['success']-caps[other]['success']),
                lost_correct=len(caps[other]['success']-caps[identity]['success']))
        nominees[identity]=dict(anchor=anchor,copy_base=base,scope=item['scope'],edit_opportunities=item['depth'],
            initialization_copy_events=1,source_id=readz(OUT/'sources.json.gz')['anchors'][item['anchor']]['id'],
            edit_kinds=[s['event']['kind'] for s in item['steps']],edit_blocks=[s['event']['block'] for s in item['steps']],
            new_individual_inputs_beyond_protected=sorted(caps[identity]['success']-protected_success),
            new_ordinary_details_beyond_protected=[dict(base=b,family=om[b]['family'],size=om[b]['size'],edges=len(om[b]['path'])-1,
                novel_individual_poses=sum(r['case'] not in protected_success for r in rows[identity] if data['metadata'][r['case']].get('base')==b))
                for b in sorted(caps[identity]['ordinary_bases']-protected_ordinary)],
            comparisons_scope='Same registered final inputs, source/own copy/all protected references',
            comparisons=comparisons,long16_available=len(long16),long16_correct=len(long16&caps[identity]['ordinary_bases']),
            correct_ordinary_edges=sorted(len(om[b]['path'])-1 for b in caps[identity]['ordinary_bases']))
    buckets={}
    for e,rs in models:
        labels=sorted({final_items[i].get('arm','common_reference') for i in e['aliases']})
        k='|'.join(labels);b=buckets.setdefault(k,dict(calls=0,work=0))
        b['calls']+=len(rs);b['work']+=sum(r['reads']+r['dispatches']+r['exposure_checks'] for r in rs)
    session=json.loads((OUT/'final_session.json').read_text())
    assert sum(v['calls'] for v in buckets.values())==session['usage']['calls']
    all_items=pool['items']+references(readz(OUT/'sources.json.gz'));all_lookup={i['id']:i for i in all_items}
    physical_costs={};audit_costs={};common_screen={}
    for phase in ('screen','final'):
        phase_buckets={};sample_calls=sample_work=0
        con=sqlite3.connect(f'file:{RUN/phase}/campaign.sqlite?mode=ro',uri=True)
        for spec,rb in con.execute('select spec,result from tasks order by n'):
            for e,r in zip(unpacked(spec),unpacked(rb)['entries']):
                labels=sorted({all_lookup[i].get('arm','common') for i in e['aliases']});label='|'.join(labels)
                b=phase_buckets.setdefault(label,dict(calls=0,work=0,candidate_seconds=0.))
                for field in b:b[field]+=r[field]
                key=hashed(packed(e['model']))
                for row in r['rows']:
                    if phase=='final' or int(hashlib.sha256((key+'/'+row['case']).encode()).hexdigest(),16)%32==0:
                        sample_calls+=1;sample_work+=row['reads']+row['dispatches']+row['exposure_checks']
                if phase=='screen':
                    for i in e['aliases']:
                        if all_lookup[i]['kind'] in ('copy_base','reference'):common_screen[i]=r['rows']
        con.close();usage=json.loads((OUT/f'{phase}_session.json').read_text())['usage']
        assert sum(v['calls'] for v in phase_buckets.values())==usage['calls']
        assert sum(v['work'] for v in phase_buckets.values())==usage['work']
        assert sample_calls==json.loads((OUT/f'{phase}_audit.json').read_text())['native_replays']
        physical_costs[phase]=phase_buckets;audit_costs[phase]=dict(native_calls=sample_calls,native_counted_work=sample_work,
            provenance='Deterministic work summed from scientific rows verified equal in native audit; no additional executions')
    screen_data=readz(OUT/'screen_cases.json.gz');screen_caps={i:capabilities_plus(rs,screen_data['metadata']) for i,rs in common_screen.items()}
    copy_checks={}
    for item in pool['items']:
        if item['kind']!='copy_base':continue
        identity=item['id'];anchor='anchor/'+item['anchor'];a=screen_caps[identity];b=screen_caps[anchor]
        copy_checks[identity]=dict(anchor=anchor,all_anchor_correct_retained=b['success']<=a['success'],
            lost_correct=len(b['success']-a['success']),new_correct=len(a['success']-b['success']),
            lost_correct_no_path=len(b['correct_no_path']-a['correct_no_path']),
            mask_status_steps_equal=sum(all(x[k]==y[k] for k in ('mask','status','steps')) for x,y in zip(common_screen[identity],common_screen[anchor])))
    equivalence=defaultdict(list)
    for identity in nominees:equivalence[hashed(packed([(r['mask'],r['status'],r['steps']) for r in rows[identity]]))].append(identity)
    writej(OUT/'interpretation.json',dict(scope='Saved audited M20 records only; no additional inference, cases or nomination.',
        allocation={k:dict(v) for k,v in allocation.items()},paired_screen_retention={k:dict(v) for k,v in paired.items()},
        instruction_ranges={k:[min(v),max(v)] for k,v in instructions.items()},
        nominees=nominees,nominee_aliases=len(choices['nominations']),nominee_identities=len(nominees),
        nominee_genotypes=len({Genome.from_dict(final_items[i]['model']['genome']).digest for i in nominees}),
        final_physical_cost_buckets=buckets,physical_cost_buckets=physical_costs,audit_native_costs=audit_costs,
        nominee_terminal_equivalence_groups=list(equivalence.values()),
        copy_bases_screen=copy_checks,queried_ordinary_bases=256,queried_long16_bases=len(long16)))
    print('M20 saved diagnostics complete:',len(nominees),'nominee identities',flush=True)


if __name__=='__main__':main()
