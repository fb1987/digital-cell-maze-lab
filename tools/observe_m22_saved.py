"""Private-register and branch-use accounting on saved audited M22 histories."""
import base64,json,time,sys
from pathlib import Path
from collections import Counter
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.guarded_extension import OUT,RUN,check,readz,writej,guard,Genome
from maze_evolution.guarded_extension_observer import frame
from maze_evolution.deep_campaign_data import cases_from_manifest

def main():
    config=check();assert not (OUT/'branch_usage.json').exists()
    assert json.loads((OUT/'trace_audit.json').read_text())['status']=='PASS'
    started=time.monotonic();data=readz(OUT/'final_cases.json.gz');choices=readz(OUT/'choices.json.gz');items={i['id']:i for i in choices['items']}
    trace=readz(OUT/'traces.json.gz');ids={r['case'] for r in trace['records']};cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in ids])
    results={};checked=scalar_dispatches=0
    for r in trace['records']:
        aliases=[i for i in r['aliases'] if i in items and items[i].get('arm')=='guarded']
        if not aliases:continue
        item=items[aliases[0]];genome=Genome.from_dict(item['model']['genome']);wrappers={}
        for step in item['steps']:
            e=step['event']
            if e['kind']=='guarded_extension':wrappers.setdefault(e['block'],[]).append(e)
        a=np.frombuffer(base64.b64decode(r['history_base64']),np.uint16).reshape(r['shape']);maze=cases[r['case']].maze
        counters=Counter();by_writer={}
        assert not guard(RUN,dict(config,session_wall_seconds=config['audit_wall_seconds']),started)
        for module,events in wrappers.items():
            c=Counter();block=genome.body.blocks[module]
            for tick in range(len(a)-1):
                for p,opened in enumerate(maze.cells):
                    if not opened:continue
                    regs=frame(block,genome.body.ports[module],a[tick],maze,p)
                    assert regs[block[-1].dst]==a[tick+1,module,p]
                    checked+=1;scalar_dispatches+=len(block)
                    for e in events:
                        old,new=e['old_register'],e['new_register'];gene=block[new+1-12]
                        assert gene.row()==e['terminal'] and gene.op==12 and gene.gate==64
                        choose_new=bool(regs[e['condition']])==e['new_when_true']
                        assert regs[gene.dst]==regs[new if choose_new else old]
                        unequal=regs[old]!=regs[new];label='new' if choose_new else 'old'
                        c['executed_selector_observations']+=1;c[label+'_selected']+=1
                        c[label+'_selected_with_unequal_values']+=unequal
                        if e is events[-1]:
                            c['outermost_observations']+=1;c['outermost_'+label+'_selected']+=1
                            c['outermost_'+label+'_with_unequal_values']+=unequal
            by_writer[str(module)]=dict(c);counters.update(c)
        for identity in aliases:
            v=results.setdefault(identity,dict(totals=Counter(),cases={}))
            v['totals'].update(counters);v['cases'][r['case']]=dict(totals=dict(counters),by_writer=by_writer,
                completed_ticks=len(a)-1,status=r['row']['status'],steps=r['row']['steps'])
    for identity,v in results.items():v['totals']=dict(v['totals'])
    writej(OUT/'branch_usage.json',dict(status='PASS',models=results,verified_module_site_ticks=checked,
        scalar_node_dispatches=scalar_dispatches,wall_seconds=time.monotonic()-started,
        scope='Posthoc independent scalar reconstruction on ALL saved guarded-nominee completed-tick traces. No new trajectories/cases or selection.',
        limits='12 metadata-selected cases; executed nested selectors may be private/inactive; outermost and unequal-value counts separate. Branch use does not prove a useful added skill.'))
    print('M22 saved-frame observer PASS',checked,'module-site-ticks')

if __name__=='__main__':main()
