"""M19 saved-data interpretation and allocation only; no inference or selection."""
import sys,json,sqlite3
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.connected_evolution import ROOT,OUT,RUN,check,writej,readz
from maze_evolution.connected_evolution_analysis import final_load
from maze_evolution.breeding_allocation_metrics import capabilities_plus,upstream_pairs,comparison
from maze_evolution.connected_evolution_genome import Genome,graph
from maze_evolution.deep_campaign_store import unpacked,packed,hashed


def main():
    check();assert not (OUT/'saved_diagnostics.json').exists() and not (OUT/'allocation_persistence.json').exists()
    assert json.loads((RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
    audits={k:json.loads((OUT/f'{k}_audit.json').read_text()) for k in ('search','final')};assert all(x['status']=='PASS' for x in audits.values())
    choices=readz(OUT/'choices.json.gz');data,rows,models,usage,chain=final_load()
    # The all-layout ledger also retains metadata for generated, unqueried poses.
    # Denominators must describe only the registered final query panel.
    queried=set(data['queries']['all']);meta={k:v for k,v in data['metadata'].items() if k in queried}
    assert len(meta)==len(queried)==1680
    assert all({r['case'] for r in rs}==queried for rs in rows.values())
    s=json.loads((OUT/'summary.json').read_text());caps={i:capabilities_plus(rs,meta) for i,rs in rows.items()}
    protected=s['protected_identities'];union={k:set().union(*(caps[i][k] for i in protected)) for k in ('pairs','corridors','ordinary_bases','correct_no_path','success')}
    ordinary={m['base']:m for m in meta.values() if m['family'] in ('ordinary_perfect','ordinary_random')}
    assert len(ordinary)==256
    details={}
    for identity,cap in caps.items():
        good=cap['ordinary_bases'];long16={b for b,m in ordinary.items() if len(m['path'])-1>=16}
        details[identity]=dict(length16plus_bases=len(long16),length16plus_successes=len(good&long16),
            max_correct_ordinary_edges=max((len(ordinary[b]['path'])-1 for b in good),default=None))
    ancestry=readz(OUT/'ancestry.json.gz');nominees={}
    for c in s['conditions']:
        identity=c['child']
        if identity in nominees:continue
        cap=caps[identity];hist=[];cur=identity
        while cur:
            assert cur not in hist;hist.append(cur);cur=ancestry[cur]['item']['parent']
        edits=[e for i in hist if ancestry[i]['phase']=='M19' for e in ancestry[i]['events']]
        assert len(edits)==c['mutations']
        g=Genome.from_dict(choices['items'][identity]['genome']);reads=graph(g);cone={2,7}
        while True:
            more=cone|{d for k in cone for d in reads[k]}
            if more==cone:break
            cone=more
        new_ordinary=cap['ordinary_bases']-union['ordinary_bases']-caps[c['phase_entry']]['ordinary_bases']
        nominees[identity]=dict(phase_entry=c['phase_entry'],root=c['root'],parent=c['parent'],M19_mutation_births=c['mutations'],
            inherited_source_study_mutations=c['inherited_mutations'],chain=hist,phase_edit_kinds=dict(Counter(e['kind'] for e in edits)),
            new_individual_inputs_beyond_protected=sorted(cap['success']-union['success']),
            new_nonfork_prefix2_pairs_beyond_protected=len(upstream_pairs(cap,meta)-upstream_pairs(union,meta)),
            new_ordinary_details=[dict(base=b,family=ordinary[b]['family'],size=ordinary[b]['size'],edges=len(ordinary[b]['path'])-1) for b in sorted(new_ordinary)],
            root_comparison=comparison(cap,caps[c['root']],meta),entry_comparison=comparison(cap,caps[c['phase_entry']],meta),
            output_halt_channel_cone=sorted(cone),spares_in_conservative_output_halt_cone=sorted(cone&{8,9}),
            response_matches_root={k:sum(a[k]==b[k] for a,b in zip(rows[identity],rows[c['root']])) for k in ('mask','status','steps')},
            response_matches_entry={k:sum(a[k]==b[k] for a,b in zip(rows[identity],rows[c['phase_entry']])) for k in ('mask','status','steps')})
    con=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True);con.execute('BEGIN')
    initial=unpacked(con.execute('select value from states where stage=-1').fetchone()[0]);labels=[x['arm'] for x in initial]
    inherited=readz(OUT/'inherited_registry.json.gz');phase_depth={i:0 for i in inherited}
    copy_depth={i:0 for i in inherited};births=Counter();kinds=defaultdict(Counter);active=defaultdict(Counter);buckets={}
    for blob, in con.execute("select decision from stages where kind='train' and complete=1 order by n"):
        for event in unpacked(blob):
            name=event['name']
            for birth in event['births']:
                item=birth['item'];identity=item['id'];parent=item['parent'];edit=birth['events']
                assert identity not in phase_depth
                phase_depth[identity]=(phase_depth[parent]+1) if parent else 0
                copy_depth[identity]=(copy_depth[parent] if parent else 0)+sum(e['kind'].startswith('initialized_') for e in edit)
                births['mutation' if edit else 'immigrant']+=1
                if edit:kinds[name][edit[0]['kind']]+=1
                g=Genome.from_dict(item['genome']);active[name][str(sum(bool(b) for b in g.body.blocks[8:]))]+=1
    for spec,result in con.execute('select spec,result from tasks order by stage,n'):
        spec=unpacked(spec);result=unpacked(result)
        for e,r in zip(spec,result['entries']):
            label='|'.join(sorted({labels[k] for k,identity in e['aliases']}));bucket=buckets.setdefault(label,dict(calls=0,work=0,candidate_seconds=0.))
            for k in bucket:bucket[k]+=r[k]
    latest=unpacked(con.execute('select value from states where stage=(select max(stage) from states)').fetchone()[0]);con.close()
    persistence={}
    for state in latest:
        pool={i['id']:i for group in ('population','archive') for i in state[group]}
        persistence[state['name']]=dict(live_and_archive_identities=len(pool),max_M19_mutation_depth=max(phase_depth[i] for i in pool),
            max_copy_births_on_a_chain=max(copy_depth[i] for i in pool),
            live_and_archive_copy_descendants=sum(copy_depth[i]>0 for i in pool),
            live_and_archive_active_spares=dict(Counter(str(sum(bool(b) for b in Genome.from_dict(i['genome']).body.blocks[8:])) for i in pool.values())))
    session=json.loads((OUT/'session.json').read_text());assert sum(births.values())==9*52*session['new_rounds']==audits['search']['births_replayed']
    assert births['mutation']==9*45*session['new_rounds'] and births['immigrant']==9*7*session['new_rounds']
    assert sum(x['calls'] for x in buckets.values())==session['usage']['calls']
    assert sum(x['work'] for x in buckets.values())==session['usage']['work']
    for name,counter in kinds.items():
        for kind,count in counter.items():assert audits['search']['variation_counts'][name]['kind/'+kind]==count
    writej(OUT/'saved_diagnostics.json',dict(scope='Saved audited records only; no new cases, inference, mutation or selection. Static cones are potential dependencies, not a causal trace.',
        nominees=nominees,nominee_aliases=len(s['conditions']),nominee_identities=len(nominees),
        nominee_genotypes=len({hashed(packed(choices['items'][i]['genome'])) for i in nominees}),model_details=details,birth_counts=dict(births)))
    writej(OUT/'allocation_persistence.json',dict(scope='Audited training/final states; shared physical work buckets partition by ALL arm labels, never double-counted. Immediate survival is measured only when a next train exists.',
        phase_edit_kinds={k:dict(v) for k,v in kinds.items()},born_active_spares={k:dict(v) for k,v in active.items()},
        final_persistence=persistence,search_physical_cost_buckets=buckets,
        variation_counts=audits['search']['variation_counts'],immediate_birth_survival=audits['search']['immediate_birth_survival'],
        nominal_queries=audits['search']['logical_query_counts']))
    print('M19 saved interpretation:',len(nominees),'nominee identities;',dict(births))

if __name__=='__main__':main()
