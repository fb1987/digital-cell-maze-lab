"""Post-run integrity/dataflow audit; does not select or modify organisms."""
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from .evaluator import Maze, Oracle, assess
from .regulatory import Genome, ALWAYS
from .runtime import Reaction
from .experiment import write_json


def output_dataflow(genome):
    """Conservative output/explicit-stop slice, not proof of semantic complexity.

    Full-state quiescence can also depend on channels outside this slice.
    Conditional writes retain both paths. Inter-tick dependencies reach a fixed
    point over the eight channels; no program is executed or rewritten.
    """
    channels, live_genes = {2,7}, set()
    references={0:(1,),1:(),2:(1,2),3:(1,2),4:(),5:(),6:(),7:(),8:(1,2),
                9:(1,2),10:(1,2),11:(1,),12:(1,2,3),16:(1,2),17:(),14:(),15:()}
    spatial={4,5,6,7,14,15,17}
    while True:
        before=set(channels)
        needed=set()
        for index in range(len(genome.genes)-1,-1,-1):
            gene=genome.genes[index]
            if gene.op==13:
                if gene.dst not in channels:
                    continue
                live_genes.add(index)
                needed.add(gene.a)
            elif gene.dst in needed:
                live_genes.add(index)
                if gene.gate==ALWAYS:
                    needed.discard(gene.dst)
                values=(gene.dst,gene.a,gene.b,gene.c)
                needed.update(values[field] for field in references[gene.op])
                if gene.op in spatial:
                    channels.add(gene.a)
            else:
                continue
            if gene.gate!=ALWAYS:
                needed.add(gene.gate)
        channels.update(r for r in needed if r<8)
        if channels==before:
            break
    return dict(genes=len(genome.genes),potential_output_stop_genes=len(live_genes),
                state_channels=sorted(channels),
                caveat='Conservative syntactic dependencies only; quiescence and semantic redundancy are not captured.')


def audit(out):
    out=Path(out)
    root=Path(__file__).resolve().parents[1]
    env=json.loads((out/'environment.json').read_text())
    champions=json.loads((out/'champions.json').read_text())
    assert hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()==env['champions_sha256']
    for name,digest in env['source_sha256'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
    identities=set()
    registry_count=0
    with gzip.open(out/'genomes.jsonl.gz','rt') as handle:
        for line in handle:
            row=json.loads(line)
            assert row['id'] not in identities
            assert row['parent'] is None or row['parent'] in identities
            assert row['genome']['version']==2 and 1<=len(row['genome']['genes'])<=128
            assert all(len(gene)==7 for gene in row['genome']['genes'])
            identities.add(row['id'])
            registry_count+=1
    records=Counter()
    work=Counter()
    maze_evaluations=Counter()
    with gzip.open(out/'evaluations.jsonl.gz','rt') as handle:
        for line in handle:
            row=json.loads(line)
            assert row['id'] in identities
            condition=row['condition']
            records[(condition,row['split'])]+=1
            work[condition]+=row['work']
            maze_evaluations[condition]+=len(row['cases'])
            for case in row['cases']:
                assert case['active']<=case['dispatches']
                assert len(case['reads'])==4
    initial_groups=defaultdict(list)
    slices={}
    for key,saved in champions.items():
        c=saved['config']
        assert records[(key,'train')]==c['population']*c['generations']
        assert work[key]==saved['work'] and maze_evaluations[key]==saved['maze_evaluations']
        assert saved['champion']['id'] in identities and saved['frozen']['id'] in identities
        initial_groups[(c['study'],c['origin'],c['replicate'])].append(saved['initial_digests'])
        slices[key]=output_dataflow(Genome.from_dict(saved['champion']['genome']))
    assert all(all(value==values[0] for value in values) for values in initial_groups.values())
    with gzip.open(out/'mazes.json.gz','rt') as handle:
        cases=json.load(handle)
    previous={row['sha256'] for row in json.loads((root/'results/first_evolution/mazes.json').read_text())}
    tests={row['case_id']:row for row in cases if row['split']=='test'}
    test_hashes={row['sha256'] for row in tests.values()}
    other={row['sha256'] for row in cases if row['split']!='test'}
    assert len(test_hashes)==len(tests)
    assert not test_hashes.intersection(previous|other)
    oracles={}
    for identity,row in tests.items():
        maze=Maze(bytes.fromhex(row['cells_hex']),row['w'],row['h'],row['start'],row['goal'],
                  row['family'],row['seed'],row['split'],identity)
        assert maze.digest==row['sha256']
        oracles[identity]=Oracle.build(maze)
    outputs=0
    statuses=defaultdict(Counter)
    gallery={}
    chosen_cases={}
    with gzip.open(out/'holdout.jsonl.gz','rt') as handle:
        for line in handle:
            row=json.loads(line)
            oracle=oracles[row['case_id']]
            packed=np.frombuffer(bytes.fromhex(row['mask']),dtype=np.uint8)
            mask=np.unpackbits(packed,bitorder='little')[:len(oracle.maze.cells)]
            reaction=Reaction(mask,row['status'],row['steps'],row['reads'],row['dispatches'],row['array_bytes'])
            checked=assess(reaction,oracle)
            for field in ('valid_path','optimal','no_path_correct','failure','path_length','reachable'):
                assert getattr(checked,field)==row[field],(row['arm'],row['case_id'],field)
            if row['range_reads']:
                assert sum(row['range_reads'])==row['reads']
                assert row['active']<=row['dispatches']
            statuses[row['arm']][row['status']]+=1
            if (row['w']==17 and row['h']==17 and row['family']=='perfect'
                    and row['arm'] in ('compiled_bfs','rich/local/random/evolution',
                                       'rich/evolved/random/evolution')):
                chosen_cases.setdefault(row['replicate'],row['case_id'])
                if row['case_id']==chosen_cases[row['replicate']]:
                    gallery[(row['replicate'],row['arm'])]=(row,mask.copy())
            outputs+=1
    value=dict(source_hashes_match=True,champion_hash_matches=True,lineage_genomes=registry_count,
        population_evaluations=sum(count for (key,split),count in records.items() if split=='train'),
        maze_evaluations=sum(maze_evaluations.values()),holdout_outputs_revalidated=outputs,
        fresh_distinct_tests=len(tests),disjoint_from_v1_train_validation=True,
        paired_initial_populations=True,output_stop_dataflow=slices,statuses=dict(statuses))
    write_json(out/'verification.json',value)
    report=out.with_suffix('.md')
    text=report.read_text().split('\n## Integrity and developmental audit')[0]
    text+='\n## Integrity and developmental audit\n\n'
    text+=(f"All saved source/champion hashes match. Lineage covers {registry_count:,} genomes; "
           f"logs contain {value['population_evaluations']:,} population evaluations and "
           f"{value['maze_evaluations']:,} maze responses during search/validation. All "
           f"{outputs:,} final rasters were decoded and independently revalidated against "
           f"fresh oracle instances. The {len(tests)} final cases have distinct input/endpoint "
           'hashes and are disjoint from all new training/validation and V1 cases. '
           'Paired topology/method conditions have exactly the same initial genotype lists.\n\n')
    text+='| Rich evolution condition | Genome genes | Potential output/stop dataflow genes |\n| --- | ---: | ---: |\n'
    for key,fields in slices.items():
        if key.startswith('rich/') and '/evolution/' in key:
            text+=f"| {key} | {fields['genes']} | {fields['potential_output_stop_genes']} |\n"
    text+=('\nThe dataflow slice is a conservative static dependency count, not a measure '
           'of functional algorithm complexity. Hidden state outside it can still affect '
           'quiescent termination. More instructions, expression and longer lifetimes do '
           'not by themselves establish useful computation. `verification.json` retains '
           'the complete audit and status distributions.\n')
    if gallery:
        from PIL import Image, ImageDraw
        replicates=sorted(chosen_cases)
        panel_w,panel_h,tile=210,220,9
        picture=Image.new('RGB',(3*panel_w,len(replicates)*panel_h),'#111827')
        draw=ImageDraw.Draw(picture)
        for y,replicate in enumerate(replicates):
            for x,(arm,label) in enumerate((('compiled_bfs','BFS oracle'),
                    ('rich/local/random/evolution','Local random'),
                    ('rich/evolved/random/evolution','Evolved-range random'))):
                row,mask=gallery[(replicate,arm)]
                maze=oracles[row['case_id']].maze
                ox,oy=x*panel_w+14,y*panel_h+56
                draw.text((ox,oy-43),f'r{replicate} {label}',fill='#f9fafb')
                detail='shortest path' if row['optimal'] else row['failure']
                draw.text((ox,oy-26),detail,fill='#b8c4d6')
                for p,opened in enumerate(maze.cells):
                    color='#172235' if not opened else '#5ae1bd' if mask[p] else '#45536a'
                    if p==maze.start:
                        color='#72b6ff'
                    elif p==maze.goal:
                        color='#ff6584'
                    px,py=p%17,p//17
                    draw.rectangle((ox+px*tile,oy+py*tile,ox+(px+1)*tile-1,oy+(py+1)*tile-1),fill=color)
        picture.save(out/'visuals'/'random_replicates.png')
        text+=('\nAll random-evolution replicates below use the first 17x17 perfect test '
               'case for that replicate; none is selected for success.\n\n'
               f'![Random-origin replicates]({out.name}/visuals/random_replicates.png)\n')
    report.write_text(text)
    print(json.dumps({key:v for key,v in value.items() if key not in ('output_stop_dataflow','statuses')},indent=2))


if __name__=='__main__':
    import sys
    audit(sys.argv[1])
