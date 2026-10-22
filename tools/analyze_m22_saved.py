"""Saved M22 accounting/profiles only. No candidate execution or reselection."""
import json,sqlite3,hashlib,time,sys
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.guarded_extension import ROOT,OUT,RUN,check,readz,writej,load,references
from maze_evolution.guarded_extension_genome import ARMS,ANCHORS,Genome
from maze_evolution.deep_campaign_store import packed,unpacked,hashed
from maze_evolution.breeding_allocation_metrics import capabilities_plus

def main():
    started=time.monotonic();check();assert not (OUT/'saved_diagnostics.json').exists()
    for phase in ('screen','final'):assert json.loads((OUT/f'{phase}_audit.json').read_text())['status']=='PASS'
    pool=readz(OUT/'pool.json.gz');selection=readz(OUT/'selection.json.gz');sources=readz(OUT/'sources.json.gz')
    all_items=pool['items']+references(sources);lookup={i['id']:i for i in all_items};allocation={a:Counter() for a in ARMS};sizes=defaultdict(list)
    for i in pool['items']:
        if i['kind']!='mutation':continue
        a=allocation[i['arm']];a['proposals']+=1;a['opportunities']+=len(i['steps'])
        original=Genome.from_dict(sources['anchors'][i['anchor']]['genome']);last=original
        sizes[i['arm']].append(Genome.from_dict(i['model']['genome']).instructions)
        for step in i['steps']:
            g=Genome.from_dict(step['genome']);e=step['event'];a['kind/'+e['kind']]+=1;a['writer/'+str(e['block'])]+=1
            a['genotype_noop_opportunities']+=e['before']==e['after']
            if i['arm']!='ordinary':
                assert g.body.ports==original.body.ports and g.initialization==original.initialization
                assert all(g.body.blocks[k][:len(b)]==b for k,b in enumerate(last.body.blocks))
                if e['kind']!='bounded_noop':
                    assert g.instructions==last.instructions+2
                    a['payload_private_reuse']+=e['payload_reuses_private_expression']
            last=g
        assert last.to_dict()==i['model']['genome']
        f=selection['features'][i['id']]
        for key in ('strict_novel_additive_pass','additive_including_archive_recovery','clean_source_retention'):a['screen/'+key]+=f[key]
        a['screen/novel_individual_gainer']+=bool(f['new_individual_inputs_beyond_archive'])
        a['screen/novel_complete_unit_gainer']+=any(f['novel_units_beyond_archive'].values())
    matched={};trios=defaultdict(dict)
    for i in pool['items']:
        if i['kind']=='mutation':trios[i['anchor'],i['paired_draw']][i['arm']]=i
    for (anchor,draw),trio in trios.items():
        a=trio['guarded'];b=trio['overwrite'];c=matched.setdefault(anchor+'/d'+str(a['depth']),Counter())
        assert a['edit_seed']==b['edit_seed'] and len(a['steps'])==len(b['steps'])
        for x,y in zip(a['steps'],b['steps']):
            assert x['rng_after']==y['rng_after']
            for field in ('block','old_register','new_register','condition','new_when_true','payload'):
                assert x['event'][field]==y['event'][field]
            gx=Genome.from_dict(x['genome']);gy=Genome.from_dict(y['genome'])
            assert gx.instructions==gy.instructions and [len(z) for z in gx.body.blocks]==[len(z) for z in gy.body.blocks]
        clean={arm:selection['features'][item['id']]['clean_source_retention'] for arm,item in trio.items()}
        c['draws']+=1;c['both_extension_arms_clean']+=clean['guarded'] and clean['overwrite']
        c['guarded_only_clean']+=clean['guarded'] and not clean['overwrite'];c['overwrite_only_clean']+=clean['overwrite'] and not clean['guarded']
        c['neither_extension_clean']+=not clean['guarded'] and not clean['overwrite'];c['ordinary_clean']+=clean['ordinary']
    choices=readz(OUT/'choices.json.gz');data,rows,_=load(True);caps={i:capabilities_plus(r,data['metadata']) for i,r in rows.items()}
    archive=list(sources['protected']);union=set().union(*(caps[i]['success'] for i in archive));arch_profile=defaultdict(list);arch_success=defaultdict(list)
    archive_ordinary=set().union(*(caps[i]['ordinary_bases'] for i in archive))
    archive_pairs=set().union(*(caps[i]['pairs'] for i in archive))
    for i in archive:
        arch_profile[hashed(packed([(r['mask'],r['status'],r['steps']) for r in rows[i]]))].append(i)
        arch_success[hashed(packed(sorted(caps[i]['success'])))].append(i)
    genotype_archive=defaultdict(list)
    for i in references(sources):
        if i['kind']=='protected':genotype_archive[hashed(packed(i['model']))].append(i['id'])
    om={m['base']:m for cid,m in data['metadata'].items() if cid in data['queries']['all'] and m['family'] in ('ordinary_perfect','ordinary_random')}
    long16={b for b,m in om.items() if len(m['path'])-1>=16};nominees={}
    for n in choices['nominations']:
        i=n['identity']
        if i in nominees:continue
        profile=hashed(packed([(r['mask'],r['status'],r['steps']) for r in rows[i]]));c=caps[i]
        index={r['case']:r for r in rows[i]}
        v=lookup[i];entry=dict(source=v.get('anchor'),role_labels=[x['label'] for x in choices['nominations'] if x['identity']==i],
            exact_archive_genotype_matches=genotype_archive.get(hashed(packed(v['model'])),[]),
            exact_archive_mask_status_tick_matches=arch_profile.get(profile,[]),archive_correct_set_matches=arch_success.get(hashed(packed(sorted(c['success']))),[]),
            new_inputs_beyond_archive=sorted(c['success']-union),long16_denominator=len(long16),long16_correct=len(long16&c['ordinary_bases']),
            ordinary_correct_edges=sorted(len(om[b]['path'])-1 for b in c['ordinary_bases']),
            novel_ordinary_details=[dict(base=b,family=om[b]['family'],size=om[b]['size'],edges=len(om[b]['path'])-1,
                responses=[{k:r[k] for k in ('case','status','steps','optimal','valid','failure','reads','dispatches')} for r in rows[i] if data['metadata'][r['case']].get('base')==b]) for b in sorted(c['ordinary_bases']-archive_ordinary)],
            novel_complete_pairs=[dict(base=p[0],pose=p[1]) for p in sorted(c['pairs']-archive_pairs)],
            novel_individual_details=[dict(case=cid,metadata=data['metadata'][cid],response={k:index[cid][k] for k in ('status','steps','optimal','valid','no_path','failure')}) for cid in sorted(c['success']-union)],
            phase_only_opportunities=len(v.get('steps',[])),source_provenance=sources['anchors'].get(v.get('anchor')))
        if v.get('anchor'):
            root='anchor/'+v['anchor'];entry['same_source_mask_status_ticks']=sum(all(a[k]==b[k] for k in ('mask','status','steps')) for a,b in zip(rows[i],rows[root]))
            entry['lost_source_correct_no_path']=len(caps[root]['correct_no_path']-c['correct_no_path'])
            entry['new_source_correct_no_path']=len(c['correct_no_path']-caps[root]['correct_no_path'])
        nominees[i]=entry
    costs={};audits={}
    for phase in ('screen','final'):
        buckets={};calls=work=0;con=sqlite3.connect(f'file:{RUN/phase}/campaign.sqlite?mode=ro',uri=True)
        for sb,rb in con.execute('select spec,result from tasks order by n'):
            for e,result in zip(unpacked(sb),unpacked(rb)['entries']):
                labels=sorted({lookup[i].get('arm',lookup[i]['kind']) for i in e['aliases']});label='|'.join(labels)
                b=buckets.setdefault(label,dict(calls=0,work=0,candidate_seconds=0.))
                for k in b:b[k]+=result[k]
                h=hashed(packed(e['model']))
                for row in result['rows']:
                    if phase=='final' or int(hashlib.sha256((h+'/'+row['case']).encode()).hexdigest(),16)%32==0:
                        calls+=1;work+=row['reads']+row['dispatches']+row['exposure_checks']
        con.close();usage=json.loads((OUT/f'{phase}_session.json').read_text())['usage']
        for k in ('calls','work'):assert sum(b[k] for b in buckets.values())==usage[k]
        assert calls==json.loads((OUT/f'{phase}_audit.json').read_text())['native_replays']
        costs[phase]=buckets;audits[phase]=dict(native_calls=calls,native_counted_work=work)
    for a,v in allocation.items():assert v['proposals']==768 and v['opportunities']==3072
    writej(OUT/'saved_diagnostics.json',dict(status='PASS',scope='Saved audited M22 records, no new candidate execution or reselection',
        allocation={a:dict(c) for a,c in allocation.items()},matched={k:dict(v) for k,v in matched.items()},
        ending_instruction_ranges={a:[min(x),max(x)] for a,x in sizes.items()},nominees=nominees,
        archive_aliases=len(archive),archive_genotypes=len(genotype_archive),queried_reachable_ordinary_bases=len(om),long16_denominator=len(long16),
        cost_buckets=costs,audit_native_costs=audits,wall_seconds=time.monotonic()-started))
    print('M22 saved accounting PASS',len(nominees),'identities')

if __name__=='__main__':main()
