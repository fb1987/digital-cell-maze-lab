"""Pre-training exact old-program equivalence on independent inputs; no selection."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from .regulatory import Genome as OldGenome
from .beacon_runtime import Organism as OldOrganism
from .beacon_probe import observe
from .growth import Genome,Individual
from .growth_runtime import Organism
from .growth_fitness import evaluate
from .choice_fitness import evaluate as old_evaluate
from .growth_data import GrowthData
from .experiment import write_json
from .runtime import Limits


def compare(a,b,array):
    assert np.array_equal(getattr(a,array),getattr(b,array))
    assert {k:v for k,v in vars(a).items() if k!=array}=={k:v for k,v in vars(b).items() if k!=array}


def run(out):
    out=Path(out);root=Path(__file__).resolve().parents[1]
    if out.exists():raise FileExistsError('Choose a fresh equivalence packet')
    started=time.perf_counter();programs={};inputs={}
    def add(topology,item):
        old=OldGenome.from_dict(item['genome']);programs.setdefault((topology,old.digest),old)
    for topology in ('local','evolved'):
        for rep in range(3):
            for arm in ('fixed','curriculum'):
                p=root/f'results/distance_curriculum/checkpoints/distance_{topology}_{arm}_{rep}.json';inputs[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest();r=json.loads(p.read_text())
                for item in r['population']+r['protected']+[v['individual'] for v in r['archives'].values()]:add(topology,item)
    for name in ('strict_validation_archive.json','training_choice_diagnostic.json'):
        p=root/'results/distance_curriculum'/name;inputs[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest();r=json.loads(p.read_text())
        if name.startswith('strict'):
            for key,record in r['records'].items():add(key.split('/')[1],record['individual'])
        else:
            for record in r['records']:
                for node in record['nodes']:add(record['condition'].split('/')[1],node['individual'])
    data=GrowthData(1113);validation=data.validation(0);cases=[validation[0].first,validation[4].second,validation[2].second]
    limits=Limits(max_steps=64,reads_per_site=4096,instructions_per_site=32768);normal=probe=fitness=work=0
    for index,((topology,digest),old) in enumerate(sorted(programs.items())):
        g=Genome.from_dict(old.to_dict());assert g.digest==digest and np.array_equal(g.array(),old.array())
        a=Organism(g,topology,limits,goal_pulse=True);b=OldOrganism(old,topology,limits,goal_pulse=True)
        for oracle in cases:
            m=oracle.maze;x=a.react(m.cells,m.w,m.h,m.start,m.goal);y=b.react(m.cells,m.w,m.h,m.start,m.goal);compare(x,y,'mask')
            normal+=2;work+=x.dispatches+x.spatial_reads+y.dispatches+y.spatial_reads
        for oracle in cases[:2]:
            m=oracle.maze
            for source in (True,False):
                x=observe(a,m.cells,m.w,m.h,m.start,m.goal,16,source);y=observe(b,m.cells,m.w,m.h,m.start,m.goal,16,source);compare(x,y,'state')
                probe+=2;work+=x.dispatches+x.reads+y.dispatches+y.reads
        # A stratified extra matrix covers phases,interventions,partial ticks and blocked inputs.
        if index%max(1,len(programs)//24)==0:
            for t in ('local','fixed','evolved'):
                for pulse,ablate in ((False,False),(True,True)):
                    for budget in (limits,Limits(max_steps=8,reads_per_site=1,instructions_per_site=1)):
                        aa=Organism(g,t,budget,ablate,pulse);bb=OldOrganism(old,t,budget,ablate,pulse);m=cases[0].maze
                        blocked=bytes(len(m.cells))
                        for cells in (m.cells,blocked):
                            x=aa.react(cells,m.w,m.h,m.start,m.goal);y=bb.react(cells,m.w,m.h,m.start,m.goal);compare(x,y,'mask');normal+=2
                            work+=x.dispatches+x.spatial_reads+y.dispatches+y.spatial_reads
                        for force in (True,False):
                            x=observe(aa,m.cells,m.w,m.h,m.start,m.goal,8,False,force);y=observe(bb,m.cells,m.w,m.h,m.start,m.goal,8,False,force);compare(x,y,'state')
                            probe+=2;work+=x.dispatches+x.reads+y.dispatches+y.reads
            item=Individual('equivalence',g,None,0)
            x=evaluate(item,validation[:2],topology,limits,'cap256');y=old_evaluate(item,validation[:2],topology,limits,'choice');assert x==y
            fitness+=2;normal+=8;probe+=16;work+=x.work+y.work
    sources=['growth.py','growth_runtime.py','growth_fitness.py','growth_data.py','growth_equivalence.py','regulatory.py','beacon_runtime.py','beacon_probe.py','beacon_fitness.py','choice_fitness.py','junction_fitness.py','balance_fitness.py','goal_fitness.py','signal_fitness.py']
    result=dict(all_checks_passed=True,scope='Independent-input equivalence only,no training/selection. Same V6 inference/probe kernels;≤128-gene instruction arrays unchanged.',
        seed=1113,unique_native_program_topology_pairs=len(programs),normal_calls=normal,probe_calls=probe,fitness_calls=fitness,
        charged_work=work,elapsed_seconds=time.perf_counter()-started,case_ids=[o.maze.case_id for o in cases],
        input_sha256=inputs,source_sha256={str((root/'maze_evolution'/p).relative_to(root)):hashlib.sha256((root/'maze_evolution'/p).read_bytes()).hexdigest() for p in sources})
    write_json(out,result);print({k:v for k,v in result.items() if k not in ('input_sha256','source_sha256')})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/capacity_equivalence.json');run(parser.parse_args().out)
