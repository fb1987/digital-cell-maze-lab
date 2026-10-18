"""Conceptual checks for interpreting source-dependent transmission."""
import random
import numpy as np
from maze_evolution.datasets import make_case
from maze_evolution.evaluator import Maze, Oracle, distances
from maze_evolution.regulatory import Gene, Genome, REMOTE_MIN, random_genome
from maze_evolution.regulatory_runtime import Organism
from maze_evolution.runtime import Limits
from maze_evolution.signal_probe import observe
from maze_evolution.signal_fitness import signal_metrics


def metric(genome,oracle,topology='local',ablate=False,horizon=16):
    m=oracle.maze
    o=Organism(genome,topology,Limits(max_steps=32),ablate)
    a=observe(o,m.cells,m.w,m.h,m.start,m.goal,horizon,True)
    b=observe(o,m.cells,m.w,m.h,m.start,m.goal,horizon,False)
    return signal_metrics(a,b,oracle,horizon)


def test_output_and_stop_channels_cannot_substitute_for_hidden_transmission():
    genome=Genome((Gene(4,12,2),Gene(10,13,12,9),Gene(13,2,13),Gene(13,7,13)))
    oracle=Oracle.build(Maze(bytes([1]*17),17,1,0,16))
    assert metric(genome,oracle)['score']==0


def test_broadcast_into_another_component_pays_leakage_penalty():
    genome=Genome((Gene(REMOTE_MIN,12,0,radius=1),Gene(4,13,0),
        Gene(10,14,12,13),Gene(10,15,14,9),Gene(13,0,15)))
    oracle=Oracle.build(Maze(bytes([1,1,1,0,1,1,1]),7,1,0,2))
    jumping=metric(genome,oracle,'evolved')
    local=metric(genome,oracle,'evolved',True)
    assert jumping['leakage']==1 and jumping['score']==0
    assert local['leakage']==0 and local['score']==1


def test_random_local_programs_obey_graph_causal_cone():
    rng=random.Random(1044)
    for family in ('perfect','random','disconnected'):
        oracle=make_case(1044,'observer-cone-unit',0,0,17,family)
        d=np.array(distances(oracle.maze,oracle.maze.start))
        ceiling=float(np.mean([np.mean(d[d>=k]<=8) for k in (2,4,8) if np.any(d>=k)]))
        for _ in range(10):
            row=metric(random_genome(rng,True),oracle,horizon=8)
            assert row['max_distance']<=8
            assert row['score']<=ceiling+1e-10
